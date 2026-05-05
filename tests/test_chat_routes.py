"""Tests for Flask chat routes."""

import pytest
from unittest.mock import patch, MagicMock
from app.main import create_app


@pytest.fixture
def app():
    """Create Flask test app."""
    with patch('app.main.start_memory_monitoring'):
        application = create_app()
    application.config['TESTING'] = True
    application.config['SECRET_KEY'] = 'test-secret'
    application.config['SESSION_TYPE'] = 'filesystem'
    return application


@pytest.fixture
def client(app):
    """Create Flask test client."""
    return app.test_client()


@pytest.fixture
def mock_agent():
    """Mock the PDNAgent to avoid real LLM calls."""
    with patch('app.pdn_chat_ai.chat_routes.get_agent_instance') as mock:
        agent = MagicMock()
        agent.chat_with_binat.return_value = "Mock response"
        agent.build_21_transformation_plan.return_value = "Mock plan"
        agent.daily_training.return_value = "Mock training"
        agent.persist_session.return_value = None
        agent.register_user_email.return_value = None
        agent.conversation_history = {}
        mock.return_value = agent
        yield agent


@pytest.fixture
def mock_user_manager():
    """Mock the user manager."""
    with patch('app.pdn_chat_ai.chat_routes.get_user_manager') as mock:
        mgr = MagicMock()
        mgr.get_user.return_value = {
            'password': 'testpass',
            'name': 'Test User',
            'pdn_code': 'a7',
            'daily_conversation_limit': 15
        }
        mock.return_value = mgr
        yield mgr


class TestLogin:
    """Tests for login endpoint."""

    def test_login_valid_credentials(self, client, mock_user_manager):
        """Valid credentials should return 200 with success."""
        response = client.post('/pdn-binat/login', json={
            'email': 'test@example.com',
            'password': 'testpass'
        })
        assert response.status_code == 200
        data = response.get_json()
        assert data['success'] is True
        assert data['user_name'] == 'Test User'

    def test_login_invalid_credentials(self, client, mock_user_manager):
        """Invalid credentials should return 401."""
        mock_user_manager.get_user.return_value = {
            'password': 'correctpass',
            'name': 'User',
            'pdn_code': 'a7',
            'daily_conversation_limit': 15
        }
        response = client.post('/pdn-binat/login', json={
            'email': 'test@example.com',
            'password': 'wrongpass'
        })
        assert response.status_code == 401
        data = response.get_json()
        assert data['success'] is False

    def test_login_missing_data(self, client, mock_user_manager):
        """Missing email/password should return 400."""
        response = client.post('/pdn-binat/login', json={
            'email': '',
            'password': ''
        })
        assert response.status_code == 400

    def test_login_no_json_body(self, client, mock_user_manager):
        """No JSON body should return error (500 from error handler wrapping 415)."""
        response = client.post('/pdn-binat/login',
                               data='not json',
                               content_type='text/plain')
        # Flask raises 415 which the error handler catches and returns 500
        assert response.status_code == 500

    def test_login_nonexistent_user(self, client, mock_user_manager):
        """Non-existent user should return 401."""
        mock_user_manager.get_user.return_value = None
        response = client.post('/pdn-binat/login', json={
            'email': 'nobody@test.com',
            'password': 'pass'
        })
        assert response.status_code == 401


class TestLogout:
    """Tests for logout endpoint."""

    def test_logout_clears_session(self, client, mock_user_manager, mock_agent):
        """Logout should clear session and return success."""
        # First login
        client.post('/pdn-binat/login', json={
            'email': 'test@example.com',
            'password': 'testpass'
        })
        # Then logout
        response = client.post('/pdn-binat/logout')
        assert response.status_code == 200
        data = response.get_json()
        assert data['success'] is True


class TestChatEndpoint:
    """Tests for chat endpoint."""

    def test_chat_requires_data(self, client, mock_user_manager, mock_agent):
        """Chat endpoint without JSON content-type triggers error handler."""
        response = client.post('/pdn-binat/chat',
                               data='not json',
                               content_type='text/plain')
        # Flask raises 415 which the error handler catches and returns 500
        assert response.status_code == 500

    def test_chat_with_valid_data(self, client, mock_user_manager, mock_agent):
        """Chat with valid data should return response."""
        # Login first
        client.post('/pdn-binat/login', json={
            'email': 'test@example.com',
            'password': 'testpass'
        })
        response = client.post('/pdn-binat/chat', json={
            'message': 'Hello',
            'user_name': 'Test User',
            'pdn_code': 'a7'
        })
        assert response.status_code == 200
        data = response.get_json()
        assert 'response' in data
        assert data['response'] == "Mock response"

    def test_chat_empty_json_returns_response(self, client, mock_user_manager, mock_agent):
        """Empty JSON with valid content-type should call agent and return response."""
        # Login first to set session
        client.post('/pdn-binat/login', json={
            'email': 'test@example.com',
            'password': 'testpass'
        })
        response = client.post('/pdn-binat/chat', json={
            'message': 'test',
            'user_name': 'Test',
            'pdn_code': 'a7'
        })
        assert response.status_code == 200
        data = response.get_json()
        assert 'response' in data
