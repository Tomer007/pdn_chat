"""PDNAgent - Single agent for all PDN chat interactions."""

import logging
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, Any

from langchain_core.messages import HumanMessage

from app.pdn_relationships.agents.base_pdn_agent import BasePDNAgent, BaseAgentConfig, UserHistory
from config import Config


class PDNAgent(BasePDNAgent):
    """Single agent for all PDN chat interactions.

    Extends BasePDNAgent with PDN-specific chat methods:
    - chat_with_binat: General PDN chat
    - build_21_transformation_plan: 21-day plan generation
    - daily_training: Daily training responses
    - _load_prompt: PDN code prompt loading with caching
    """

    def __init__(self, llm_provider=None, model_name=None):
        """Initialize the PDN agent.

        Args:
            llm_provider (str, optional): LLM provider ('openai' or 'anthropic').
                                        Defaults to config value.
            model_name (str, optional): Model name to use. Defaults to config value.
        """
        agent_config = BaseAgentConfig(
            llm_provider=llm_provider,
            model_name=model_name,
        )
        super().__init__(config=agent_config)

        self._prompt_cache = {}
        self._prompts_dir = Path(__file__).parent / "prompts"

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

        response = self.llm.invoke([
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
