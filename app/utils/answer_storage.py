import json
from pathlib import Path
from typing import Dict, Any
from datetime import datetime

ANSWERS_DIR = Path("saved_results/temp_answers")

# Make sure the directory exists
ANSWERS_DIR.mkdir(parents=True, exist_ok=True)

def save_answer(email: str, question_number: int, answer_data: dict):
    """Save a single answer to the user's temp file."""
    file_path = ANSWERS_DIR / f"answers_{email}.json"
    
    if file_path.exists():
        with open(file_path, "r", encoding="utf-8") as f:
            data = json.load(f)
    else:
        data = {}

    data[str(question_number)] = answer_data

    with open(file_path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

def load_answers(email: str) -> dict:
    """Load all answers from the user's temp file."""
    sanitized_email = email.replace("@", "_at_").replace(".", "_dot_")
    file_path = ANSWERS_DIR / f"answers_{sanitized_email}.json"

    if not file_path.exists():
        return {}
    
    with open(file_path, "r", encoding="utf-8") as f:
        return json.load(f)

def clear_answers(email: str):
    """Delete the user's temp answer file."""
    sanitized_email = email.replace("@", "_at_").replace(".", "_dot_")
    file_path = ANSWERS_DIR / f"answers_{sanitized_email}.json"

    if file_path.exists():
        file_path.unlink()

def save_user_metadata(metadata: Dict[str, Any], email: str = None) -> None:
    """
    Save user metadata to the answers JSON file with proper Hebrew encoding.
    Includes timestamp in filename.
    """
    if not email:
        raise ValueError("Email is required to save user metadata")
        
    # Generate timestamp
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    file_path = ANSWERS_DIR / f"answers_{email}.json"
    file_path.parent.mkdir(parents=True, exist_ok=True)
    
    if file_path.exists():
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
    else:
        data = {}
    
    # Update metadata
    data['metadata'] = metadata
    
    # Save with proper Hebrew encoding
    with open(file_path, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
