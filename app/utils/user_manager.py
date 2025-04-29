from typing import List, Dict
import json
from pathlib import Path

USERS_FILE = Path("saved_results/users.json")
USERS_FILE.parent.mkdir(parents=True, exist_ok=True)

def load_all_users_from_db() -> List[Dict]:
    if not USERS_FILE.exists():
        return []
    
    with open(USERS_FILE, 'r', encoding='utf-8') as f:
        return json.load(f)

def save_user_to_db(user_data: Dict) -> None:
    users = load_all_users_from_db()
    users.append(user_data)
    
    with open(USERS_FILE, 'w', encoding='utf-8') as f:
        json.dump(users, f, ensure_ascii=False, indent=2)
