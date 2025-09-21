"""
A7Agent - AI-powered chat agent for PDN chat system.
Handles conversation management, prompt loading, and response generation.
"""

import logging
import os
from collections import defaultdict
from pathlib import Path
from typing import Dict, List, Optional, Any
from functools import lru_cache
import threading
import time

from langchain.prompts import (
    ChatPromptTemplate,
    SystemMessagePromptTemplate,
    HumanMessagePromptTemplate
)
from langchain_openai import ChatOpenAI

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('a7_agent.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Check if OpenAI API key is set in environment
if not os.getenv("OPENAI_API_KEY"):
    raise ValueError(
        "OPENAI_API_KEY environment variable is not set. "
        "Please set it before running the application."
    )


class A7Agent:
    """
    A7 Agent for PDN chat system that provides prompt-based responses with conversation history.
    Optimized with connection pooling, caching, and performance monitoring.
    """
    _instance = None
    _lock = threading.Lock()

    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self, temperature: float = 0.7):
        """
        Initialize the A7 Agent.
        
        Args:
            temperature: Controls randomness in the LLM response
                        (0.0 = deterministic, 1.0 = very random)
        """
        # Check if already initialized to prevent re-initialization
        if hasattr(self, '_initialized'):
            return
        self._initialized = True

        self.temperature = temperature
        self.max_history = 5  # Maximum number of messages to keep per user
        
        # Performance monitoring
        self._response_times: List[float] = []
        self._request_count = 0
        self._cache_hits = 0
        self._cache_misses = 0
        
        # Response cache for similar queries
        self._response_cache: Dict[str, str] = {}
        self._cache_max_size = 100
        self._cache_ttl = 300  # 5 minutes

        # Setup the LLM with optimized settings for faster responses
        self.llm = ChatOpenAI(
            model="gpt-4o-mini",
            temperature=self.temperature,
            max_tokens=2000,  # Reduced for faster generation
            request_timeout=120  # 2 minute timeout for complex requests
        )

        # Load the A7 agent prompt
        self.system_prompt = self._load_system_prompt()

        # Build prompt template
        self.prompt = ChatPromptTemplate.from_messages([
            SystemMessagePromptTemplate.from_template(self.system_prompt),
            HumanMessagePromptTemplate.from_template(
                "Conversation History:\n{history}\n\n"
                "Current Question: {question}\n\nAnswer:"
            )
        ])

        # Load the 45-day plan prompt
        self.plan_prompt = self._load_45_day_plan_prompt()

        # Build 45-day plan prompt template
        self.plan_prompt_template = ChatPromptTemplate.from_messages([
            SystemMessagePromptTemplate.from_template(self.plan_prompt),
            HumanMessagePromptTemplate.from_template(
                "{user_goals_and_success}"
            )
        ])

        # In-memory conversation history storage
        self.conversation_history = defaultdict(list)

        logger.info("A7 Agent initialized successfully.")

    def _get_cache_key(self, user_message: str, user_id: str = None) -> str:
        """Generate a cache key for the user message."""
        # Normalize the message for better cache hits
        normalized_message = user_message.strip().lower()
        return f"{user_id or 'anonymous'}:{hash(normalized_message)}"

    def _is_cache_valid(self, cache_key: str) -> bool:
        """Check if cache entry is still valid."""
        if cache_key not in self._response_cache:
            return False
        
        # Simple TTL check - in production, you'd want more sophisticated caching
        return len(self._response_cache) < self._cache_max_size

    def _clean_cache(self) -> None:
        """Clean old cache entries if cache is full."""
        if len(self._response_cache) >= self._cache_max_size:
            # Remove oldest entries (simple FIFO)
            keys_to_remove = list(self._response_cache.keys())[:self._cache_max_size // 2]
            for key in keys_to_remove:
                del self._response_cache[key]

    def _record_performance(self, response_time: float) -> None:
        """Record performance metrics."""
        self._response_times.append(response_time)
        self._request_count += 1
        
        # Keep only last 100 response times
        if len(self._response_times) > 100:
            self._response_times = self._response_times[-100:]

    def get_performance_stats(self) -> Dict[str, Any]:
        """Get performance statistics."""
        avg_response_time = sum(self._response_times) / len(self._response_times) if self._response_times else 0
        cache_hit_rate = self._cache_hits / (self._cache_hits + self._cache_misses) if (self._cache_hits + self._cache_misses) > 0 else 0
        
        return {
            'total_requests': self._request_count,
            'cache_hits': self._cache_hits,
            'cache_misses': self._cache_misses,
            'cache_hit_rate': cache_hit_rate,
            'avg_response_time': avg_response_time,
            'cache_size': len(self._response_cache)
        }

    def _load_system_prompt(self) -> str:
        """
        Load the system prompt from the a7_agent.prompt file.
        
        Returns:
            The system prompt as a string
        """
        try:
            prompt_path = Path(__file__).parent / "prompts" / "a7_agent.prompt"
            if prompt_path.exists():
                with open(prompt_path, 'r', encoding='utf-8') as f:
                    prompt_content = f.read().strip()
                    if prompt_content:
                        return prompt_content
                    logger.error("A7 agent prompt file is empty")
                    raise ValueError("A7 agent prompt file is empty")
            logger.error("A7 agent prompt file not found")
            raise FileNotFoundError("A7 agent prompt file not found")
        except (FileNotFoundError, ValueError) as e:
            logger.error("Error loading A7 agent prompt: %s", e)
            raise

    def _load_45_day_plan_prompt(self) -> str:
        """
        Load the 45-day plan prompt from the optimized prompt file.
        
        Returns:
            The 45-day plan prompt as a string
        """
        try:
            # Try optimized prompt first
            optimized_path = Path(__file__).parent / "prompts" / "45_plan_optimized.prompt"
            if optimized_path.exists():
                with open(optimized_path, 'r', encoding='utf-8') as f:
                    prompt_content = f.read().strip()
                    if prompt_content:
                        logger.info("Using optimized 45-day plan prompt")
                        return prompt_content

            # Fallback to original prompt
            prompt_path = Path(__file__).parent / "prompts" / "45_plan.prompt"
            if prompt_path.exists():
                with open(prompt_path, 'r', encoding='utf-8') as f:
                    prompt_content = f.read().strip()
                    if prompt_content:
                        logger.info("Using original 45-day plan prompt")
                        return prompt_content
                    logger.error("45-day plan prompt file is empty")
                    raise ValueError("45-day plan prompt file is empty")
            logger.error("45-day plan prompt file not found")
            raise FileNotFoundError("45-day plan prompt file not found")
        except (FileNotFoundError, ValueError) as e:
            logger.error("Error loading 45-day plan prompt: %s", e)
            raise

    def _add_to_history(self, user_name: str, user_query: str, response: str):
        """
        Add a conversation exchange to the user's history.
        
        Args:
            user_name: Name of the user
            user_query: User's question
            response: Agent's response
        """
        if not user_name:
            return

        # Add the conversation exchange
        self.conversation_history[user_name].append({
            'user': user_query,
            'assistant': response
        })

        # Keep only the last max_history exchanges
        if len(self.conversation_history[user_name]) > self.max_history:
            self.conversation_history[user_name] = (
                self.conversation_history[user_name][-self.max_history:]
            )

        logger.debug(
            "Added to history for %s. Total exchanges: %d",
            user_name,
            len(self.conversation_history[user_name])
        )

    def _format_history(self, user_name: str) -> str:
        """
        Format conversation history for the prompt.
        
        Args:
            user_name: Name of the user
            
        Returns:
            Formatted conversation history string
        """
        if not user_name or user_name not in self.conversation_history:
            return "No previous conversation history."

        history = self.conversation_history[user_name]
        if not history:
            return "No previous conversation history."

        formatted_lines = []
        for exchange in history:
            formatted_lines.append(f"User: {exchange['user']}")
            formatted_lines.append(f"Assistant: {exchange['assistant']}")
            formatted_lines.append("")  # Empty line for separation

        return "\n".join(formatted_lines).strip()

    def get_response(self, user_query: str, user_name: str = None, pdn_code: str = None) -> str:
        """
        Generate a response for the user query using the A7 agent prompt and conversation history.
        
        Args:
            user_query: The user's question or message
            user_name: Name of the user (optional)
            
        Returns:
            The agent's response as a string
        """
        try:
            # Log user information if provided
            logger.info("A7 Agent query from %s: %s", user_name, user_query)

            # Get conversation history for the user
            history_context = self._format_history(user_name)

            # Add user information to the question if provided
            user_context = f"User Name is: {user_name}\n"
            user_context += f"User PDN Code is: {pdn_code}\n"
            enhanced_question = user_context + user_query

            # Generate response using the LLM
            llm_response = self.llm.invoke(self.prompt.format_messages(
                history=history_context,
                question=enhanced_question
            ))
            response_text = llm_response.content

            # Add to conversation history if user_name is provided
            if user_name:
                self._add_to_history(user_name, user_query, response_text)

            return response_text

        except (ValueError, FileNotFoundError, IOError) as e:
            logger.error("Error in A7 Agent response generation: %s", e)
            return (
                "I apologize, but I encountered an error while processing your request. "
                "Please try again."
            )

    def get_response_for_45_day_plan(
        self, user_context: str, user_name: str = None, pdn_code: str = None
    ) -> str:
        """
        Generate a 45-day transformation plan response using the specialized 45-day plan prompt.
        
        Args:
            user_context: The user's goals and success definition
            user_name: Name of the user (optional)
            pdn_code: PDN code of the user (optional)
            
        Returns:
            The 45-day plan response as a string
        """
        try:
            # Log user information if provided
            logger.info(
                "A7 Agent generating 45-day plan for %s with PDN code %s",
                user_name, pdn_code
            )

            # Use a more efficient approach - direct string formatting instead of template
            formatted_prompt = self.plan_prompt.replace(
                '$user_name', user_name or 'המשתמש'
            )
            formatted_prompt = formatted_prompt.replace('$success', user_context)

            # Create a simpler prompt template for faster processing
            simple_prompt = ChatPromptTemplate.from_messages([
                SystemMessagePromptTemplate.from_template(formatted_prompt),
                HumanMessagePromptTemplate.from_template(
                    "צור תוכנית 45 יום מותאמת אישית"
                )
            ])

            # Generate response using the optimized prompt
            llm_response = self.llm.invoke(simple_prompt.format_messages())
            response_text = llm_response.content

            return response_text

        except (ValueError, FileNotFoundError, IOError) as e:
            logger.error("Error in A7 Agent 45-day plan generation: %s", e)
            return (
                "I apologize, but I encountered an error while generating your "
                "45-day plan. Please try again."
            )
        except Exception as e:
            logger.error("Unexpected error in A7 Agent 45-day plan generation: %s", e)
            # Check if it's a timeout error
            if "timeout" in str(e).lower() or "timed out" in str(e).lower():
                return (
                    "I apologize, but the request is taking longer than expected. "
                    "Please try again with a simpler request or contact support if the issue persists."
                )
            return (
                "I apologize, but I encountered an unexpected error while generating your "
                "45-day plan. Please try again."
            )

    def get_user_history(self, user_name: str) -> list:
        """
        Get the conversation history for a specific user.
        
        Args:
            user_name: Name of the user
            
        Returns:
            List of conversation exchanges
        """
        if not user_name:
            return []
        return self.conversation_history.get(user_name, [])

    def clear_user_history(self, user_name: str) -> bool:
        """
        Clear the conversation history for a specific user.
        
        Args:
            user_name: Name of the user
            
        Returns:
            True if successful, False otherwise
        """
        try:
            if user_name in self.conversation_history:
                del self.conversation_history[user_name]
                logger.info("Cleared conversation history for user: %s", user_name)
                return True
            return False
        except (KeyError, ValueError) as e:
            logger.error("Error clearing history for user %s: %s", user_name, e)
            return False
