"""Tests for PDNAgent (mock LLM calls)."""

import pytest
from unittest.mock import patch, MagicMock, PropertyMock
from datetime import datetime, timedelta
from pathlib import Path

from app.pdn_chat_ai.binat_agents.pdn_agent import PDNAgent, UserHistory


@pytest.fixture
def mock_config():
    """Mock Config class."""
    config = MagicMock()
    config.LLM_PROVIDER = 'openai'
    config.OPENAI_API_KEY = 'test-key'
    config.ANTHROPIC_API_KEY = 'test-key'
    config.OPENAI_MODEL = 'gpt-4o-mini'
    config.ANTHROPIC_MODEL = 'claude-sonnet-4-20250514'
    return config


@pytest.fixture
def agent(tmp_path, monkeypatch, mock_config):
    """Create a PDNAgent with mocked LLM."""
    monkeypatch.setenv('SAVED_RESULTS_DIR', str(tmp_path))
    with patch('app.pdn_relationships.agents.base_pdn_agent.Config', return_value=mock_config):
        with patch('app.pdn_relationships.agents.base_pdn_agent.ChatOpenAI') as mock_openai:
            mock_llm = MagicMock()
            mock_openai.return_value = mock_llm
            ag = PDNAgent(llm_provider='openai', model_name='gpt-4o-mini')
            ag.llm = mock_llm
            ag.summary_llm = mock_llm
    return ag


class TestEstimateTokens:
    """Tests for _estimate_tokens()."""

    def test_returns_reasonable_estimate(self, agent):
        """Should estimate ~1 token per 3 chars."""
        text = "Hello world, this is a test message"
        result = agent._estimate_tokens(text)
        assert result == len(text) // 3

    def test_empty_string(self, agent):
        """Empty string should return 0."""
        assert agent._estimate_tokens("") == 0

    def test_hebrew_text(self, agent):
        """Hebrew text should also use char/3 estimate."""
        text = "שלום עולם"
        result = agent._estimate_tokens(text)
        assert result == len(text) // 3


class TestHasExceededDailyLimit:
    """Tests for _has_exceeded_daily_limit()."""

    def test_not_exceeded_initially(self, agent):
        """New user should not have exceeded limit."""
        assert agent._has_exceeded_daily_limit("TestUser") is False

    def test_exceeded_after_max(self, agent):
        """Should return True after reaching limit."""
        agent.user_conversations["TestUser"]['count'] = 15
        agent.user_conversations["TestUser"]['last_reset'] = datetime.now()
        assert agent._has_exceeded_daily_limit("TestUser") is True

    def test_custom_limit(self, agent):
        """Should respect custom limit parameter."""
        agent.user_conversations["TestUser"]['count'] = 5
        agent.user_conversations["TestUser"]['last_reset'] = datetime.now()
        assert agent._has_exceeded_daily_limit("TestUser", max_conversations_per_day=5) is True
        assert agent._has_exceeded_daily_limit("TestUser", max_conversations_per_day=10) is False

    def test_exempt_user_never_exceeded(self, agent):
        """Exempt users should never be limited."""
        exempt_name = 'פנינה'
        agent.user_conversations[exempt_name]['count'] = 1000
        agent.user_conversations[exempt_name]['last_reset'] = datetime.now()
        assert agent._has_exceeded_daily_limit(exempt_name) is False


class TestResetDailyCount:
    """Tests for _reset_daily_count()."""

    def test_resets_at_midnight(self, agent):
        """Should reset count when a new day starts."""
        yesterday = datetime.now() - timedelta(days=1)
        agent.user_conversations["TestUser"]['count'] = 10
        agent.user_conversations["TestUser"]['last_reset'] = yesterday
        agent._reset_daily_count("TestUser")
        assert agent.user_conversations["TestUser"]['count'] == 0

    def test_no_reset_same_day(self, agent):
        """Should not reset if still same day."""
        agent.user_conversations["TestUser"]['count'] = 5
        agent.user_conversations["TestUser"]['last_reset'] = datetime.now()
        agent._reset_daily_count("TestUser")
        assert agent.user_conversations["TestUser"]['count'] == 5


class TestAddToHistory:
    """Tests for _add_to_history()."""

    def test_appends_to_raw_list(self, agent):
        """Should append exchange to raw history."""
        agent._add_to_history("TestUser", "Hello", "Hi there")
        hist = agent.conversation_history["TestUser"]
        assert len(hist.raw) == 1
        assert hist.raw[0]['user'] == "Hello"
        assert hist.raw[0]['assistant'] == "Hi there"

    def test_multiple_additions(self, agent):
        """Multiple additions should accumulate."""
        agent._add_to_history("TestUser", "msg1", "resp1")
        agent._add_to_history("TestUser", "msg2", "resp2")
        hist = agent.conversation_history["TestUser"]
        assert len(hist.raw) == 2


class TestFormatHistory:
    """Tests for _format_history()."""

    def test_empty_history_returns_empty(self, agent):
        """No history should return empty string."""
        result = agent._format_history("NewUser")
        assert result == ""

    def test_with_summary_and_raw(self, agent):
        """Should include both summary and recent exchanges."""
        hist = agent.conversation_history["TestUser"]
        hist.summary = "Previous topics discussed"
        hist.raw = [{"user": "Hello", "assistant": "Hi"}]
        result = agent._format_history("TestUser")
        assert "Previous conversation summary:" in result
        assert "Previous topics discussed" in result
        assert "Recent exchanges:" in result
        assert "User: Hello" in result

    def test_with_only_raw(self, agent):
        """Should format raw exchanges without summary."""
        hist = agent.conversation_history["TestUser"]
        hist.raw = [{"user": "Q1", "assistant": "A1"}]
        result = agent._format_history("TestUser")
        assert "User: Q1" in result
        assert "Assistant: A1" in result


class TestClearUserHistory:
    """Tests for clear_user_history()."""

    def test_resets_history(self, agent):
        """Should reset user's history to empty."""
        agent.conversation_history["TestUser"].raw = [{"user": "x", "assistant": "y"}]
        agent.conversation_history["TestUser"].summary = "some summary"
        agent.clear_user_history("TestUser")
        hist = agent.conversation_history["TestUser"]
        assert hist.raw == []
        assert hist.summary == ""


class TestRegisterUserEmail:
    """Tests for register_user_email()."""

    def test_stores_mapping(self, agent):
        """Should store name-to-email mapping."""
        agent.register_user_email("תומר", "tomer@test.com")
        assert agent._user_email_map["תומר"] == "tomer@test.com"

    def test_empty_values_ignored(self, agent):
        """Empty name or email should not store."""
        agent.register_user_email("", "email@test.com")
        agent.register_user_email("Name", "")
        assert "" not in agent._user_email_map
        assert "Name" not in agent._user_email_map


class TestPersistSession:
    """Tests for persist_session()."""

    def test_saves_history_to_disk(self, agent):
        """Should persist summary to disk via history_service."""
        agent.conversation_history["TestUser"].summary = "Test summary"
        agent.conversation_history["TestUser"].raw = []
        with patch.object(agent.history_service, 'save_user_history', return_value=True) as mock_save:
            agent.persist_session("TestUser", "test@email.com")
            mock_save.assert_called_once()
            call_args = mock_save.call_args
            assert call_args[0][0] == "test@email.com"
            assert "Test summary" in call_args[0][1]

    def test_empty_user_does_nothing(self, agent):
        """Empty user_name should not persist."""
        with patch.object(agent.history_service, 'save_user_history') as mock_save:
            agent.persist_session("", "")
            mock_save.assert_not_called()

    def test_summarizes_raw_turns_on_persist(self, agent):
        """Should summarize remaining raw turns before persisting."""
        agent.conversation_history["TestUser"].raw = [
            {"user": "Hello", "assistant": "Hi there"}
        ]
        mock_response = MagicMock()
        mock_response.content = "Summarized content"
        agent.summary_llm.invoke = MagicMock(return_value=mock_response)
        with patch.object(agent.history_service, 'save_user_history', return_value=True):
            agent.persist_session("TestUser", "test@email.com")
        assert agent.conversation_history["TestUser"].summary == "Summarized content"
