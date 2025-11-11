"""Conversation statistics tracking utility."""

import json
import logging
from datetime import datetime, timedelta
from collections import defaultdict
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

        self.stats = defaultdict(lambda: defaultdict(int))
        self._lock = threading.Lock()
        self._dirty = False
        self._load_stats()
    
    def _load_stats(self):
        """Load stats from file."""
        if not self.stats_file.exists():
            return
        try:
            with open(self.stats_file, 'r') as f:
                data = json.load(f)
            self.stats = defaultdict(lambda: defaultdict(int), 
                                    {date: defaultdict(int, users) for date, users in data.items()})
            logger.info(f"Loaded conversation stats from {self.stats_file}")
        except Exception as e:
            logger.error(f"Failed to load conversation stats: {e}")
    
    def _save_stats(self):
        """Save stats to file."""
        if not self._dirty:
            return
        try:
            self.stats_file.parent.mkdir(parents=True, exist_ok=True)
            with open(self.stats_file, 'w') as f:
                json.dump({date: dict(users) for date, users in self.stats.items()}, f, indent=2)
            self._dirty = False
            logger.debug(f"Saved conversation stats to {self.stats_file}")
        except Exception as e:
            logger.error(f"Failed to save conversation stats: {e}")
    
    def increment_conversation(self, email: str):
        """Increment conversation count for user today."""
        today = datetime.now().strftime('%Y-%m-%d')
        with self._lock:
            self.stats[today][email] += 1
            self._dirty = True
            self._save_stats()
    
    def get_user_stats(self, email: str, days: int = 7) -> dict:
        """Get conversation stats for user over specified days."""
        today = datetime.now().date()
        stats = {}
        for i in range(days):
            date_str = (today - timedelta(days=i)).strftime('%Y-%m-%d')
            stats[date_str] = self.stats[date_str].get(email, 0)
        return stats
    
    def get_all_stats(self, days: int = 7) -> dict:
        """Get all user stats over specified days."""
        today = datetime.now().date()
        all_stats = {}
        for i in range(days):
            date_str = (today - timedelta(days=i)).strftime('%Y-%m-%d')
            all_stats[date_str] = dict(self.stats[date_str])
        return all_stats

# Global instance
conversation_stats = ConversationStats()