"""PDNAgent - Single agent for all PDN chat interactions."""

import json
import logging
import os
import time

from collections import defaultdict
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from pathlib import Path
from typing import List, Dict, Any, Union

from langchain_anthropic import ChatAnthropic
from langchain_core.messages import SystemMessage, HumanMessage
from langchain_openai import ChatOpenAI

from app.utils.user_history_service import UserHistoryService
from config import Config

@dataclass
class UserHistory:
    raw: List[dict] = field(default_factory=list)
    summary: str = ""

class PDNAgent:
    """Single agent for all PDN chat interactions."""
    
    MAX_CONTEXT_TOKENS = 3500
    MAX_TURNS_BEFORE_SUMMARY = 6
    RAW_TURNS_TO_KEEP = 3
    MAX_CONVERSATIONS_PER_DAY = 15
    MAX_SUMMARY_TOKENS = 500  # Budget cap for summary length
    EXEMPT_USERS = frozenset(['פנינה'])  # Users exempt from daily limits

    def __init__(self, llm_provider=None, model_name=None):
        """Initialize the PDN agent.

        Args:
            llm_provider (str, optional): LLM provider ('openai' or 'anthropic').
                                        Defaults to config value.
            model_name (str, optional): Model name to use. Defaults to config value.
        """
        config = Config()
        self.llm_provider = llm_provider or config.LLM_PROVIDER
        self.model_name = model_name or (config.ANTHROPIC_MODEL if self.llm_provider.lower() == 'anthropic' else config.OPENAI_MODEL)
        self.llm = self._initialize_llm(config)
        self._is_anthropic = self.llm_provider.lower() == 'anthropic'

        # Use a cheap model for summarization — same provider as main LLM
        if self._is_anthropic:
            self.summary_llm = ChatAnthropic(model="claude-3-5-haiku-latest", temperature=0.3, api_key=config.ANTHROPIC_API_KEY)
        else:
            self.summary_llm = ChatOpenAI(model="gpt-4o-mini", temperature=0.3, api_key=config.OPENAI_API_KEY)

        self.conversation_history = defaultdict(UserHistory)
        self.user_conversations = defaultdict(lambda: {'count': 0, 'last_reset': datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)})
        # Map display name → email for history persistence (display names may be non-ASCII)
        self._user_email_map: Dict[str, str] = {}

        # Token usage tracking — persisted to file with daily granularity
        self._usage_file = Path(os.getenv('SAVED_RESULTS_DIR', 'saved_results')) / 'token_usage.json'
        self.token_usage = self._load_usage_file()
        self._last_usage_save = 0  # timestamp of last disk write
        self._usage_save_interval = 5  # seconds between disk writes

        # User history persistence service
        self.history_service = UserHistoryService(
            base_dir=str(Path(os.getenv('SAVED_RESULTS_DIR', 'saved_results')))
        )

        self.logger = logging.getLogger("pdn_agent")
        self._prompt_cache = {}
        self._prompts_dir = Path(__file__).parent / "prompts"

        self.logger.info("Initialized PDNAgent with %s using model %s", self.llm_provider, self.model_name)

    def _initialize_llm(self, config) -> Union[ChatAnthropic, ChatOpenAI]:
        """Initialize the appropriate LLM based on the provider."""
        providers = {
            'anthropic': (ChatAnthropic, config.ANTHROPIC_API_KEY, "ANTHROPIC_API_KEY"),
            'openai': (ChatOpenAI, config.OPENAI_API_KEY, "OPENAI_API_KEY")
        }

        provider_key = self.llm_provider.lower() if self.llm_provider.lower() in providers else 'openai'
        llm_class, api_key, key_name = providers[provider_key]

        if not api_key:
            raise ValueError(f"{key_name} not set")

        return llm_class(model=self.model_name, temperature=0.7, max_tokens=1500, api_key=api_key, timeout=180)

    def _reset_daily_count(self, user_name: str):
        """Reset the daily conversation count at midnight."""
        now = datetime.now()
        user_data = self.user_conversations[user_name]
        # Reset count if a new day has started
        if now.date() > user_data['last_reset'].date():
            old_date = user_data['last_reset'].date()
            user_data['count'] = 0
            user_data['last_reset'] = now
            self.logger.info("Daily count for %s has been reset. Previous: %s, Current: %s", user_name, old_date, now.date())

    def _has_exceeded_daily_limit(self, user_name: str, max_conversations_per_day: int = None) -> bool:
        """Check if the user has exceeded the daily conversation limit."""
        self._reset_daily_count(user_name)

        if user_name not in self.EXEMPT_USERS:
            limit = max_conversations_per_day or self.MAX_CONVERSATIONS_PER_DAY
            return self.user_conversations[user_name]['count'] >= limit
        else:
            return False

    def _increment_conversation_count(self, user_name: str):
        """Increment the conversation count for the user."""
        self.user_conversations[user_name]['count'] += 1
        self.logger.info("Incremented conversation count for %s. Current count: %d", user_name, self.user_conversations[user_name]['count'])

    def _load_prompt(self, pdn_code: str, prompt_file: str) -> str:
        """Load prompt file with caching. Raises FileNotFoundError with clear message if code is invalid."""
        if not pdn_code:
            raise ValueError("PDN code is required")

        code_path = self._prompts_dir / "pdn_code" / f"{pdn_code}.prompt"
        if not code_path.exists():
            raise ValueError(f"Unknown PDN code: {pdn_code}")

        cache_key = f"{pdn_code}_{prompt_file}"
        if cache_key not in self._prompt_cache:
            prompt_content = (
                (self._prompts_dir / prompt_file).read_text(encoding='utf-8') +
                code_path.read_text(encoding='utf-8')
            )
            if prompt_file in ["binat_agent.prompt", "daily_training.prompt"]:
                prompt_content += (self._prompts_dir / "guardrails.prompt").read_text(encoding='utf-8')
            self._prompt_cache[cache_key] = prompt_content
        return self._prompt_cache[cache_key]

    def _estimate_tokens(self, text: str) -> int:
        """Estimate token count. Hebrew tokenizes at ~1 token per 2-3 chars."""
        return len(text) // 3

    def _build_system_message(self, system_prompt: str) -> SystemMessage:
        """Build a SystemMessage, adding Anthropic cache_control when applicable.

        Anthropic caches the system prompt server-side for 5 minutes.
        Subsequent calls with the same prompt pay only 10% of the input token cost.
        
        Note: cache_control must be on a content block (dict), not on additional_kwargs,
        because langchain-anthropic only reads cache_control from content blocks.
        """
        if self._is_anthropic:
            return SystemMessage(
                content=[{
                    "type": "text",
                    "text": system_prompt,
                    "cache_control": {"type": "ephemeral"}
                }]
            )
        return SystemMessage(content=system_prompt)

    def _load_usage_file(self) -> dict:
        """Load token usage history from JSON file."""
        try:
            if self._usage_file.exists():
                with open(self._usage_file, 'r') as f:
                    return json.load(f)
        except Exception as e:
            self.logger.warning("Could not load token usage file: %s", e)
        return {}

    def _save_usage_file(self, force: bool = False):
        """Persist token usage history to JSON file (debounced to avoid excessive I/O)."""
        now = time.time()
        if not force and (now - self._last_usage_save) < self._usage_save_interval:
            return
        try:
            self._usage_file.parent.mkdir(parents=True, exist_ok=True)
            with open(self._usage_file, 'w') as f:
                json.dump(self.token_usage, f, ensure_ascii=False, indent=2)
            self._last_usage_save = now
        except Exception as e:
            self.logger.warning("Could not save token usage file: %s", e)

    def _track_usage(self, user_name: str, response):
        """Extract and accumulate token usage from an LLM response, stored per user per day."""
        if not user_name:
            return
        usage = getattr(response, 'usage_metadata', None)
        if not usage:
            return

        # Handle both dict (OpenAI) and object (Anthropic) formats
        def get_val(obj, key, default=0):
            if isinstance(obj, dict):
                return obj.get(key, default) or default
            return getattr(obj, key, default) or default

        today = datetime.now().strftime('%Y-%m-%d')

        if user_name not in self.token_usage:
            self.token_usage[user_name] = {}
        if today not in self.token_usage[user_name]:
            self.token_usage[user_name][today] = {
                'input_tokens': 0, 'output_tokens': 0,
                'cache_creation_tokens': 0, 'cache_read_tokens': 0,
                'calls': 0, 'model': ''
            }

        day = self.token_usage[user_name][today]
        day['input_tokens'] += get_val(usage, 'input_tokens')
        day['output_tokens'] += get_val(usage, 'output_tokens')
        day['calls'] += 1
        day['model'] = self.model_name

        # Track cache tokens from input_token_details
        details = get_val(usage, 'input_token_details', None)
        if details:
            day['cache_creation_tokens'] += get_val(details, 'cache_creation')
            day['cache_read_tokens'] += get_val(details, 'cache_read')

        self._save_usage_file()

    def get_usage_stats(self, days: int = 14) -> Dict[str, Any]:
        """Return token usage stats with daily history and cost projections."""
        INPUT_PRICE = 3.0
        OUTPUT_PRICE = 15.0
        CACHE_WRITE_PRICE = 3.75
        CACHE_READ_PRICE = 0.30

        cutoff = (datetime.now() - timedelta(days=days)).strftime('%Y-%m-%d')

        def calc_cost(d):
            uncached = d['input_tokens'] - d['cache_creation_tokens'] - d['cache_read_tokens']
            return (
                (max(0, uncached) / 1e6) * INPUT_PRICE +
                (d['output_tokens'] / 1e6) * OUTPUT_PRICE +
                (d['cache_creation_tokens'] / 1e6) * CACHE_WRITE_PRICE +
                (d['cache_read_tokens'] / 1e6) * CACHE_READ_PRICE
            )

        def calc_savings(d):
            if d['cache_read_tokens'] <= 0:
                return 0
            return (d['cache_read_tokens'] / 1e6) * (INPUT_PRICE - CACHE_READ_PRICE)

        # Build per-user summary + daily breakdown
        users = {}
        daily_totals = {}

        for user, date_data in self.token_usage.items():
            user_total = {'input_tokens': 0, 'output_tokens': 0, 'cache_creation_tokens': 0,
                          'cache_read_tokens': 0, 'calls': 0, 'model': '', 'daily': {}}

            for date_str, d in sorted(date_data.items()):
                if date_str < cutoff:
                    continue
                user_total['input_tokens'] += d['input_tokens']
                user_total['output_tokens'] += d['output_tokens']
                user_total['cache_creation_tokens'] += d['cache_creation_tokens']
                user_total['cache_read_tokens'] += d['cache_read_tokens']
                user_total['calls'] += d['calls']
                user_total['model'] = d.get('model', '')
                user_total['daily'][date_str] = {**d, 'cost': round(calc_cost(d), 4)}

                if date_str not in daily_totals:
                    daily_totals[date_str] = {'input_tokens': 0, 'output_tokens': 0,
                                              'cache_creation_tokens': 0, 'cache_read_tokens': 0,
                                              'calls': 0, 'cost': 0}
                dt = daily_totals[date_str]
                dt['input_tokens'] += d['input_tokens']
                dt['output_tokens'] += d['output_tokens']
                dt['cache_creation_tokens'] += d['cache_creation_tokens']
                dt['cache_read_tokens'] += d['cache_read_tokens']
                dt['calls'] += d['calls']
                dt['cost'] += calc_cost(d)

            user_total['total_cost'] = round(calc_cost(user_total), 4)
            user_total['cache_savings'] = round(calc_savings(user_total), 4)
            users[user] = user_total

        # Round daily totals
        for dt in daily_totals.values():
            dt['cost'] = round(dt['cost'], 4)

        # Projection: average daily cost over active days → project to 30 days
        sorted_days = sorted(daily_totals.keys())
        active_days = len(sorted_days)
        total_cost_period = sum(dt['cost'] for dt in daily_totals.values())
        avg_daily_cost = total_cost_period / active_days if active_days > 0 else 0

        projection = {
            'active_days': active_days,
            'avg_daily_cost': round(avg_daily_cost, 4),
            'projected_monthly': round(avg_daily_cost * 30, 2),
            'projected_yearly': round(avg_daily_cost * 365, 2),
        }

        return {
            'users': users,
            'daily_totals': dict(sorted(daily_totals.items())),
            'projection': projection,
            'period_days': days
        }

    def _summarize_old_turns(self, user_name: str) -> None:
        """Summarize old exchanges into a single consolidated narrative with token budget."""
        hist = self.conversation_history[user_name]
        if len(hist.raw) <= self.RAW_TURNS_TO_KEEP:
            return
        
        old_turns = hist.raw[:-self.RAW_TURNS_TO_KEEP]
        text = "\n".join(f"User: {ex['user']}\nAssistant: {ex['assistant']}" for ex in old_turns)
        today = datetime.now().strftime('%Y-%m-%d')
        
        # Build context for the LLM: existing summary + new turns
        if hist.summary:
            merge_input = (
                f"EXISTING SUMMARY:\n{hist.summary}\n\n"
                f"NEW CONVERSATION (date: {today}):\n{text}"
            )
            prompt = self._get_merge_prompt()
        else:
            merge_input = f"CONVERSATION (date: {today}):\n{text}"
            prompt = self._get_initial_prompt()
        
        try:
            consolidated = self.summary_llm.invoke([
                SystemMessage(content=prompt),
                HumanMessage(content=merge_input)
            ], max_tokens=self.MAX_SUMMARY_TOKENS).content
            
            hist.summary = consolidated.strip()
            # Persist history to disk for cross-session continuity (use email, not display name)
            persist_id = self._user_email_map.get(user_name, user_name)
            if hist.summary:
                self.history_service.save_user_history(
                    persist_id, hist.summary,
                    metadata={
                        "source": "PDNChat",
                        "summary_version": "3",
                        "last_session_date": today,
                    }
                )
            hist.raw = hist.raw[-self.RAW_TURNS_TO_KEEP:]
            self.logger.info("Summarized %d turns for %s", len(old_turns), user_name)
        except Exception as e:
            # Summarization failed — keep raw history intact to avoid data loss
            self.logger.warning("Summarization failed for %s, keeping raw history: %s", user_name, e)

    def _get_merge_prompt(self) -> str:
        """Return the prompt for merging existing summary with new conversation."""
        return (
            "You are a personal development coach's memory system. "
            "Merge the EXISTING SUMMARY with the NEW CONVERSATION into ONE consolidated summary.\n\n"
            "FORMAT — produce exactly these sections:\n"
            "נושאים מרכזיים: [main topics/challenges discussed across all sessions]\n"
            "פרטים חשובים: [specific names, numbers, decisions — NEVER drop concrete details]\n"
            "מסע רגשי: [how the user's feelings evolved over time]\n"
            "החלטות ופעולות: [what was decided, what actions were taken or planned]\n"
            "לא נפתר: [open questions, unresolved tensions]\n"
            "סטטוס נוכחי: [where the user left off, what they plan to do next]\n\n"
            "RULES:\n"
            "- ONE consolidated narrative per section, not separate blocks per session\n"
            "- NEVER drop specific numbers, names, prices, or decisions\n"
            "- Include dates when things happened (e.g., 'ב-5.5 החליט...')\n"
            "- Prioritize recent/unresolved items over old resolved ones\n"
            "- If summary is getting long, compress OLD RESOLVED items, keep RECENT ones detailed\n"
            "- Max 10 lines total. Use Hebrew.\n"
            "- If the user spoke English about specific topics, keep those terms in English"
        )

    def _get_initial_prompt(self) -> str:
        """Return the prompt for creating the first summary from a conversation."""
        return (
            "You are a personal development coach's memory system. "
            "Summarize this conversation into a structured memory.\n\n"
            "FORMAT:\n"
            "נושאים מרכזיים: [main topics/challenges]\n"
            "פרטים חשובים: [specific names, numbers, decisions]\n"
            "מסע רגשי: [user's emotional state and why]\n"
            "החלטות ופעולות: [what was decided or planned]\n"
            "סטטוס נוכחי: [where the user left off]\n\n"
            "RULES:\n"
            "- Keep specific details: numbers, names, prices, dates\n"
            "- Max 8 lines. Use Hebrew.\n"
            "- If the user spoke English about specific topics, keep those terms"
        )

    def _add_to_history(self, user_name: str, user_query: str, assistant_response: str):
        """Add conversation exchange to history with hybrid summarization."""
        hist = self.conversation_history[user_name]
        hist.raw.append({"user": user_query, "assistant": assistant_response})
        
        # Calculate total tokens
        total_tokens = sum(
            self._estimate_tokens(ex['user']) + self._estimate_tokens(ex['assistant'])
            for ex in hist.raw
        )
        
        # Check both conditions
        turn_limit_reached = len(hist.raw) >= self.MAX_TURNS_BEFORE_SUMMARY
        token_limit_reached = total_tokens > self.MAX_CONTEXT_TOKENS
        
        # Summarize if either condition is met
        if turn_limit_reached or token_limit_reached:
            reason = "turn limit" if turn_limit_reached else "token limit"
            self.logger.info("Summarizing for %s: %s reached (turns=%d, tokens=%d)", user_name, reason, len(hist.raw), total_tokens)
            self._summarize_old_turns(user_name)

    def _format_history(self, user_name: str) -> str:
        """Format conversation history with summary + recent exchanges."""
        hist = self.conversation_history.get(user_name)
        if not hist or (not hist.raw and not hist.summary):
            return ""
        
        parts = []
        if hist.summary:
            parts.append(f"Previous conversation summary:\n{hist.summary}")
        
        if hist.raw:
            recent = "\n\n".join(f"User: {ex['user']}\nAssistant: {ex['assistant']}" for ex in hist.raw)
            parts.append(f"Recent exchanges:\n{recent}")
        
        return "\n\n".join(parts)

    def clear_user_history(self, user_name: str):
        """Clear conversation history for user."""
        if user_name in self.conversation_history:
            self.conversation_history[user_name] = UserHistory()

    def register_user_email(self, user_name: str, email: str) -> None:
        """Register the email for a display name so history can be persisted by email."""
        if user_name and email:
            self._user_email_map[user_name] = email

    def persist_session(self, user_name: str, email: str) -> None:
        """Force-save all conversation history for a user (called on logout).
        
        Summarizes any remaining raw turns and persists the result to disk.
        """
        if not user_name or not email:
            return
        self.register_user_email(user_name, email)
        hist = self.conversation_history.get(user_name)
        if not hist:
            return
        
        if hist.raw:
            # Summarize ALL remaining turns (bypass threshold)
            old_turns = hist.raw
            text = "\n".join(
                f"User: {ex['user']}\nAssistant: {ex['assistant']}" for ex in old_turns
            )
            today = datetime.now().strftime('%Y-%m-%d')
            
            if hist.summary:
                merge_input = (
                    f"EXISTING SUMMARY:\n{hist.summary}\n\n"
                    f"NEW CONVERSATION (date: {today}):\n{text}"
                )
                prompt = self._get_merge_prompt()
            else:
                merge_input = f"CONVERSATION (date: {today}):\n{text}"
                prompt = self._get_initial_prompt()
            
            try:
                consolidated = self.summary_llm.invoke([
                    SystemMessage(content=prompt),
                    HumanMessage(content=merge_input)
                ], max_tokens=self.MAX_SUMMARY_TOKENS).content
                hist.summary = consolidated.strip()
                hist.raw = []
            except Exception as e:
                self.logger.warning("Logout summarization failed for %s: %s", user_name, e)
        
        # Persist whatever summary we have
        if hist.summary:
            self.history_service.save_user_history(
                email, hist.summary,
                metadata={
                    "source": "PDNChat",
                    "summary_version": "3",
                    "last_session_date": datetime.now().strftime('%Y-%m-%d'),
                }
            )

    def chat_with_binat(self, user_query: str, user_name: str = None, pdn_code: str = None, daily_conversation_limit: int = None) -> str:
        """Generate response using PDN prompt."""
        if self._has_exceeded_daily_limit(user_name, daily_conversation_limit):
            return "הגעת למגבלת השיחות להיום, אנא חזור אלינו מחר."

        system_prompt = self._load_prompt(pdn_code, "binat_agent.prompt")
        history_context = self._format_history(user_name)

        if history_context:
            user_message = (
                f"<context>\n"
                f"User: {user_name} | Code: {pdn_code}\n"
                f"Session history:\n{history_context}\n"
                f"</context>\n\n"
                f"<user_message>\n{user_query}\n</user_message>"
            )
        else:
            user_message = (
                f"<context>\n"
                f"User: {user_name} | Code: {pdn_code}\n"
                f"</context>\n\n"
                f"<user_message>\n{user_query}\n</user_message>"
            )

        response = self.llm.invoke([
            self._build_system_message(system_prompt),
            HumanMessage(content=user_message)
        ])
        self._track_usage(user_name, response)
        response_text = response.content

        # Increment count AFTER successful LLM call
        if user_name:
            self._increment_conversation_count(user_name)
            self._add_to_history(user_name, user_query, response_text)

        return response_text

    def build_21_transformation_plan(self, user_goal: str, user_name: str, pdn_code: str, daily_conversation_limit: int = None) -> str:
        """Generate 21-day transformation plan."""
        if self._has_exceeded_daily_limit(user_name, daily_conversation_limit):
            return "הגעת למגבלת השיחות להיום, אנא חזור אלינו מחר."

        system_prompt = self._load_prompt(pdn_code, "21_plan.prompt")
        user_message = f"user_name: {user_name}\nuser_pdn_code: {pdn_code}\nuser_goal: {user_goal}"

        response =  self.llm.invoke([
            self._build_system_message(system_prompt),
            HumanMessage(content=user_message)
        ], max_tokens=4000)
        self._track_usage(user_name, response)
        response_text = response.content

        # Increment count AFTER successful LLM call
        if user_name:
            self._increment_conversation_count(user_name)
            self._add_to_history(user_name, user_goal, response_text)

        return response_text

    def daily_training(self, user_name: str, pdn_code: str, day_task: str, daily_conversation_limit: int = None) -> str:
        """Generate personalized daily training response."""
        if self._has_exceeded_daily_limit(user_name, daily_conversation_limit):
            return "הגעת למגבלת השיחות להיום, אנא חזור אלינו מחר."

        system_prompt = self._load_prompt(pdn_code, "daily_training.prompt")
        user_message = f"User name: {user_name}\n User day Task: {day_task}\n."

        response = self.llm.invoke([
            self._build_system_message(system_prompt),
            HumanMessage(content=user_message)
        ])
        self._track_usage(user_name, response)
        response_text = response.content

        # Increment count AFTER successful LLM call
        if user_name:
            self._increment_conversation_count(user_name)
            self._add_to_history(user_name, day_task, response_text)

        return response_text
