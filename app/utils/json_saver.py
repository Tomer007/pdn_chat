import json
import os
from datetime import datetime
from pathlib import Path

def save_user_results(email: str, questions: list):
    """
    Save user questionnaire results to a JSON file.
    
    Args:
        email (str): User's email address
        questions (list): List of question-answer pairs
    """
    # Create saved_results directory if it doesn't exist
    saved_results_dir = Path("saved_results")
    saved_results_dir.mkdir(exist_ok=True)
    
    # Generate filename with email and timestamp
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"{email}_{timestamp}.json"
    filepath = saved_results_dir / filename
    
    # Prepare data structure
    data = {
        "questions": questions
    }
    
    # Save to JSON file
    with open(filepath, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    
    return str(filepath) 