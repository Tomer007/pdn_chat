import json
import os
from datetime import datetime
from typing import Dict, Any, Optional

from .csv_metadata_handler import UserMetadataHandler
from .pdn_file_path import PDNFilePath

# Initialize the utility
pdn_file_path = PDNFilePath()


def save_answer(email: str, question_number: int, answer_data: dict, question_text: str = None):
    """Save a single answer to the user's temp file."""

    # Create filename
    file_extension = ".json"
    filename = f"{email}_answers{file_extension}"

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
    Load user answers from a JSON file
    """
    try:
        # Try to load the complete answers file first (with underscore suffix)
        file_extension = ".json"
        complete_filename = f"{email}_answers_{file_extension}"
        complete_file_path = pdn_file_path.get_user_file_path(email, complete_filename)

        # If complete file exists, load it
        if os.path.exists(complete_file_path) and not os.path.isdir(complete_file_path):
            with open(complete_file_path, "r", encoding="utf-8") as f:
                answers = json.load(f)
                print(f"Successfully loaded complete answers for {email}")
                return answers

        # Fallback to regular answers file
        filename = f"{email}_answers{file_extension}"
        file_path = pdn_file_path.get_user_file_path(email, filename)

        # Check if the path exists and is a file (not a directory)
        if not os.path.exists(file_path):
            print(f"Answers file not found for {email}")
            return None

        if os.path.isdir(file_path):
            print(f"Path exists but is a directory, not a file: {file_path}")
            # Try to remove the directory if it exists
            try:
                os.rmdir(file_path)
                print(f"Removed directory: {file_path}")
            except OSError as e:
                print(f"Could not remove directory {file_path}: {e}")
            return None

        # Load the JSON file
        with open(file_path, "r", encoding="utf-8") as f:
            answers = json.load(f)
            print(f"Successfully loaded answers for {email}")
            return answers

    except FileNotFoundError:
        print(f"Answers file not found for {email}")
        return None
    except json.JSONDecodeError as e:
        print(f"Error decoding JSON for {email}: {e}")
        return None
    except Exception as e:
        print(f"Error loading answers for {email}: {e}")
        return None





def save_user_metadata(metadata: Dict[str, Any], email: str = None) -> None:
    """
    Save user metadata to the answers JSON file with proper Hebrew encoding.
    Includes timestamp in filename.
    """
    if not email:
        raise ValueError("Email is required to save user metadata")

    # Create filename
    file_extension = ".json"
    filename = f"{email}_answers{file_extension}"

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
