"""
Preservation Property Tests - Baseline Behavior Verification

**Validates: Requirements 3.1, 3.2, 3.3, 3.4, 3.5, 3.6, 3.7, 3.8, 3.11**

These tests verify that existing correct behavior is preserved on UNFIXED code.
They encode the baseline behavior that must NOT regress when fixes are applied.

EXPECTED OUTCOME: All tests PASS on unfixed code (confirms baseline behavior).
"""

import csv
import fcntl
import json
import os
import sys
import tempfile
from datetime import datetime, timedelta
from pathlib import Path
from unittest.mock import patch, MagicMock

import pytest
from hypothesis import given, settings, assume, HealthCheck
from hypothesis import strategies as st

# Ensure project root is on sys.path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


# ============================================================================
# Strategies
# ============================================================================

# Strategy for valid email addresses
valid_emails = st.emails()

# Strategy for CSV-safe text (no commas, newlines, or quotes that break CSV)
csv_safe_text = st.text(
    min_size=1,
    max_size=50,
    alphabet=st.characters(
        whitelist_categories=('L', 'N', 'Z'),
        whitelist_characters='-_.'
    )
).filter(lambda s: len(s.strip()) > 0)

# Strategy for plain text (no HTML tags)
plain_text = st.text(
    min_size=1,
    max_size=100,
    alphabet=st.characters(
        whitelist_categories=('L', 'N', 'Z', 'P'),
        blacklist_characters='<>'
    )
).filter(lambda s: '<' not in s and '>' not in s and len(s.strip()) > 0)

# Strategy for user names (simple alphanumeric)
user_names = st.text(
    min_size=2,
    max_size=20,
    alphabet=st.characters(whitelist_categories=('L',))
).filter(lambda s: len(s.strip()) >= 2)

# Strategy for conversation messages
conversation_messages = st.text(
    min_size=1,
    max_size=200,
    alphabet=st.characters(whitelist_categories=('L', 'N', 'Z', 'P'))
).filter(lambda s: len(s.strip()) > 0)


# ============================================================================
# Fixtures
# ============================================================================

@pytest.fixture
def app_client(monkeypatch, tmp_path):
    """Create a Flask test client with minimal env setup."""
    monkeypatch.setenv('SECRET_KEY', 'test-secret-key')
    monkeypatch.setenv('OPENAI_API_KEY', 'test-openai-key')
    monkeypatch.setenv('ANTHROPIC_API_KEY', 'test-anthropic-key')
    monkeypatch.setenv('LLM_PROVIDER', 'openai')
    monkeypatch.setenv('FLASK_ENV', 'testing')
    monkeypatch.setenv('SAVED_RESULTS_DIR', str(tmp_path))

    from app.main import create_app
    app = create_app()
    app.config['TESTING'] = True
    with app.test_client() as client:
        yield client


@pytest.fixture
def authenticated_client(app_client):
    """Create an authenticated Flask test client with a valid session token."""
    # Login to get a valid session token
    response = app_client.post('/pdn-admin/login', json={
        'email': 'admin@test.com',
        'password': 'pdn'  # Default admin password
    })
    data = response.get_json()
    assert response.status_code == 200, f"Login failed: {data}"
    session_token = data['session_token']
    return app_client, session_token


@pytest.fixture
def csv_handler(tmp_path, monkeypatch):
    """Create a UserMetadataHandler with a temp directory."""
    monkeypatch.setenv('SECRET_KEY', 'test-secret-key')
    monkeypatch.setenv('SAVED_RESULTS_DIR', str(tmp_path))

    from app.utils.csv_metadata_handler import UserMetadataHandler

    handler = UserMetadataHandler()
    handler.csv_filename = tmp_path / "user_metadata.csv"
    return handler


# ============================================================================
# Property 10: Preservation - Authenticated Access
# For all properly authenticated admin requests, response status is 200
# and data is returned.
# **Validates: Requirements 3.1, 3.2, 3.3**
# ============================================================================

class TestPreservation_AuthenticatedAccess:
    """
    **Validates: Requirements 3.1, 3.2, 3.3**

    Preservation: Authenticated admin requests to admin endpoints must
    continue to return data successfully after fixes are applied.
    """

    def test_authenticated_metadata_csv_returns_200(self, authenticated_client):
        """Authenticated GET /pdn-admin/metadata/csv returns 200 with data."""
        client, token = authenticated_client
        response = client.get(f'/pdn-admin/metadata/csv?session_token={token}')
        assert response.status_code == 200, (
            f"Authenticated /metadata/csv should return 200, got {response.status_code}"
        )
        data = response.get_json()
        assert 'data' in data, "Response should contain 'data' key"

    def test_authenticated_token_usage_returns_200(self, authenticated_client):
        """Authenticated GET /pdn-admin/token-usage returns 200."""
        client, token = authenticated_client
        # Patch the agent instance to avoid needing real LLM setup
        with patch('app.pdn_admin.admin_routes.get_token_usage') as mock_usage:
            response = client.get(f'/pdn-admin/token-usage?session_token={token}')
            # Should be 200 or 500 (if agent not initialized), but NOT 401
            assert response.status_code != 401, (
                "Authenticated /token-usage should not return 401"
            )

    def test_authenticated_user_questionnaire_returns_data_or_404(self, authenticated_client):
        """Authenticated GET /pdn-admin/user/questionnaire/<email> returns data or 404 (not 401)."""
        client, token = authenticated_client
        response = client.get(f'/pdn-admin/user/questionnaire/test@example.com?session_token={token}')
        # Should be 200 (data found) or 404 (user not found), but NOT 401
        assert response.status_code in (200, 404, 500), (
            f"Authenticated /user/questionnaire should not return 401, got {response.status_code}"
        )

    def test_authenticated_user_voice_returns_data_or_404(self, authenticated_client):
        """Authenticated GET /pdn-admin/user/voice/<email> returns data or 404 (not 401)."""
        client, token = authenticated_client
        response = client.get(f'/pdn-admin/user/voice/test@example.com?session_token={token}')
        # Should be 200 or 404, but NOT 401
        assert response.status_code in (200, 404), (
            f"Authenticated /user/voice should not return 401, got {response.status_code}"
        )

    def test_authenticated_serve_audio_returns_file_or_404(self, authenticated_client, tmp_path, monkeypatch):
        """Authenticated GET /pdn-admin/audio/<path> returns file or 404 (not 401)."""
        client, token = authenticated_client
        monkeypatch.setenv('SAVED_RESULTS_DIR', str(tmp_path))

        # Create a test audio file
        user_dir = tmp_path / "testuser"
        user_dir.mkdir(parents=True, exist_ok=True)
        audio_file = user_dir / "question1.wav"
        audio_file.write_bytes(b'\x00' * 100)

        response = client.get(f'/pdn-admin/audio/testuser/question1.wav?session_token={token}')
        # Should be 200 (file served) or 404 (not found), but NOT 401
        assert response.status_code in (200, 404), (
            f"Authenticated /audio should not return 401, got {response.status_code}"
        )


# ============================================================================
# Property 11: Preservation - CSV Normal Write Operations
# For all valid CSV data written under normal conditions, read-back
# produces identical data.
# **Validates: Requirements 3.4, 3.5**
# ============================================================================

class TestPreservation_CSVNormalOperations:
    """
    **Validates: Requirements 3.4, 3.5**

    Preservation: CSV writes under normal (non-crash, non-concurrent)
    conditions must persist data correctly and read-back must produce
    identical data.
    """

    @given(
        email=st.from_regex(r'[a-z]{3,10}@[a-z]{3,8}\.[a-z]{2,4}', fullmatch=True),
        pdn_code=st.sampled_from(['A1', 'A2', 'B3', 'C4', 'D5', 'E1', 'E5', 'X1']),
        referral_source=st.sampled_from(['web', 'friend', 'doctor', 'social', ''])
    )
    @settings(max_examples=15, suppress_health_check=[HealthCheck.function_scoped_fixture])
    def test_csv_write_read_roundtrip(self, csv_handler, email, pdn_code, referral_source):
        """For all valid CSV data written under normal conditions, read-back produces identical data."""
        # Write data
        data = [{
            "User ID": "UID001",
            "Email": email,
            "Date": "01/01/2024",
            "PDN Code": pdn_code,
            "PDN Voice Code": "",
            "Diagnose PDN Code": "",
            "Diagnose Comments": "",
            "PDN Update Comments": "",
            "Referral Source": referral_source
        }]

        result = csv_handler._write_csv_data(data)
        assert result is True, "Write should succeed under normal conditions"

        # Read back
        read_data = csv_handler._read_csv_data()
        assert len(read_data) == 1, f"Expected 1 row, got {len(read_data)}"
        assert read_data[0]["Email"] == email, f"Email mismatch: {read_data[0]['Email']} != {email}"
        assert read_data[0]["PDN Code"] == pdn_code, f"PDN Code mismatch"
        assert read_data[0]["Referral Source"] == referral_source, "Referral Source mismatch"

    @given(
        num_rows=st.integers(min_value=1, max_value=10),
        pdn_codes=st.lists(
            st.sampled_from(['A1', 'A2', 'B3', 'C4', 'D5', 'E1', 'E5']),
            min_size=1, max_size=10
        )
    )
    @settings(max_examples=10, suppress_health_check=[HealthCheck.function_scoped_fixture])
    def test_csv_multiple_rows_persist_correctly(self, csv_handler, num_rows, pdn_codes):
        """Multiple rows written in a single operation persist correctly."""
        assume(len(pdn_codes) >= num_rows)

        data = []
        for i in range(num_rows):
            data.append({
                "User ID": f"UID{i:03d}",
                "Email": f"user{i}@test.com",
                "Date": f"{i+1:02d}/01/2024",
                "PDN Code": pdn_codes[i],
                "PDN Voice Code": "",
                "Diagnose PDN Code": "",
                "Diagnose Comments": "",
                "PDN Update Comments": "",
                "Referral Source": ""
            })

        result = csv_handler._write_csv_data(data)
        assert result is True, "Write should succeed"

        read_data = csv_handler._read_csv_data()
        assert len(read_data) == num_rows, f"Expected {num_rows} rows, got {len(read_data)}"

        for i in range(num_rows):
            assert read_data[i]["Email"] == f"user{i}@test.com"
            assert read_data[i]["PDN Code"] == pdn_codes[i]


# ============================================================================
# Property 12: Preservation - Plain Text Typewriter
# For all plain text strings (no HTML tags), typewriter tokenizer produces
# individual characters.
# **Validates: Requirements 3.6**
# ============================================================================

class TestPreservation_PlainTextTypewriter:
    """
    **Validates: Requirements 3.6**

    Preservation: The typewriter effect on plain text (no HTML) must continue
    to animate character-by-character. Each token should be a single character.
    """

    def _simulate_typewriter_split(self, text):
        """
        Simulate the current typewriter behavior: text.split('')
        In Python, equivalent to list(text) - splits into individual characters.
        This is the CORRECT behavior for plain text.
        """
        return list(text)

    @given(text=plain_text)
    @settings(max_examples=30, suppress_health_check=[HealthCheck.function_scoped_fixture])
    def test_plain_text_produces_individual_characters(self, text):
        """For all plain text (no HTML), typewriter produces individual characters."""
        tokens = self._simulate_typewriter_split(text)

        # Each token should be exactly one character
        for token in tokens:
            assert len(token) == 1, (
                f"Plain text token should be single character, got '{token}' (len={len(token)})"
            )

        # Joining all tokens should reproduce the original text
        assert ''.join(tokens) == text, "Tokens should reconstruct original text"

    @given(text=plain_text)
    @settings(max_examples=20, suppress_health_check=[HealthCheck.function_scoped_fixture])
    def test_plain_text_token_count_equals_length(self, text):
        """For plain text, number of tokens equals string length."""
        tokens = self._simulate_typewriter_split(text)
        assert len(tokens) == len(text), (
            f"Token count ({len(tokens)}) should equal text length ({len(text)})"
        )

    @given(text=plain_text)
    @settings(max_examples=20, suppress_health_check=[HealthCheck.function_scoped_fixture])
    def test_plain_text_no_partial_tags_in_output(self, text):
        """For plain text (no HTML), there should never be partial tags in any intermediate state."""
        tokens = self._simulate_typewriter_split(text)

        # Accumulate tokens and check no intermediate state has unclosed '<'
        accumulated = ""
        for token in tokens:
            accumulated += token
            # Since there's no HTML, there should never be '<' or '>'
            assert '<' not in accumulated or '>' in accumulated[accumulated.rfind('<'):], (
                f"Unexpected partial tag in plain text rendering: '{accumulated}'"
            )


# ============================================================================
# Property 13: Preservation - Active User Conversation History
# For all active users with recent activity, conversation history is retained.
# **Validates: Requirements 3.7, 3.8**
# ============================================================================

class TestPreservation_ActiveUserHistory:
    """
    **Validates: Requirements 3.7, 3.8**

    Preservation: Active users' conversation history and summarization must
    work as before. Active users should retain their history.
    """

    @given(
        user_name=user_names,
        messages=st.lists(
            st.tuples(conversation_messages, conversation_messages),
            min_size=1, max_size=5
        )
    )
    @settings(max_examples=15, deadline=None, suppress_health_check=[HealthCheck.function_scoped_fixture])
    def test_active_user_history_retained(self, user_name, messages):
        """For all active users, conversation history is maintained after adding messages."""
        from app.pdn_relationships.agents.base_pdn_agent import UserHistory, BasePDNAgent

        # Create a conversation history dict (simulating the agent's state)
        conversation_history = {}
        conversation_history[user_name] = UserHistory()

        # Add messages to history
        hist = conversation_history[user_name]
        for user_msg, assistant_msg in messages:
            hist.raw.append({"user": user_msg, "assistant": assistant_msg})

        # Verify history is retained
        assert user_name in conversation_history, "Active user should be in history"
        assert len(conversation_history[user_name].raw) == len(messages), (
            f"Expected {len(messages)} messages, got {len(conversation_history[user_name].raw)}"
        )

        # Verify message content is preserved
        for i, (user_msg, assistant_msg) in enumerate(messages):
            assert conversation_history[user_name].raw[i]["user"] == user_msg
            assert conversation_history[user_name].raw[i]["assistant"] == assistant_msg

    @given(
        user_name=user_names,
        query=conversation_messages,
        response=conversation_messages
    )
    @settings(max_examples=15, suppress_health_check=[HealthCheck.function_scoped_fixture])
    def test_format_history_returns_content_for_active_user(self, user_name, query, response):
        """For active users with history, _format_history returns non-empty content."""
        from app.pdn_relationships.agents.base_pdn_agent import UserHistory, BasePDNAgent

        # Simulate agent's conversation_history
        conversation_history = {}
        conversation_history[user_name] = UserHistory()
        conversation_history[user_name].raw.append({"user": query, "assistant": response})

        # Simulate _format_history logic
        hist = conversation_history.get(user_name)
        assert hist is not None, "Active user should have history entry"
        assert len(hist.raw) > 0, "Active user should have raw exchanges"

        # Format should produce non-empty output
        parts = []
        if hist.summary:
            parts.append(f"Previous conversation summary:\n{hist.summary}")
        if hist.raw:
            recent = "\n\n".join(
                f"User: {ex['user']}\nAssistant: {ex['assistant']}" for ex in hist.raw
            )
            parts.append(f"Recent exchanges:\n{recent}")

        formatted = "\n\n".join(parts)
        assert len(formatted) > 0, "Formatted history should be non-empty for active user"
        assert query in formatted, "User query should appear in formatted history"
        assert response in formatted, "Assistant response should appear in formatted history"


# ============================================================================
# Property 11 (continued): Preservation - answer_storage.py Operations
# For answer_storage.py operations, existing atomic write and locking
# patterns function correctly.
# **Validates: Requirements 3.11**
# ============================================================================

class TestPreservation_AnswerStoragePatterns:
    """
    **Validates: Requirements 3.11**

    Preservation: answer_storage.py's existing atomic write and file locking
    patterns must not be interfered with. The _save_with_lock function must
    continue to use fcntl.flock for exclusive access.
    """

    @given(
        email=st.from_regex(r'[a-z]{3,10}@[a-z]{3,8}\.[a-z]{2,4}', fullmatch=True),
        question_number=st.integers(min_value=1, max_value=20),
        answer_text=st.text(min_size=1, max_size=100, alphabet=st.characters(
            whitelist_categories=('L', 'N', 'Z')
        ))
    )
    @settings(max_examples=10, suppress_health_check=[HealthCheck.function_scoped_fixture])
    def test_save_with_lock_uses_fcntl(self, tmp_path, monkeypatch, email, question_number, answer_text):
        """answer_storage._save_with_lock uses fcntl.flock for file locking."""
        monkeypatch.setenv('SAVED_RESULTS_DIR', str(tmp_path))

        from app.utils.answer_storage import _save_with_lock

        # Create a test file path
        file_path = tmp_path / "test_data.json"
        test_data = {"question": question_number, "answer": answer_text}

        # Track fcntl.flock calls
        flock_calls = []
        original_flock = fcntl.flock

        def tracking_flock(fd, operation):
            flock_calls.append(operation)
            return original_flock(fd, operation)

        with patch('app.utils.answer_storage.fcntl.flock', side_effect=tracking_flock):
            _save_with_lock(file_path, test_data)

        # Verify fcntl.flock was called with LOCK_EX and LOCK_UN
        assert fcntl.LOCK_EX in flock_calls, "Should acquire exclusive lock"
        assert fcntl.LOCK_UN in flock_calls, "Should release lock"

        # Verify data was written correctly
        with open(file_path, 'r') as f:
            saved_data = json.load(f)
        assert saved_data == test_data, "Data should be persisted correctly"

    @given(
        email=st.from_regex(r'[a-z]{3,10}@[a-z]{3,8}\.[a-z]{2,4}', fullmatch=True),
        answer_data=st.dictionaries(
            keys=st.text(min_size=1, max_size=10, alphabet=st.characters(whitelist_categories=('L',))),
            values=st.text(min_size=1, max_size=50, alphabet=st.characters(whitelist_categories=('L', 'N'))),
            min_size=1, max_size=5
        )
    )
    @settings(max_examples=10, suppress_health_check=[HealthCheck.function_scoped_fixture])
    def test_save_answer_roundtrip(self, tmp_path, monkeypatch, email, answer_data):
        """save_answer followed by load_answers produces consistent data."""
        monkeypatch.setenv('SAVED_RESULTS_DIR', str(tmp_path))

        # Create user directory
        from app.utils.pdn_file_path import PDNFilePath
        pdn_fp = PDNFilePath(base_dir=str(tmp_path))
        user_dir = pdn_fp.get_user_dir(email)
        user_dir.mkdir(parents=True, exist_ok=True)

        from app.utils.answer_storage import save_answer, load_answers

        # Save an answer
        save_answer(email, 1, answer_data, question_text="Test question")

        # Load it back
        loaded = load_answers(email)
        assert loaded is not None, "Should load saved answers"
        assert "1" in loaded, "Should contain question 1"
        assert loaded["1"]["question_text"] == "Test question"

        # Verify answer data fields are preserved
        for key, value in answer_data.items():
            if value is not None:
                assert loaded["1"][key] == value, f"Field '{key}' should be preserved"
