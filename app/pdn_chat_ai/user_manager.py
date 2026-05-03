"""UserManager - JSON file-backed user management with in-memory caching."""

import json
import logging
import re
import threading
from pathlib import Path
from typing import Optional

logger = logging.getLogger("pdn_chat_ai")

# Default seed data — used only on first run when users.json doesn't exist
_SEED_USERS = {
    'tomergur@gmail.com': {'password': 'pdn', 'pdn_code': 'e5', 'name': 'תומר', 'daily_conversation_limit': 100},
    'pdncode@gmail.com': {'password': 'pdn', 'pdn_code': 'a7', 'name': 'פנינה', 'daily_conversation_limit': 10},
    'anna123benyehuda@gmail.com': {'password': 'pdn', 'pdn_code': 'a3', 'name': 'אנה', 'daily_conversation_limit': 100},
    'yaelrapoport2@gmail.com': {'password': 'pdn', 'pdn_code': 'a3', 'name': 'יעל', 'daily_conversation_limit': 100},
    'einavmakover@gmail.com': {'password': 'pdn', 'pdn_code': 'e9', 'name': 'עינב', 'daily_conversation_limit': 100},
    'ronitamizur@gmail.com': {'password': 'pdn', 'pdn_code': 'p10', 'name': 'רונית', 'daily_conversation_limit': 100},
}

_EMAIL_PATTERN = re.compile(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$')


class UserManager:
    """Manages user data with JSON file persistence and in-memory caching."""

    PROMPTS_DIR = Path(__file__).parent / "binat_agents" / "prompts" / "pdn_code"

    def __init__(self, json_path: Optional[Path] = None):
        self._json_path = json_path or (Path(__file__).parent.parent / "data" / "users.json")
        self._users: dict = {}
        self._lock = threading.Lock()
        self._load_users()

    def _load_users(self) -> None:
        """Load users from JSON file, seeding from _SEED_USERS if file missing or corrupt."""
        with self._lock:
            if self._json_path.exists():
                try:
                    data = json.loads(self._json_path.read_text(encoding='utf-8'))
                    if isinstance(data, dict) and len(data) > 0:
                        self._users = data
                        return
                except (json.JSONDecodeError, OSError):
                    pass
            # Seed from hardcoded data
            self._users = dict(_SEED_USERS)
            self._save_to_file()

    def _save_to_file(self) -> None:
        """Persist current in-memory users to JSON file atomically."""
        tmp_path = self._json_path.with_suffix('.tmp')
        self._json_path.parent.mkdir(parents=True, exist_ok=True)
        tmp_path.write_text(
            json.dumps(self._users, ensure_ascii=False, indent=2),
            encoding='utf-8'
        )
        tmp_path.replace(self._json_path)

    def get_user(self, email: str) -> Optional[dict]:
        """Retrieve a single user by email. Returns None if not found."""
        with self._lock:
            user = self._users.get(email)
            return dict(user) if user else None

    def get_all_users(self) -> list:
        """Return all users as a list of dicts (passwords excluded)."""
        with self._lock:
            return [
                {
                    'email': email,
                    'name': data.get('name', ''),
                    'gender': data.get('gender', ''),
                    'pdn_code': data.get('pdn_code', ''),
                    'daily_conversation_limit': data.get('daily_conversation_limit', 15),
                }
                for email, data in self._users.items()
            ]

    def add_user(self, email: str, password: str, name: str,
                 pdn_code: str, daily_conversation_limit: int = 15,
                 gender: str = '') -> dict:
        """Add a new user. Raises ValueError if email exists or validation fails."""
        email = email.strip().lower()

        if not self.validate_email(email):
            raise ValueError("כתובת אימייל לא תקינה")
        if not password:
            raise ValueError("סיסמה נדרשת")
        if not name.strip():
            raise ValueError("שם נדרש")
        if gender and gender not in ('male', 'female'):
            raise ValueError("מין חייב להיות male או female")

        available_codes = self.get_available_pdn_codes()
        if pdn_code not in available_codes:
            raise ValueError(f"קוד PDN לא תקין: {pdn_code}")

        if not isinstance(daily_conversation_limit, int) or daily_conversation_limit < 1:
            raise ValueError("מגבלת שיחות יומית חייבת להיות מספר חיובי")

        with self._lock:
            if email in self._users:
                raise ValueError(f"משתמש עם אימייל {email} כבר קיים")

            self._users[email] = {
                'password': password,
                'pdn_code': pdn_code,
                'name': name.strip(),
                'gender': gender,
                'daily_conversation_limit': daily_conversation_limit,
            }
            self._save_to_file()

        logger.info("Added user: %s (%s)", email, pdn_code)
        return {'email': email, 'name': name.strip(), 'gender': gender,
                'pdn_code': pdn_code, 'daily_conversation_limit': daily_conversation_limit}

    def update_user(self, email: str, **updates) -> dict:
        """Update an existing user's fields. Raises KeyError if not found."""
        with self._lock:
            if email not in self._users:
                raise KeyError(f"משתמש {email} לא נמצא")

            allowed = {'password', 'name', 'gender', 'pdn_code', 'daily_conversation_limit'}
            for key in updates:
                if key not in allowed:
                    continue

                value = updates[key]
                if key == 'pdn_code':
                    available_codes = self.get_available_pdn_codes()
                    if value not in available_codes:
                        raise ValueError(f"קוד PDN לא תקין: {value}")
                elif key == 'daily_conversation_limit':
                    if not isinstance(value, int) or value < 1:
                        raise ValueError("מגבלת שיחות יומית חייבת להיות מספר חיובי")
                elif key == 'name' and not str(value).strip():
                    raise ValueError("שם נדרש")
                elif key == 'gender' and value and value not in ('male', 'female'):
                    raise ValueError("מין חייב להיות male או female")

                self._users[email][key] = value

            self._save_to_file()

        user = self._users[email]
        logger.info("Updated user: %s", email)
        return {'email': email, 'name': user['name'], 'gender': user.get('gender', ''),
                'pdn_code': user['pdn_code'], 'daily_conversation_limit': user['daily_conversation_limit']}

    def delete_user(self, email: str) -> None:
        """Remove a user by email. Raises KeyError if not found."""
        with self._lock:
            if email not in self._users:
                raise KeyError(f"משתמש {email} לא נמצא")
            del self._users[email]
            self._save_to_file()
        logger.info("Deleted user: %s", email)

    def get_available_pdn_codes(self) -> list:
        """Return PDN codes that have a matching .prompt file on disk."""
        if not self.PROMPTS_DIR.exists():
            return []
        return sorted(p.stem for p in self.PROMPTS_DIR.glob('*.prompt'))

    @staticmethod
    def validate_email(email: str) -> bool:
        """Validate email format using regex."""
        return bool(_EMAIL_PATTERN.match(email))


# Module-level singleton
_user_manager: Optional[UserManager] = None


def get_user_manager() -> UserManager:
    """Get or create the singleton UserManager instance."""
    global _user_manager
    if _user_manager is None:
        _user_manager = UserManager()
    return _user_manager
