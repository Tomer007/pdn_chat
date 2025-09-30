"""
PDNAgent - Single agent for all PDN chat interactions.
Dynamically loads prompts based on PDN code.
"""

import logging
import threading
import time
from collections import defaultdict
from functools import wraps
from pathlib import Path
from typing import Dict

from langchain.prompts import (
    ChatPromptTemplate,
    HumanMessagePromptTemplate,
    SystemMessagePromptTemplate,
)
from langchain_openai import ChatOpenAI
import os

# Check if OpenAI API key is set in environment
if not os.getenv("OPENAI_API_KEY"):
    raise ValueError(
        "OPENAI_API_KEY environment variable is not set. "
        "Please set it before running the application."
    )


def retry_on_failure(max_retries: int = 3, delay: float = 1.0, backoff: float = 2.0):
    """
    Decorator to retry function calls on failure with exponential backoff.
    
    Args:
        max_retries: Maximum number of retry attempts
        delay: Initial delay between retries in seconds
        backoff: Multiplier for delay after each retry
    """
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            current_delay = delay
            last_exception = None
            
            for attempt in range(max_retries + 1):
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    last_exception = e
                    if attempt < max_retries:
                        logger = logging.getLogger("pdn_agent")
                        logger.warning(
                            "Attempt %d failed for %s: %s. Retrying in %.2f seconds...",
                            attempt + 1, func.__name__, str(e), current_delay
                        )
                        time.sleep(current_delay)
                        current_delay *= backoff
                    else:
                        logger = logging.getLogger("pdn_agent")
                        logger.error(
                            "All %d attempts failed for %s. Last error: %s",
                            max_retries + 1, func.__name__, str(e)
                        )
            
            # If all retries failed, raise the last exception
            raise last_exception
        return wrapper
    return decorator


class PDNAgent:
    """Single agent for all PDN chat interactions."""

    def __init__(self):
        """Initialize the PDN agent with common functionality."""
        self.agent_name = "PDN"
        self.llm = ChatOpenAI(
            model="gpt-4o-mini",
            temperature=0.7,
            max_tokens=2000,
            request_timeout=120  # 2 minute timeout for complex requests
        )
        
        # Conversation history storage
        self.conversation_history = defaultdict(list)
        self.max_history = 10  # Keep last 10 exchanges per user
        self._history_lock = threading.Lock()
        
        # Load 21-day plan prompt (common for all PDN codes)
        self.plan_prompt = self._load_21_day_plan_prompt()
        
        # Configure logging
        self.logger = logging.getLogger("pdn_agent")
        self.logger.setLevel(logging.INFO)
        
        # Start cleanup thread for conversation history
        self._start_cleanup_thread()

    def _start_cleanup_thread(self):
        """Start background thread for conversation history cleanup."""
        def cleanup_worker():
            while True:
                try:
                    time.sleep(3600)  # Run every hour
                    self._cleanup_old_conversations()
                except Exception as e:
                    self.logger.error("Error in cleanup thread: %s", e)
        
        cleanup_thread = threading.Thread(target=cleanup_worker, daemon=True)
        cleanup_thread.start()
        self.logger.info("Started conversation history cleanup thread")

    def _cleanup_old_conversations(self):
        """Clean up old conversation histories to prevent memory leaks."""
        with self._history_lock:
            current_time = time.time()
            users_to_remove = []
            
            for user_name, history in self.conversation_history.items():
                # Remove users with no recent activity (older than 24 hours)
                if not history or len(history) == 0:
                    users_to_remove.append(user_name)
                    continue
                
                # Keep only last 5 exchanges for very old conversations
                if len(history) > 5:
                    self.conversation_history[user_name] = history[-5:]
            
            # Remove empty user histories
            for user_name in users_to_remove:
                del self.conversation_history[user_name]
                self.logger.debug("Cleaned up empty history for user: %s", user_name)
            
            if users_to_remove:
                self.logger.info("Cleaned up %d inactive user histories", len(users_to_remove))

    def _get_prompt_filename(self, pdn_code: str) -> str:
        """Return the filename for the given PDN code's prompt."""
        pdn_code = pdn_code.upper()
        if pdn_code == "A7":
            return "a7_agent.prompt"
        elif pdn_code == "E5":
            return "e5_agent.prompt"
        elif pdn_code == "P6":
            return "p6_agent.prompt"
        else:
            # Default to A7 if unknown PDN code
            self.logger.warning(f"Unknown PDN code: {pdn_code}, using A7 prompt")
            return "a7_agent.prompt"

    def _load_system_prompt(self, pdn_code: str) -> ChatPromptTemplate:
        """Load the system prompt from file based on PDN code."""
        
        base_prompt_path = Path(__file__).parent / "prompts/base_agent.prompt"

        prompt_filename = self._get_prompt_filename(pdn_code)
        prompt_path = Path(__file__).parent / "prompts" / prompt_filename
        
        self.logger.debug(f"Loading base prompt from {base_prompt_path}")
        self.logger.debug(f"Loading prompt for PDN code {pdn_code} from {prompt_filename}")
        
        with open(base_prompt_path, 'r', encoding='utf-8') as f:
            base_prompt_text = f.read()

        with open(prompt_path, 'r', encoding='utf-8') as f:
            pdn_code_prompt_text = f.read()
        
        system_message = SystemMessagePromptTemplate.from_template(base_prompt_text + pdn_code_prompt_text)

        human_message = HumanMessagePromptTemplate.from_template(
            "Previous conversation:\n{history}\n\nUser question: {question}"
        )
        
        return ChatPromptTemplate.from_messages([system_message, human_message])

    def _load_21_day_plan_prompt(self) -> ChatPromptTemplate:
        """Load the 21-day plan prompt from file."""
        prompt_path = Path(__file__).parent / "prompts" / "21_plan.prompt"
        with open(prompt_path, 'r', encoding='utf-8') as f:
            prompt_text = f.read()
        
        system_message = SystemMessagePromptTemplate.from_template(prompt_text)
        human_message = HumanMessagePromptTemplate.from_template(
            "User goals and success criteria: {goals_and_success}"
        )
        
        return ChatPromptTemplate.from_messages([system_message, human_message])

    def _add_to_history(self, user_name: str, user_query: str, assistant_response: str):
        """Add a conversation exchange to the user's history."""
        with self._history_lock:
            self.conversation_history[user_name].append({
                "user": user_query,
                "assistant": assistant_response
            })
            
            # Keep only the last max_history messages
            if len(self.conversation_history[user_name]) > self.max_history:
                self.conversation_history[user_name] = self.conversation_history[user_name][-self.max_history:]
            
            self.logger.debug("Added conversation exchange for user %s. Total exchanges: %d", 
                            user_name, len(self.conversation_history[user_name]))

    def _format_history(self, user_name: str) -> str:
        """Format conversation history for the prompt."""
        if not user_name or user_name not in self.conversation_history:
            self.logger.debug("No conversation history found for user: %s", user_name)
            return "No previous conversation."
        
        history = self.conversation_history[user_name]
        if not history:
            self.logger.debug("Empty conversation history for user: %s", user_name)
            return "No previous conversation."
        
        self.logger.debug("Found %d conversation exchanges for user: %s", len(history), user_name)
        
        formatted_lines = []
        for exchange in history:
            formatted_lines.append(f"User: {exchange['user']}")
            formatted_lines.append(f"Assistant: {exchange['assistant']}")
            formatted_lines.append("")

        return "\n".join(formatted_lines).strip()

    @retry_on_failure(max_retries=2, delay=1.0, backoff=2.0)
    def chat_with_user(self, user_query: str, user_name: str = None, pdn_code: str = None) -> str:
        """Generate a response for the user query using the appropriate PDN prompt."""
        self.logger.info("Processing query from %s (PDN: %s)", user_name, pdn_code)

        # Load the appropriate prompt for the PDN code
        prompt = self._load_system_prompt(pdn_code)
        
        # Get conversation history for the user
        history_context = self._format_history(user_name)
        
        # Add user context
        user_context = f"User Name is: {user_name}\n"
        user_context += f"User PDN Code is: {pdn_code}\n"
        enhanced_question = user_context + user_query

        # Generate response using LLM
        llm_response = self.llm.invoke(prompt.format_messages(
            history=history_context,
            question=enhanced_question
        ))
        response_text = llm_response.content

        # Add to conversation history
        if user_name:
            self._add_to_history(user_name, user_query, response_text)

        return response_text

    @retry_on_failure(max_retries=2, delay=1.0, backoff=2.0)
    def get_response_for_21_day_plan(self, user_goals_and_success: str, user_name: str, pdn_code: str) -> str:
        """Generate a 21-day transformation plan for the user."""
        self.logger.info("Generating 21-day plan for %s (PDN: %s)", user_name, pdn_code)

        # Generate plan using LLM
        llm_response = self.llm.invoke(self.plan_prompt.format_messages(
            goals_and_success=user_goals_and_success
        ))
        plan_text = llm_response.content

        return plan_text

    def clear_user_history(self, user_name: str):
        """Clear conversation history for a specific user."""
        with self._history_lock:
            if user_name in self.conversation_history:
                del self.conversation_history[user_name]
                self.logger.info("PDN Agent cleared conversation history for user: %s", user_name)
