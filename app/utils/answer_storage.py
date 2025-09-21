"""
Answer Storage Module

This module provides functionality for saving and loading user questionnaire answers
and metadata. It handles JSON file operations with proper Hebrew encoding support
and integrates with the CSV metadata handler for comprehensive data management.

Key functions:
- save_answer: Save individual question answers
- load_answers: Load all user answers from JSON file
- save_user_metadata: Save user metadata with timestamp
"""

import json
import os
from datetime import datetime
from typing import Dict, Any, Optional
from functools import lru_cache

from .csv_metadata_handler import UserMetadataHandler
from .pdn_file_path import PDNFilePath

# Initialize the utility
pdn_file_path = PDNFilePath()

# Cache for frequently accessed data
_answer_cache: Dict[str, Dict[str, Any]] = {}
_cache_timestamp: Optional[datetime] = None
_cache_validity_seconds = 30  # Cache valid for 30 seconds


def _is_cache_valid() -> bool:
    """Check if the current cache is still valid."""
    global _cache_timestamp
    if _cache_timestamp is None:
        return False
    
    current_time = datetime.now()
    return (current_time - _cache_timestamp).total_seconds() < _cache_validity_seconds


def _invalidate_cache() -> None:
    """Invalidate the current cache."""
    global _answer_cache, _cache_timestamp
    _answer_cache.clear()
    _cache_timestamp = None


def _update_cache(email: str, data: Dict[str, Any]) -> None:
    """Update the cache with new data."""
    global _answer_cache, _cache_timestamp
    _answer_cache[email] = data
    _cache_timestamp = datetime.now()


def save_answer(email: str, question_number: int, answer_data: Dict[str, Any], question_text: Optional[str] = None) -> None:
    """
    Save a single answer to the user's temporary JSON file.
    
    Args:
        email (str): User's email address (used for file naming)
        question_number (int): The question number being answered
        answer_data (dict): Dictionary containing the answer data
        question_text (str, optional): The text of the question being answered
    """

    # Create filename
    filename = f"{email}_answers.json"
    file_path = pdn_file_path.get_user_file_path(email, filename)

    # Try to get data from cache first
    data = _answer_cache.get(email, {})
    
    # If not in cache or cache is invalid, load from file
    if not data or not _is_cache_valid():
        if file_path.exists():
            try:
                with open(file_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
            except (json.JSONDecodeError, IOError):
                data = {}
        else:
            data = {}
        
        # Update cache
        _update_cache(email, data)

    # Filter out None values from answer_data
    filtered_answer_data = {k: v for k, v in answer_data.items() if v is not None}

    # Add question text if provided
    if question_text:
        filtered_answer_data['question_text'] = question_text

    data[str(question_number)] = filtered_answer_data

    # Save to file
    try:
        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        
        # Update cache with new data
        _update_cache(email, data)
    except IOError as e:
        # If file write fails, invalidate cache
        _invalidate_cache()
        raise e


def load_answers(email: str) -> Optional[Dict[str, Any]]:
    """
    Load user answers from a JSON file with caching for performance.
    
    Args:
        email (str): User's email address (used for file naming)
        
    Returns:
        Optional[Dict[str, Any]]: Dictionary containing all user answers, or None if file doesn't exist
    """
    # Check cache first
    if _is_cache_valid() and email in _answer_cache:
        return _answer_cache[email]
    
    try:
        filename = f"{email}_answers.json"
        file_path = pdn_file_path.get_user_file_path(email, filename)

        # Check if the path exists and is a file (not a directory)
        if not os.path.exists(file_path):
            return None

        if os.path.isdir(file_path):
            # Try to remove the directory if it exists
            try:
                os.rmdir(file_path)
            except OSError:
                pass
            return None

        # Load the JSON file
        with open(file_path, "r", encoding="utf-8") as f:
            answers = json.load(f)
            
            # Update cache
            _update_cache(email, answers)
            return answers

    except (FileNotFoundError, json.JSONDecodeError, IOError):
        return None
    except Exception:
        return None


def save_user_metadata(metadata: Dict[str, Any], email: str = None) -> None:
    """
    Save user metadata to the answers JSON file with proper Hebrew encoding.
    
    Args:
        metadata (Dict[str, Any]): Dictionary containing user metadata
        email (str, optional): User's email address (required for file naming)
        
    Raises:
        ValueError: If email is not provided
    """
    if not email:
        raise ValueError("Email is required to save user metadata")

    # Create filename
    filename = f"{email}_answers.json"

    file_path = pdn_file_path.get_user_file_path(email, filename)

    csv_metadata_handler = UserMetadataHandler()
    csv_metadata_handler.append_user_metadata(metadata)

    # Try to get data from cache first
    data = _answer_cache.get(email, {})
    
    # If not in cache or cache is invalid, load from file
    if not data or not _is_cache_valid():
        if file_path.exists():
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
            except (json.JSONDecodeError, IOError):
                data = {}
        else:
            data = {}

    # Update metadata
    metadata['timestamp'] = datetime.now().strftime("%Y_%m_%d_%H_%M")
    data['metadata'] = metadata

    # Save with proper Hebrew encoding
    try:
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        
        # Update cache with new data
        _update_cache(email, data)
    except IOError as e:
        # If file write fails, invalidate cache
        _invalidate_cache()
        raise e
