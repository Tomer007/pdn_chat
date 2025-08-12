from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_openai import OpenAIEmbeddings, ChatOpenAI
from langchain_community.vectorstores import Chroma

from langchain.prompts import ChatPromptTemplate, SystemMessagePromptTemplate, HumanMessagePromptTemplate
from pathlib import Path
from langchain_community.document_loaders import PyPDFLoader, UnstructuredWordDocumentLoader
import os
import logging
from ..utils.conversation_history import conversation_history
from ..data.config import settings

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('pdn_rag.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Check if OpenAI API key is set in environment
if not os.getenv("OPENAI_API_KEY"):
    raise ValueError("OPENAI_API_KEY environment variable is not set. Please set it before running the application.")

# Import system prompt from prompts module
from ..prompts import BINT_CHAT_SOURCE_PROMPT

class PDNRAG:

    @staticmethod
    def load_documents(directory_path):
        documents = []
        for file in Path(directory_path).glob("*"):
            if file.suffix.lower() == ".pdf":
                loader = PyPDFLoader(str(file))
                docs = loader.load()
            elif file.suffix.lower() == ".docx":
                loader = UnstructuredWordDocumentLoader(str(file))
                docs = loader.load()
            else:
                continue

            for doc in docs:
                doc.metadata["source"] = file.name
            documents.extend(docs)
        return documents

    def __init__(
        self,
        docs_path: str,
        persist_dir: str = None,
        persist: bool = True
    ):
        """
        Initialize the RAG pipeline.
        :param docs_path: Path to the Hebrew text documents.
        :param persist_dir: Directory for Chroma vector database persistence.
        :param persist: Whether to persist and reuse Chroma DB.
        """
        embeddings = OpenAIEmbeddings(model="text-embedding-3-large")
        
        # Load persisted DB if exists
        if persist and Path(persist_dir).exists():
            logger.info("Loading existing Chroma vectorstore...")
            self.vectorstore = Chroma(persist_directory=persist_dir, embedding_function=embeddings)
            logger.info("Chroma vectorstore loaded successfully.")  
        else:
            # Load and prepare documents
            logger.info("Loading documents...")
            docs = self.load_documents(docs_path)
            logger.info(f"Loaded {len(docs)} documents")

            logger.info("Splitting documents...")
            splitter = RecursiveCharacterTextSplitter(
                chunk_size=settings.RAG_CHUNK_SIZE, 
                chunk_overlap=settings.RAG_CHUNK_OVERLAP
            )
            docs = splitter.split_documents(docs)

            logger.info("Creating embeddings and vector store...")
            self.vectorstore = Chroma.from_documents(docs, embeddings, persist_directory=persist_dir)
            logger.info("Chroma vectorstore created successfully.")

        # Setup retriever
        logger.info("Setting up retriever and QA chain...")
        self.retriever = self.vectorstore.as_retriever(
            search_type="similarity", 
            search_kwargs={"k": settings.RAG_SEARCH_K}
        )

        # Build prompt template with PDN chat source prompt
        self.prompt = ChatPromptTemplate.from_messages([
            SystemMessagePromptTemplate.from_template(BINT_CHAT_SOURCE_PROMPT),
            HumanMessagePromptTemplate.from_template("Context: {context}\n\nQuestion: {question}\n\nAnswer:")
        ])

        # Setup the LLM with system prompt
        self.llm = ChatOpenAI(model="gpt-4o-mini", temperature=0.5)
        self.qa_chain = self.prompt | self.llm

        logger.info("RAG setup complete.")

    def retrieve(self, user_query: str, user_name: str = None, user_id: str = None, pdn_code: str = None) -> str:
        """
        Retrieve and generate an answer for a given user query using the PDN RAG system.
        """
        # Log user information if provided
        user_info = ""
        if user_name or user_id:
            user_info = f" (User: {user_name or 'Unknown'}, ID: {user_id or 'Unknown'}, PDN Code: {pdn_code or 'Unknown'})"
        
        logger.info(f"Querying: {user_query}{user_info}")  
        try:
            # Retrieve relevant documents
            docs = self.retriever.invoke(user_query)
            
            # Combine context from documents
            context = "\n\n".join([doc.page_content for doc in docs])
            
            # Add conversation history if user_id is provided
            conversation_context = ""
            if user_id:
                conversation_context = conversation_history.get_conversation_context(user_id)
                if conversation_context:
                    context = f"Previous Conversation:\n{conversation_context}\n\nDocument Context:\n{context}"
            
            # Add user information to the question if provided
            enhanced_question = user_query
            if user_name or user_id:
                user_context = f"User Name is: {user_name }\nUser PDN Code is: {pdn_code }\nUser ID is: {user_id }\n"
                enhanced_question = user_context + user_query
            
            # Generate response using the LLM chain
            input_data = {"context": context, "question": enhanced_question}
            llm_response = self.qa_chain.invoke(input_data)
            response_text = llm_response.content
            logger.debug(f"LLM response: {llm_response}")
            
            # Store conversation history if user_id is provided
            if user_id:
                conversation_history.add_message(user_id, user_query, response_text, user_name)
                logger.info(f"Conversation history stored for user {user_id}")
            
            return response_text
        except Exception as e:
            logger.error(f"Error in RAG chain: {e}")
            raise e
    
