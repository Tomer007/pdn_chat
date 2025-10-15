"""PDNAgent - Single agent for all PDN chat interactions."""

import logging
import os
import threading
import time
from collections import defaultdict
from pathlib import Path

from langchain_core.messages import SystemMessage, HumanMessage
from langchain_openai import ChatOpenAI

if not os.getenv("OPENAI_API_KEY"):
    raise ValueError("OPENAI_API_KEY not set")
else:
    print("OPENAI_API_KEY 1 is set--" + os.getenv("OPENAI_API_KEY")  + "--ttt")

class PDNAgent:
    """Single agent for all PDN chat interactions."""

    def __init__(self):
        """Initialize the PDN agent."""
        self.llm = ChatOpenAI(model="gpt-4o-mini", temperature=0.7, max_tokens=4000)
        self.conversation_history = defaultdict(list)
        self.max_history = 10
        self._history_lock = threading.Lock()
        self.logger = logging.getLogger("pdn_agent")
        self._prompt_cache = {}
        self._start_cleanup_thread()

    def _start_cleanup_thread(self):
        """Start background thread for history cleanup."""
        def cleanup_worker():
            while True:
                time.sleep(3600)
                try:
                    self._cleanup_old_conversations()
                except Exception as e:
                    self.logger.error("Cleanup error: %s", e)

        threading.Thread(target=cleanup_worker, daemon=True).start()

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
        if cache_key in self._prompt_cache:
            return self._prompt_cache[cache_key]

        prompts_dir = Path(__file__).parent / "prompts"
        pdn_codes_prompts_dir = Path(__file__).parent / "prompts/pdn_code/"
        prompt = (prompts_dir / prompt_file).read_text(encoding='utf-8') + \
                 (pdn_codes_prompts_dir / f"{pdn_code}.prompt").read_text(encoding='utf-8')

        self._prompt_cache[cache_key] = prompt
        return prompt

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


    def build_21_transformation_plan(self, user_goals_and_success: str, user_name: str, pdn_code: str) -> str:
        """Generate 21-day transformation plan."""
        system_prompt = self._load_prompt(pdn_code, "21_plan.prompt")
        user_message = f"User Name: {user_name}\nPDN Code: {pdn_code}\nGoals and Success: {user_goals_and_success}"

        return self.llm.invoke([
            SystemMessage(content=system_prompt),
            HumanMessage(content=user_message)
        ]).content

    def daily_training(self, user_name: str, pdn_code: str, day_task: str, user_replication: str) -> str:
        """Generate personalized daily training response."""
        system_prompt = self._load_prompt(pdn_code, "daily_training.prompt")
        user_message = f"User name: {user_name}\n User day Task: {day_task}\n User reaction to task::\n{user_replication}\nאנא תן לי משוב אישי על המשימה והתגובה שלי."

        response_text = self.llm.invoke([
            SystemMessage(content=system_prompt),
            HumanMessage(content=user_message)
        ]).content

        if user_name:
            self._add_to_history(user_name, f"Daily Training - Task: {day_task}, Response: {user_replication}", response_text)

        return response_text

    def clear_user_history(self, user_name: str):
        """Clear conversation history for user."""
        with self._history_lock:
            self.conversation_history.pop(user_name, None)
