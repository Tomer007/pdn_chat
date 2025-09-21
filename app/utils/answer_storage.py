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

from .csv_metadata_handler import UserMetadataHandler
from .pdn_file_path import PDNFilePath

# Initialize the utility
pdn_file_path = PDNFilePath()


def save_answer(email: str, question_number: int, answer_data: dict, question_text: str = None):
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

    if file_path.exists():
        with open(file_path, "r", encoding="utf-8") as f:
            data = json.load(f)
    else:
        data = {}

    # Filter out None values from answer_data
    filtered_answer_data = {k: v for k, v in answer_data.items() if v is not None}

    # Add question text if provided
    if question_text:
        filtered_answer_data['question_text'] = question_text

    data[str(question_number)] = filtered_answer_data

    with open(file_path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def load_answers(email: str) -> Optional[Dict[str, Any]]:
    """
    Load user answers from a JSON file.
    
    Args:
        email (str): User's email address (used for file naming)
        
    Returns:
        Optional[Dict[str, Any]]: Dictionary containing all user answers, or None if file doesn't exist
    """
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
            return answers

    except (FileNotFoundError, json.JSONDecodeError):
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

    if file_path.exists():
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
    else:
        data = {}

    # Generate timestamp

    # Update metadata
    metadata['timestamp'] = datetime.now().strftime("%Y_%m_%d_%H_%M")
    data['metadata'] = metadata

    # Save with proper Hebrew encoding
    with open(file_path, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
