"""
LangSmith Configuration Utility

This module provides centralized LangSmith configuration and utilities
for tracing and monitoring LangChain operations across the PDN Chat application.
"""

import os
import logging
from typing import Optional
from langsmith import Client

logger = logging.getLogger(__name__)


class LangSmithConfig:
    """Centralized LangSmith configuration and client management."""
    
    def __init__(self):
        """Initialize LangSmith configuration."""
        self.api_key = os.getenv("LANGSMITH_API_KEY", "")
        self.project = os.getenv("LANGSMITH_PROJECT", "PDN_CHAT")
        self.endpoint = os.getenv("LANGSMITH_ENDPOINT", "https://api.smith.langchain.com")
        self.tracing_v2 = os.getenv("LANGSMITH_TRACING_V2", "true").lower() == "true"
        
        # Initialize client
        self.client = self._create_client()
        
        logger.info(f"LangSmith configured - Project: {self.project}, Tracing V2: {self.tracing_v2}")
    
    def _create_client(self) -> Optional[Client]:
        """Create LangSmith client with error handling."""
        try:
            client = Client(
                api_key=self.api_key,
                api_url=self.endpoint
            )
            logger.info("LangSmith client initialized successfully")
            return client
        except Exception as e:
            logger.warning(f"Failed to initialize LangSmith client: {e}")
            return None
    
    def is_enabled(self) -> bool:
        """Check if LangSmith tracing is enabled."""
        return self.tracing_v2 and self.client is not None
    
    def get_project_name(self) -> str:
        """Get the current project name."""
        return self.project
    
    def get_client(self) -> Optional[Client]:
        """Get the LangSmith client instance."""
        return self.client


# Global LangSmith configuration instance
langsmith_config = LangSmithConfig()


def get_langsmith_config() -> LangSmithConfig:
    """Get the global LangSmith configuration instance."""
    return langsmith_config


def is_langsmith_enabled() -> bool:
    """Check if LangSmith tracing is enabled."""
    return langsmith_config.is_enabled()


def get_langsmith_client() -> Optional[Client]:
    """Get the LangSmith client instance."""
    return langsmith_config.get_client()
