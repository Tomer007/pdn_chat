"""
Session File Cleanup Utility

Periodically removes expired Flask filesystem session files from disk.
This prevents orphaned session files from accumulating indefinitely.
"""

import logging
import os
import threading
import time
from pathlib import Path
from typing import Optional

logger = logging.getLogger(__name__)


class SessionFileCleanup:
    """Periodically cleans up expired Flask filesystem session files."""

    def __init__(
        self,
        session_dir: str = "flask_session",
        session_lifetime_seconds: float = 7200,  # 2 hours default
        cleanup_interval_seconds: float = 3600,  # 1 hour default
    ):
        """
        Initialize session file cleanup.

        Args:
            session_dir: Path to the Flask session directory.
            session_lifetime_seconds: Maximum age (in seconds) before a session
                file is considered expired and eligible for removal.
            cleanup_interval_seconds: How often (in seconds) the background
                cleanup thread runs.
        """
        self.session_dir = Path(session_dir)
        self.session_lifetime_seconds = session_lifetime_seconds
        self.cleanup_interval_seconds = cleanup_interval_seconds
        self._running = False
        self._thread: Optional[threading.Thread] = None

    def cleanup_expired_sessions(self) -> int:
        """
        Scan the session directory and remove files older than the session lifetime.

        Only removes files whose mtime exceeds the session lifetime.
        Returns the number of files removed.
        """
        if not self.session_dir.exists():
            return 0

        removed = 0
        now = time.time()
        cutoff = now - self.session_lifetime_seconds

        try:
            for entry in self.session_dir.iterdir():
                if not entry.is_file():
                    continue
                try:
                    mtime = entry.stat().st_mtime
                    if mtime < cutoff:
                        entry.unlink()
                        removed += 1
                except OSError as e:
                    logger.warning(
                        "Failed to remove session file %s: %s", entry.name, e
                    )
        except OSError as e:
            logger.error("Error scanning session directory %s: %s", self.session_dir, e)

        if removed > 0:
            logger.info("Cleaned up %d expired session file(s)", removed)

        return removed

    def start(self) -> None:
        """Start the background cleanup thread."""
        if self._running:
            return

        # Run initial cleanup on startup
        self.cleanup_expired_sessions()

        self._running = True
        self._thread = threading.Thread(target=self._cleanup_loop, daemon=True)
        self._thread.start()
        logger.info(
            "Session file cleanup started (interval=%ds, lifetime=%ds)",
            self.cleanup_interval_seconds,
            self.session_lifetime_seconds,
        )

    def stop(self) -> None:
        """Stop the background cleanup thread."""
        self._running = False
        if self._thread:
            self._thread.join(timeout=5)
        logger.info("Session file cleanup stopped")

    def _cleanup_loop(self) -> None:
        """Background loop that periodically cleans expired session files."""
        while self._running:
            try:
                time.sleep(self.cleanup_interval_seconds)
                if self._running:
                    self.cleanup_expired_sessions()
            except Exception as e:
                logger.error("Error in session cleanup loop: %s", e)
                time.sleep(60)


# Module-level instance
_session_cleanup: Optional[SessionFileCleanup] = None


def start_session_cleanup(
    session_dir: str = "flask_session",
    session_lifetime_seconds: float = 7200,
    cleanup_interval_seconds: float = 3600,
) -> SessionFileCleanup:
    """
    Start the global session file cleanup background thread.

    Args:
        session_dir: Path to the Flask session directory.
        session_lifetime_seconds: Max age before a file is removed.
        cleanup_interval_seconds: How often cleanup runs.

    Returns:
        The SessionFileCleanup instance.
    """
    global _session_cleanup
    if _session_cleanup is None:
        _session_cleanup = SessionFileCleanup(
            session_dir=session_dir,
            session_lifetime_seconds=session_lifetime_seconds,
            cleanup_interval_seconds=cleanup_interval_seconds,
        )
    _session_cleanup.start()
    return _session_cleanup


def stop_session_cleanup() -> None:
    """Stop the global session file cleanup."""
    global _session_cleanup
    if _session_cleanup:
        _session_cleanup.stop()
