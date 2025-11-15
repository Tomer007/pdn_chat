"""PDNAgent - Single agent for all PDN chat interactions."""

import logging
import os
import sys

from collections import defaultdict
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import List

from langchain_anthropic import ChatAnthropic
from langchain_core.messages import SystemMessage, HumanMessage
from langchain_openai import ChatOpenAI

sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..', '..'))
from config import Config

@dataclass
class UserHistory:
    raw: List[dict] = field(default_factory=list)
    summary: str = ""

class PDNAgent:
    """Single agent for all PDN chat interactions."""
    
    MAX_CONTEXT_TOKENS = 3500
    MAX_TURNS_BEFORE_SUMMARY = 5
    RAW_TURNS_TO_KEEP = 5
    MAX_CONVERSATIONS_PER_DAY = 15

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
        self.summary_llm = ChatOpenAI(model="gpt-4o-mini", temperature=0.3, api_key=config.OPENAI_API_KEY)
        
        self.conversation_history = defaultdict(UserHistory)
        self.user_conversations = defaultdict(lambda: {'count': 0, 'last_reset': datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)})

        self.logger = logging.getLogger("pdn_agent")
        self._prompt_cache = {}
        self._prompts_dir = Path(__file__).parent / "prompts"
        
        self.logger.info(f"Initialized PDNAgent with {self.llm_provider} using model {self.model_name}")

    def _initialize_llm(self, config):
        """Initialize the appropriate LLM based on the provider."""
        providers = {
            'anthropic': (ChatAnthropic, config.ANTHROPIC_API_KEY, "ANTHROPIC_API_KEY"),
            'openai': (ChatOpenAI, config.OPENAI_API_KEY, "OPENAI_API_KEY")
        }
        
        provider_key = self.llm_provider.lower() if self.llm_provider.lower() in providers else 'openai'
        llm_class, api_key, key_name = providers[provider_key]
        
        if not api_key:
            raise ValueError(f"{key_name} not set")
        
        return llm_class(model=self.model_name, temperature=0.7, max_tokens=4000, api_key=api_key, timeout=180)

    def _reset_daily_count(self, user_name: str):
        """Reset the daily conversation count at midnight."""
        now = datetime.now()
        user_data = self.user_conversations[user_name]
        # Reset count if a new day has started
        if now.date() > user_data['last_reset'].date():
            old_date = user_data['last_reset'].date()
            user_data['count'] = 0
            user_data['last_reset'] = now
            self.logger.info(f"Daily count for {user_name} has been reset. Previous: {old_date}, Current: {now.date()}")

    def _check_conversation_limit(self, user_name: str) -> bool:
        """Check if the user has exceeded the daily conversation limit."""
        self._reset_daily_count(user_name)
        return self.user_conversations[user_name]['count'] < self.MAX_CONVERSATIONS_PER_DAY

    def _increment_conversation_count(self, user_name: str):
        """Increment the conversation count for the user."""
        self.user_conversations[user_name]['count'] += 1
        self.logger.info(f"Incremented conversation count for {user_name}. Current count: {self.user_conversations[user_name]['count']}")

    def _load_prompt(self, pdn_code: str, prompt_file: str) -> str:
        """Load prompt file with caching."""
        cache_key = f"{pdn_code}_{prompt_file}"
        if cache_key not in self._prompt_cache:
            prompt_content = (
                (self._prompts_dir / prompt_file).read_text(encoding='utf-8') +
                (self._prompts_dir / "pdn_code" / f"{pdn_code}.prompt").read_text(encoding='utf-8')
            )
            if prompt_file in ["binat_agent.prompt", "daily_training.prompt"]:
                prompt_content += (self._prompts_dir / "guardrails.prompt").read_text(encoding='utf-8')
            self._prompt_cache[cache_key] = prompt_content
        return self._prompt_cache[cache_key]

    def _estimate_tokens(self, text: str) -> int:
        """Estimate token count (rough: 1 token ≈ 4 chars)."""
        return len(text) // 4

    def _summarize_old_turns(self, user_name: str):
        """Summarize old exchanges when raw list exceeds threshold."""
        hist = self.conversation_history[user_name]
        if len(hist.raw) <= self.RAW_TURNS_TO_KEEP:
            return
        
        old_turns = hist.raw[:-self.RAW_TURNS_TO_KEEP]
        text = "\n".join(f"User: {ex['user']}\nAssistant: {ex['assistant']}" for ex in old_turns)
        
        new_summary = self.summary_llm.invoke([
            SystemMessage(content="Summarize this conversation in 2-3 sentences, focusing on key topics and advice given."),
            HumanMessage(content=text)
        ]).content
        
        hist.summary = f"{hist.summary}\n{new_summary}".strip() if hist.summary else new_summary
        hist.raw = hist.raw[-self.RAW_TURNS_TO_KEEP:]
        self.logger.info(f"Summarized {len(old_turns)} turns for {user_name}")

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
            self.logger.info(f"Summarizing for {user_name}: {reason} reached (turns={len(hist.raw)}, tokens={total_tokens})")
            self._summarize_old_turns(user_name)

    def _format_history(self, user_name: str) -> str:
        """Format conversation history with summary + recent exchanges."""
        hist = self.conversation_history.get(user_name)
        if not hist or (not hist.raw and not hist.summary):
            return "No previous conversation."
        
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

    def chat_with_binat(self, user_query: str, user_name: str = None, pdn_code: str = None) -> str:
        """Generate response using PDN prompt."""
        if not self._check_conversation_limit(user_name):
            return "הגעת למגבלת השיחות להיום, אנא חזור אלינו מחר."

        # Increment count immediately after limit check to prevent race conditions
        if user_name:
            self._increment_conversation_count(user_name)

        system_prompt = self._load_prompt(pdn_code, "binat_agent.prompt")
        history_context = self._format_history(user_name)
        enhanced_question = f"User Name is: {user_name}\nUser PDN Code is: {pdn_code}\n{user_query}"

        user_message = f"Conversation History:\n{history_context}\n\nCurrent Question:\n{enhanced_question}"

        response_text = self.llm.invoke([
            SystemMessage(content=system_prompt),
            HumanMessage(content=user_message)
        ]).content

        if user_name:
            self._add_to_history(user_name, user_query, response_text)

        return response_text

    def build_21_transformation_plan(self, user_goal: str, user_name: str, pdn_code: str) -> str:
        """Generate 21-day transformation plan."""
        if not self._check_conversation_limit(user_name):
            return "הגעת למגבלת השיחות להיום, אנא חזור אלינו מחר."

        # Increment count immediately after limit check to prevent race conditions
        if user_name:
            self._increment_conversation_count(user_name)

        system_prompt = self._load_prompt(pdn_code, "21_plan.prompt")
        user_message = f"user_name: {user_name}\nuser_pdn_code: {pdn_code}\nuser_goal: {user_goal}"

        response_text =  self.llm.invoke([
            SystemMessage(content=system_prompt),
            HumanMessage(content=user_message)
        ]).content

        if user_name:
            self._add_to_history(user_name, user_goal, response_text)

        return response_text

    def daily_training(self, user_name: str, pdn_code: str, day_task: str) -> str:
        """Generate personalized daily training response."""
        if not self._check_conversation_limit(user_name):
            return "הגעת למגבלת השיחות להיום, אנא חזור אלינו מחר."

        # Increment count immediately after limit check to prevent race conditions
        if user_name:
            self._increment_conversation_count(user_name)

        system_prompt = self._load_prompt(pdn_code, "daily_training.prompt")
        user_message = f"User name: {user_name}\n User day Task: {day_task}\n."

        response_text = self.llm.invoke([
            SystemMessage(content=system_prompt),
            HumanMessage(content=user_message)
        ]).content

        if user_name:
            self._add_to_history(user_name, day_task, response_text)

        return response_text
