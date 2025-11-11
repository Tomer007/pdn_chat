"""Conversation statistics tracking utility."""

import json
import logging
from datetime import datetime, timedelta
import threading

from app.utils.pdn_file_path import PDNFilePath

logger = logging.getLogger(__name__)

class ConversationStats:
    """Track daily conversation counts per user."""
    
    def __init__(self):
        pdn_file_path = PDNFilePath()
        user_dir = pdn_file_path.get_base_dir()
        self.stats_file = user_dir / "conversation_stats.json"
        logger.info("conversation stats file path: %s", self.stats_file)
        self._lock = threading.RLock()
    
    def _load_stats(self):
        """Load stats from file."""
        if not self.stats_file.exists():
            return {}
        try:
            with open(self.stats_file, 'r') as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"Failed to load conversation stats: {e}")
            return {}
    
    def _save_stats(self, stats):
        """Save stats to file."""
        try:
            self.stats_file.parent.mkdir(parents=True, exist_ok=True)
            with open(self.stats_file, 'w') as f:
                json.dump(stats, f, indent=2)
            logger.debug(f"Saved conversation stats to {self.stats_file}")
        except Exception as e:
            logger.error(f"Failed to save conversation stats: {e}")
    
    def increment_conversation(self, email: str):
        """Increment conversation count for user today."""
        today = datetime.now().strftime('%Y-%m-%d')
        with self._lock:
            stats = self._load_stats()
            if today not in stats:
                stats[today] = {}
            stats[today][email] = stats[today].get(email, 0) + 1
            self._save_stats(stats)
    
    def get_all_stats(self, days: int = 7) -> dict:
        """Get all user stats over specified days."""
        with self._lock:
            today = datetime.now().date()
            stats = self._load_stats()
            return {(today - timedelta(days=i)).strftime('%Y-%m-%d'): stats.get((today - timedelta(days=i)).strftime('%Y-%m-%d'), {}) for i in range(days)}

# Global instance
conversation_stats = ConversationStats()