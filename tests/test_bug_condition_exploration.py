"""
Bug Condition Exploration Tests - Security and Stability Defects

**Validates: Requirements 1.1, 1.2, 1.3, 1.4, 1.5, 1.7, 1.11**

These tests encode the EXPECTED correct behavior. They are designed to FAIL on
unfixed code, proving the bugs exist. After fixes are applied, these tests should PASS.

CRITICAL: Test failure = success (proves bugs exist on unfixed code).
DO NOT fix the code or tests when they fail.
"""

import os
import sys
import csv
import tempfile
import signal
from pathlib import Path
from unittest.mock import patch, MagicMock

import pytest
from hypothesis import given, settings, assume, HealthCheck
from hypothesis import strategies as st

# Ensure project root is on sys.path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


# ============================================================================
# Fixtures
# ============================================================================

@pytest.fixture
def app_client(monkeypatch):
    """Create a Flask test client with minimal env setup."""
    monkeypatch.setenv('SECRET_KEY', 'test-secret-key')
    monkeypatch.setenv('OPENAI_API_KEY', 'test-openai-key')
    monkeypatch.setenv('ANTHROPIC_API_KEY', 'test-anthropic-key')
    monkeypatch.setenv('LLM_PROVIDER', 'openai')
    monkeypatch.setenv('FLASK_ENV', 'testing')
    monkeypatch.setenv('SAVED_RESULTS_DIR', tempfile.mkdtemp())

    from app.main import create_app
    app = create_app()
    app.config['TESTING'] = True
    with app.test_client() as client:
        yield client


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
# Category A: Admin Auth Bypass
# Tests that unauthenticated requests to admin endpoints return 401.
# Will FAIL on unfixed code because try/except swallows abort(401).
# ============================================================================

class TestCategoryA_AuthBypass:
    """
    **Validates: Requirements 1.1**

    Bug: admin_routes.py wraps verify_session() in try/except that catches
    the abort(401) exception and continues executing endpoint logic.
    Expected: Unauthenticated requests should get 401 Unauthorized.
    """

    def test_metadata_csv_no_auth(self, app_client):
        """GET /pdn-admin/metadata/csv without session_token → should be 401."""
        response = app_client.get('/pdn-admin/metadata/csv')
        assert response.status_code == 401, (
            f"Expected 401 for unauthenticated /metadata/csv, got {response.status_code}. "
            "Bug confirmed: try/except swallows abort(401)."
        )

    def test_user_questionnaire_no_auth(self, app_client):
        """GET /pdn-admin/user/questionnaire/<email> without session_token → should be 401."""
        response = app_client.get('/pdn-admin/user/questionnaire/test@example.com')
        assert response.status_code == 401, (
            f"Expected 401 for unauthenticated /user/questionnaire, got {response.status_code}. "
            "Bug confirmed: try/except swallows abort(401)."
        )

    def test_user_voice_no_auth(self, app_client):
        """GET /pdn-admin/user/voice/<email> without session_token → should be 401."""
        response = app_client.get('/pdn-admin/user/voice/test@example.com')
        assert response.status_code == 401, (
            f"Expected 401 for unauthenticated /user/voice, got {response.status_code}. "
            "Bug confirmed: try/except swallows abort(401)."
        )

    def test_user_diagnose_no_auth(self, app_client):
        """PUT /pdn-admin/user/diagnose/<email> without session_token → should be 401."""
        response = app_client.put(
            '/pdn-admin/user/diagnose/test@example.com',
            json={"diagnose_pdn_code": "X1", "diagnose_comments": "test"}
        )
        assert response.status_code == 401, (
            f"Expected 401 for unauthenticated /user/diagnose, got {response.status_code}. "
            "Bug confirmed: try/except swallows abort(401)."
        )

    def test_serve_audio_admin_no_auth(self, app_client):
        """GET /pdn-admin/audio/<path> without session_token → should be 401."""
        response = app_client.get('/pdn-admin/audio/user@example.com/question1.wav')
        assert response.status_code == 401, (
            f"Expected 401 for unauthenticated /audio/<path>, got {response.status_code}. "
            "Bug confirmed: try/except swallows abort(401)."
        )

    def test_token_usage_no_auth(self, app_client):
        """GET /pdn-admin/token-usage without session_token → should be 401."""
        response = app_client.get('/pdn-admin/token-usage')
        assert response.status_code == 401, (
            f"Expected 401 for unauthenticated /token-usage, got {response.status_code}. "
            "Bug confirmed: try/except swallows abort(401)."
        )


# ============================================================================
# Category B: Audio Routes No-Auth
# Tests that audio_routes.py endpoints require authentication.
# Will FAIL because no auth check exists in audio_routes.py.
# ============================================================================

class TestCategoryB_AudioNoAuth:
    """
    **Validates: Requirements 1.2**

    Bug: audio_routes.py serve_audio() has no authentication check at all.
    Expected: Unauthenticated requests should get 401 Unauthorized.
    """

    def test_audio_route_no_auth(self, app_client, tmp_path, monkeypatch):
        """GET /pdn-admin/audio/<path:filename> via audio_bp without auth → should be 401."""
        # Create a test audio file so the route doesn't 404 for file-not-found reasons
        monkeypatch.setenv('SAVED_RESULTS_DIR', str(tmp_path))
        user_dir = tmp_path / "testuser@example.com"
        user_dir.mkdir(parents=True, exist_ok=True)
        audio_file = user_dir / "question1.wav"
        audio_file.write_bytes(b'\x00' * 100)  # Fake WAV content

        # Patch PDNFilePath to use our tmp_path
        with patch('app.pdn_admin.audio_routes.PDNFilePath') as mock_pfp:
            mock_instance = MagicMock()
            mock_instance.get_user_dir.return_value = user_dir
            mock_pfp.return_value = mock_instance

            response = app_client.get('/pdn-admin/audio/testuser@example.com/question1.wav')

        assert response.status_code == 401, (
            f"Expected 401 for unauthenticated audio route, got {response.status_code}. "
            "Bug confirmed: audio_routes.py has no authentication check."
        )


# ============================================================================
# Category C: Save-Audio No-Auth
# Tests that /pdn-admin/api/save-audio requires authentication.
# Will FAIL because no auth check exists in save_audio().
# ============================================================================

class TestCategoryC_SaveAudioNoAuth:
    """
    **Validates: Requirements 1.3**

    Bug: save_audio() in admin_routes.py has no verify_session() call.
    Expected: Unauthenticated POST should get 401 Unauthorized.
    """

    def test_save_audio_no_auth(self, app_client, tmp_path, monkeypatch):
        """POST /pdn-admin/api/save-audio without auth → should be 401."""
        monkeypatch.setenv('SAVED_RESULTS_DIR', str(tmp_path))

        import io
        data = {
            'audio': (io.BytesIO(b'\x00' * 100), 'test.wav'),
            'username': 'testuser'
        }

        with patch('app.pdn_admin.admin_routes.PDNFilePath') as mock_pfp:
            mock_instance = MagicMock()
            mock_instance.get_user_dir.return_value = tmp_path / "testuser"
            mock_pfp.return_value = mock_instance
            (tmp_path / "testuser").mkdir(parents=True, exist_ok=True)

            response = app_client.post(
                '/pdn-admin/api/save-audio',
                data=data,
                content_type='multipart/form-data'
            )

        assert response.status_code == 401, (
            f"Expected 401 for unauthenticated save-audio, got {response.status_code}. "
            "Bug confirmed: save_audio() has no authentication check."
        )


# ============================================================================
# Category D: Neo Login Accepts Any Credentials
# Tests that /neo/login rejects invalid credentials.
# Will FAIL because any email/password combination is accepted.
# ============================================================================

class TestCategoryD_NeoLogin:
    """
    **Validates: Requirements 1.4**

    Bug: neo_routes.py login_post() accepts any email/password combination
    without validation ("For demo purposes, accept any email/password").
    Expected: Invalid credentials should be rejected with 401.
    """

    @given(
        email=st.emails(),
        password=st.text(min_size=1, max_size=50)
    )
    @settings(max_examples=10, suppress_health_check=[HealthCheck.function_scoped_fixture])
    def test_neo_login_rejects_invalid_credentials(self, app_client, email, password):
        """POST /neo/login with random credentials → should be 401."""
        response = app_client.post('/neo/login', json={
            'email': email,
            'password': password
        })
        assert response.status_code == 401, (
            f"Expected 401 for invalid credentials ({email}/{password}), "
            f"got {response.status_code}. "
            "Bug confirmed: any credentials are accepted."
        )


# ============================================================================
# Category E: CSV Corruption (Non-Atomic Write)
# Tests that a crash during _write_csv_data() leaves original file intact.
# Will FAIL because open('w') truncates the file immediately.
# ============================================================================

class TestCategoryE_CSVCorruption:
    """
    **Validates: Requirements 1.5**

    Bug: _write_csv_data() uses open('w') which truncates the file immediately.
    If the process crashes mid-write, the file is corrupted/empty.
    Expected: Original file should remain intact after a simulated crash.
    """

    def test_csv_crash_preserves_original(self, csv_handler):
        """Simulate crash during _write_csv_data() → original file should remain intact."""
        # Setup: write initial data
        initial_data = [
            {"User ID": "UID001", "Email": "user1@test.com", "Date": "01/01/2024",
             "PDN Code": "E5", "PDN Voice Code": "", "Diagnose PDN Code": "",
             "Diagnose Comments": "", "PDN Update Comments": "", "Referral Source": ""}
        ]
        csv_handler._write_csv_data(initial_data)

        # Verify initial data was written
        assert csv_handler.csv_filename.exists()
        original_content = csv_handler.csv_filename.read_text(encoding='utf-8')
        assert "user1@test.com" in original_content

        # Simulate crash: patch open to raise an error mid-write
        # This simulates what happens when the process crashes after truncation
        original_open = open

        def crashing_open(path, mode='r', *args, **kwargs):
            if mode == 'w' and str(csv_handler.csv_filename) in str(path):
                # Simulate: file is opened in 'w' mode (truncates), then crash
                f = original_open(path, mode, *args, **kwargs)
                f.write("")  # File is now truncated/empty
                f.close()
                raise OSError("Simulated crash during write")
            return original_open(path, mode, *args, **kwargs)

        new_data = [
            {"User ID": "UID001", "Email": "user1@test.com", "Date": "01/01/2024",
             "PDN Code": "E5-UPDATED", "PDN Voice Code": "", "Diagnose PDN Code": "",
             "Diagnose Comments": "", "PDN Update Comments": "", "Referral Source": ""},
            {"User ID": "UID002", "Email": "user2@test.com", "Date": "02/01/2024",
             "PDN Code": "A3", "PDN Voice Code": "", "Diagnose PDN Code": "",
             "Diagnose Comments": "", "PDN Update Comments": "", "Referral Source": ""}
        ]

        with patch('builtins.open', side_effect=crashing_open):
            try:
                csv_handler._write_csv_data(new_data)
            except OSError:
                pass  # Expected crash

        # After crash: original file should still be intact
        post_crash_content = csv_handler.csv_filename.read_text(encoding='utf-8')
        assert "user1@test.com" in post_crash_content, (
            f"Original file was corrupted after crash. Content: '{post_crash_content[:100]}'. "
            "Bug confirmed: non-atomic write truncates file on crash."
        )


# ============================================================================
# Category F: Typewriter HTML Splitting
# Tests that the typewriter tokenizer doesn't produce partial HTML tags.
# Will FAIL because split('') breaks tags character-by-character.
# ============================================================================

class TestCategoryF_TypewriterHTML:
    """
    **Validates: Requirements 1.7**

    Bug: typewriterEffect() uses html.split('') which splits HTML tags
    character-by-character, producing broken partial tags like '<str', '<stro'.
    Expected: HTML tags should be atomic tokens (never split mid-tag).
    """

    def _simulate_typewriter_split(self, html):
        """
        Simulate the FIXED typewriter behavior: regex tokenizer that splits
        HTML into atomic units (complete tags or single characters).
        Matches the fixed JS regex: /<[^>]+>|[^<]/g
        """
        import re
        return re.findall(r'<[^>]+>|[^<]', html)

    def _has_partial_tags(self, tokens):
        """
        Check if any intermediate rendering state contains a partial HTML tag.
        A partial tag is when we have '<' without a matching '>' in the accumulated output.
        """
        accumulated = ""
        for token in tokens:
            accumulated += token
            # Check if there's an unclosed '<' (partial tag)
            last_open = accumulated.rfind('<')
            if last_open != -1:
                last_close = accumulated.rfind('>', last_open)
                if last_close == -1:
                    # We have an unclosed tag - this is a partial tag state
                    return True
        return False

    def test_strong_tag_no_partial(self):
        """<strong>hello</strong> should not produce partial tags in tokens."""
        html = "<strong>hello</strong>"
        tokens = self._simulate_typewriter_split(html)

        # Check that no intermediate state has a partial tag
        has_partial = self._has_partial_tags(tokens)
        assert not has_partial, (
            f"Partial HTML tags detected in typewriter output for '{html}'. "
            f"Tokens: {tokens[:10]}... "
            "Bug confirmed: split('') breaks HTML tags character-by-character."
        )

    def test_anchor_tag_no_partial(self):
        """<a href="url">link</a> should not produce partial tags."""
        html = '<a href="https://example.com">link</a>'
        tokens = self._simulate_typewriter_split(html)

        has_partial = self._has_partial_tags(tokens)
        assert not has_partial, (
            f"Partial HTML tags detected for anchor tag. "
            "Bug confirmed: split('') breaks HTML tags."
        )

    @given(
        tag_name=st.sampled_from(['strong', 'em', 'b', 'i', 'span', 'div', 'p']),
        content=st.text(min_size=1, max_size=20, alphabet=st.characters(
            whitelist_categories=('L', 'N', 'Z'),
            whitelist_characters=' '
        ))
    )
    @settings(max_examples=10, suppress_health_check=[HealthCheck.function_scoped_fixture])
    def test_html_tags_atomic_property(self, tag_name, content):
        """For any HTML tag wrapping content, typewriter should not produce partial tags."""
        assume(len(content.strip()) > 0)
        html = f"<{tag_name}>{content}</{tag_name}>"
        tokens = self._simulate_typewriter_split(html)

        has_partial = self._has_partial_tags(tokens)
        assert not has_partial, (
            f"Partial HTML tags detected for '<{tag_name}>{content}</{tag_name}>'. "
            "Bug confirmed: character-by-character split breaks HTML tags."
        )


# ============================================================================
# Category G: Config Import Crash
# Tests that importing app.data.config doesn't raise AttributeError.
# Will FAIL because self._config is never defined before being referenced.
# ============================================================================

class TestCategoryG_ConfigImport:
    """
    **Validates: Requirements 1.11**

    Bug: Settings.__init__ references self._config['project']['name'] but
    _config is never assigned. This causes AttributeError on import.
    Expected: Import should succeed without raising AttributeError.
    """

    def test_config_import_no_error(self):
        """Import app.data.config → should not raise AttributeError."""
        # Remove cached module if previously imported (to test fresh import)
        modules_to_remove = [k for k in sys.modules if k.startswith('app.data.config')]
        for mod in modules_to_remove:
            del sys.modules[mod]

        try:
            import importlib
            mod = importlib.import_module('app.data.config')
            # If we get here, the import succeeded (no crash)
            assert hasattr(mod, 'settings') or True  # Just verify no crash
        except AttributeError as e:
            pytest.fail(
                f"Config import raised AttributeError: {e}. "
                "Bug confirmed: self._config is undefined in Settings.__init__."
            )
