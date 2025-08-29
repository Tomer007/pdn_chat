from langchain_openai import ChatOpenAI
from langchain.prompts import ChatPromptTemplate, SystemMessagePromptTemplate, HumanMessagePromptTemplate
from pathlib import Path
import os
import logging
from collections import defaultdict

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
    raise ValueError("OPENAI_API_KEY environment variable is not set. Please set it before running the application.")

class A7Agent:
    """
    A7 Agent for PDN chat system that provides prompt-based responses with conversation history.
    """
    _instance = None
    
    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self, temperature: float = 0.7):
        """
        Initialize the A7 Agent.
        
        Args:
            temperature: Controls randomness in the LLM response (0.0 = deterministic, 1.0 = very random)
        """
        # Check if already initialized to prevent re-initialization
        if hasattr(self, '_initialized'):
            return
        self._initialized = True
        
        self.temperature = temperature
        self.max_history = 5  # Maximum number of messages to keep per user
        
        # Setup the LLM
        self.llm = ChatOpenAI(
            model="gpt-4o-mini", 
            temperature=self.temperature
        )
        
        # Load the A7 agent prompt
        self.system_prompt = self._load_system_prompt()
        
        # Build prompt template
        self.prompt = ChatPromptTemplate.from_messages([
            SystemMessagePromptTemplate.from_template(self.system_prompt),
            HumanMessagePromptTemplate.from_template("Conversation History:\n{history}\n\nCurrent Question: {question}\n\nAnswer:")
        ])
        
        # In-memory conversation history storage
        self.conversation_history = defaultdict(list)
        
        logger.info("A7 Agent initialized successfully.")

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
                    else:
                        logger.error("A7 agent prompt file is empty")
                        raise ValueError("A7 agent prompt file is empty")
            else:
                logger.error("A7 agent prompt file not found")
                raise FileNotFoundError("A7 agent prompt file not found")
        except Exception as e:
            logger.error(f"Error loading A7 agent prompt: {e}")
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
            self.conversation_history[user_name] = self.conversation_history[user_name][-self.max_history:]
        
        logger.debug(f"Added to history for {user_name}. Total exchanges: {len(self.conversation_history[user_name])}")

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
            logger.info(f"A7 Agent query from {user_name}: {user_query}")
        
            # Get conversation history for the user
            history_context = self._format_history(user_name)
            
            # Add user information to the question if provided
            enhanced_question = user_query

            user_context = f"User Name is: {user_name }\n"
            user_context += f"User PDN Code is: {pdn_code }\n"
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
            
        except Exception as e:
            logger.error(f"Error in A7 Agent response generation: {e}")
            return "I apologize, but I encountered an error while processing your request. Please try again."

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
                logger.info(f"Cleared conversation history for user: {user_name}")
                return True
            return False
        except Exception as e:
            logger.error(f"Error clearing history for user {user_name}: {e}")
            return False

    