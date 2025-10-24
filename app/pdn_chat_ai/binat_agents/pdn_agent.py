"""PDNAgent - Single agent for all PDN chat interactions."""

import logging
import os
import threading
import time
from collections import defaultdict
from pathlib import Path

from langchain_core.messages import SystemMessage, HumanMessage
from langchain_openai import ChatOpenAI
from langchain_anthropic import ChatAnthropic

# Import configuration
import sys
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..', '..'))
from config import Config

class PDNAgent:
    """Single agent for all PDN chat interactions."""

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
        
        self.conversation_history = defaultdict(list)
        self.max_history = 4
        self._history_lock = threading.Lock()
        self.logger = logging.getLogger("pdn_agent")
        self._prompt_cache = {}
        self._prompts_dir = Path(__file__).parent / "prompts"
        
        threading.Thread(target=self._cleanup_worker, daemon=True).start()
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

    def _cleanup_worker(self):
        """Background worker for history cleanup."""
        while True:
            time.sleep(3600)
            try:
                self._cleanup_old_conversations()
            except Exception as e:
                self.logger.error("Cleanup error: %s", e)

    def _cleanup_old_conversations(self):
        """Clean up old conversation histories."""
        with self._history_lock:
            users_to_remove = [user for user, hist in self.conversation_history.items() if not hist]

            for user_name in users_to_remove:
                del self.conversation_history[user_name]

            for user_name, history in self.conversation_history.items():
                if len(history) > 5:
                    self.conversation_history[user_name] = history[-5:]

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

    def _add_to_history(self, user_name: str, user_query: str, assistant_response: str):
        """Add conversation exchange to history."""
        with self._history_lock:
            self.conversation_history[user_name].append({"user": user_query, "assistant": assistant_response})
            if len(self.conversation_history[user_name]) > self.max_history:
                self.conversation_history[user_name] = self.conversation_history[user_name][-self.max_history:]

    def _format_history(self, user_name: str) -> str:
        """Format conversation history."""
        history = self.conversation_history.get(user_name)
        return "No previous conversation." if not history else \
               "\n\n".join(f"User: {ex['user']}\nAssistant: {ex['assistant']}" for ex in history)

    def clear_user_history(self, user_name: str):
        """Clear conversation history for user."""
        with self._history_lock:
            self.conversation_history.pop(user_name, None)

    def chat_with_binat(self, user_query: str, user_name: str = None, pdn_code: str = None) -> str:
        """Generate response using PDN prompt."""
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
        system_prompt = self._load_prompt(pdn_code, "21_plan.prompt")
        user_message = f"user_name: {user_name}\nuser_pdn_code: {pdn_code}\nGoal: {user_goal}"

        response_text =  self.llm.invoke([
            SystemMessage(content=system_prompt),
            HumanMessage(content=user_message)
        ]).content

        if user_name:
            self._add_to_history(user_name, user_goal, response_text)

        return response_text

    def daily_training(self, user_name: str, pdn_code: str, day_task: str) -> str:
        """Generate personalized daily training response."""
        system_prompt = self._load_prompt(pdn_code, "daily_training.prompt")
        user_message = f"User name: {user_name}\n User day Task: {day_task}\n."

        response_text = self.llm.invoke([
            SystemMessage(content=system_prompt),
            HumanMessage(content=user_message)
        ]).content

        if user_name:
            self._add_to_history(user_name, day_task, response_text)

        return response_text

