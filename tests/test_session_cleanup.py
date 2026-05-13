"""
Tests for session file cleanup utility.

Validates: Requirements 2.9 (expired session files periodically removed from disk)
Preservation: 3.8 (active Flask sessions function correctly without premature cleanup)
"""

import os
import time
import tempfile
from pathlib import Path

import pytest

from app.utils.session_cleanup import SessionFileCleanup


@pytest.fixture
def session_dir(tmp_path):
    """Create a temporary session directory with test files."""
    return tmp_path / "flask_session"


@pytest.fixture
def cleanup(session_dir):
    """Create a SessionFileCleanup instance with short lifetime for testing."""
    session_dir.mkdir(parents=True, exist_ok=True)
    return SessionFileCleanup(
        session_dir=str(session_dir),
        session_lifetime_seconds=60,  # 1 minute for testing
        cleanup_interval_seconds=1,
    )


def _create_session_file(session_dir: Path, name: str, age_seconds: float) -> Path:
    """Create a session file with a specific age (mtime in the past)."""
    session_dir.mkdir(parents=True, exist_ok=True)
    filepath = session_dir / name
    filepath.write_text("session-data")
    # Set mtime to the past
    mtime = time.time() - age_seconds
    os.utime(filepath, (mtime, mtime))
    return filepath


class TestCleanupExpiredSessions:
    """Tests for cleanup_expired_sessions method."""

    def test_removes_expired_files(self, session_dir, cleanup):
        """Expired session files (mtime > lifetime) are removed."""
        # Create a file older than the 60s lifetime
        expired_file = _create_session_file(session_dir, "expired_session", age_seconds=120)

        removed = cleanup.cleanup_expired_sessions()

        assert removed == 1
        assert not expired_file.exists()

    def test_preserves_active_files(self, session_dir, cleanup):
        """Active session files (mtime < lifetime) are NOT removed."""
        # Create a recent file (10 seconds old, well within 60s lifetime)
        active_file = _create_session_file(session_dir, "active_session", age_seconds=10)

        removed = cleanup.cleanup_expired_sessions()

        assert removed == 0
        assert active_file.exists()

    def test_mixed_files_only_removes_expired(self, session_dir, cleanup):
        """Only expired files are removed; active files are preserved."""
        expired = _create_session_file(session_dir, "old_session", age_seconds=200)
        active = _create_session_file(session_dir, "new_session", age_seconds=5)

        removed = cleanup.cleanup_expired_sessions()

        assert removed == 1
        assert not expired.exists()
        assert active.exists()

    def test_empty_directory(self, session_dir, cleanup):
        """No error when session directory is empty."""
        session_dir.mkdir(parents=True, exist_ok=True)

        removed = cleanup.cleanup_expired_sessions()

        assert removed == 0

    def test_nonexistent_directory(self, tmp_path):
        """No error when session directory does not exist."""
        cleanup = SessionFileCleanup(
            session_dir=str(tmp_path / "nonexistent"),
            session_lifetime_seconds=60,
        )

        removed = cleanup.cleanup_expired_sessions()

        assert removed == 0

    def test_skips_subdirectories(self, session_dir, cleanup):
        """Subdirectories inside session dir are not removed."""
        session_dir.mkdir(parents=True, exist_ok=True)
        subdir = session_dir / "some_subdir"
        subdir.mkdir()

        removed = cleanup.cleanup_expired_sessions()

        assert removed == 0
        assert subdir.exists()

    def test_multiple_expired_files(self, session_dir, cleanup):
        """Multiple expired files are all removed."""
        files = []
        for i in range(5):
            f = _create_session_file(session_dir, f"session_{i}", age_seconds=120 + i * 10)
            files.append(f)

        removed = cleanup.cleanup_expired_sessions()

        assert removed == 5
        for f in files:
            assert not f.exists()


class TestBackgroundThread:
    """Tests for the background cleanup thread."""

    def test_start_and_stop(self, session_dir, cleanup):
        """Background thread starts and stops cleanly."""
        cleanup.start()
        assert cleanup._running is True
        assert cleanup._thread is not None
        assert cleanup._thread.is_alive()

        cleanup.stop()
        assert cleanup._running is False

    def test_start_runs_initial_cleanup(self, session_dir, cleanup):
        """Starting the cleanup runs an immediate cleanup pass."""
        expired = _create_session_file(session_dir, "expired", age_seconds=120)

        cleanup.start()
        # Give a moment for the initial cleanup to run
        time.sleep(0.1)

        assert not expired.exists()
        cleanup.stop()

    def test_start_is_idempotent(self, session_dir, cleanup):
        """Calling start() multiple times does not create multiple threads."""
        cleanup.start()
        thread1 = cleanup._thread

        cleanup.start()
        thread2 = cleanup._thread

        assert thread1 is thread2
        cleanup.stop()
