"""Tests for PDNAgent conversation history and summarization logic.

These tests expose the bug where summarization fires on every single turn
after the first summarization, instead of batching turns before summarizing.
"""

import pytest
from unittest.mock import patch, MagicMock
from app.pdn_chat_ai.binat_agents.pdn_agent import PDNAgent, UserHistory


@pytest.fixture
def agent():
    """Create a PDNAgent with mocked LLMs so no real API calls are made."""
    with patch("app.pdn_chat_ai.binat_agents.pdn_agent.ChatOpenAI") as mock_openai, \
         patch("app.pdn_chat_ai.binat_agents.pdn_agent.ChatAnthropic"), \
         patch("app.pdn_chat_ai.binat_agents.pdn_agent.Config") as mock_config:

        cfg = mock_config.return_value
        cfg.LLM_PROVIDER = "openai"
        cfg.OPENAI_API_KEY = "fake-key"
        cfg.OPENAI_MODEL = "gpt-4o-mini"
        cfg.ANTHROPIC_API_KEY = "fake-key"
        cfg.ANTHROPIC_MODEL = "claude-3"

        # Make the main LLM and summary LLM return predictable responses
        mock_llm_instance = MagicMock()
        mock_llm_instance.invoke.return_value = MagicMock(content="summary of old turns")
        mock_openai.return_value = mock_llm_instance

        agent = PDNAgent()
        # Override summary_llm to track calls
        agent.summary_llm = MagicMock()
        agent.summary_llm.invoke.return_value = MagicMock(content="summary of old turns")
        yield agent


class TestSummarizationTriggerFrequency:
    """Tests that verify when summarization fires relative to turn count."""

    def test_no_summarization_before_threshold(self, agent):
        """Summarization should NOT fire when turns < MAX_TURNS_BEFORE_SUMMARY."""
        user = "test_user"
        # Add 4 turns (below threshold of 5)
        for i in range(4):
            agent._add_to_history(user, f"question {i}", f"answer {i}")

        assert agent.summary_llm.invoke.call_count == 0
        assert len(agent.conversation_history[user].raw) == 4
        assert agent.conversation_history[user].summary == ""

    def test_no_summarization_at_exact_threshold(self, agent):
        """At exactly MAX_TURNS_BEFORE_SUMMARY (10) turns, _add_to_history
        triggers _summarize_old_turns which summarizes the 5 oldest turns
        and keeps the 5 most recent."""
        user = "test_user"
        for i in range(agent.MAX_TURNS_BEFORE_SUMMARY):
            agent._add_to_history(user, f"question {i}", f"answer {i}")

        # 10 turns: summarization fires, trimming to 5 raw + summary
        assert agent.summary_llm.invoke.call_count == 1
        assert len(agent.conversation_history[user].raw) == agent.RAW_TURNS_TO_KEEP

    def test_first_summarization_at_threshold_plus_one(self, agent):
        """At turn 11, summarization has already fired at turn 10.
        Turn 11 adds one more but doesn't re-trigger (6 raw < 10 threshold)."""
        user = "test_user"
        for i in range(agent.MAX_TURNS_BEFORE_SUMMARY + 1):
            agent._add_to_history(user, f"question {i}", f"answer {i}")

        # Only 1 summarization (at turn 10), turn 11 doesn't trigger again
        assert agent.summary_llm.invoke.call_count == 1
        assert len(agent.conversation_history[user].raw) == agent.RAW_TURNS_TO_KEEP + 1

    def test_summarization_should_not_fire_on_every_turn_after_first(self, agent):
        """BUG TEST: After first summarization, adding one more turn should NOT
        trigger another summarization. Currently it does because
        MAX_TURNS_BEFORE_SUMMARY == RAW_TURNS_TO_KEEP == 5.

        After the first summarization trims raw to 5, the 7th turn makes
        raw length 6, which is >= 5, so summarization fires again for just
        1 turn. This is wasteful and not the intended batching behavior.
        """
        user = "test_user"
        # Trigger first summarization at turn 6
        for i in range(agent.MAX_TURNS_BEFORE_SUMMARY + 1):
            agent._add_to_history(user, f"question {i}", f"answer {i}")

        assert agent.summary_llm.invoke.call_count == 1
        first_summary_call_count = agent.summary_llm.invoke.call_count

        # Add one more turn (turn 7) — this should NOT trigger summarization
        agent._add_to_history(user, "question extra", "answer extra")

        # BUG: This assertion will FAIL with current code because
        # summarization fires again (call_count becomes 2)
        assert agent.summary_llm.invoke.call_count == first_summary_call_count, \
            "Summarization fired again after just 1 new turn — should wait for a batch"

    def test_summarization_does_not_fire_every_turn_after_first(self, agent):
        """After the fix, summarization should NOT fire on every turn.
        With MAX_TURNS_BEFORE_SUMMARY=10 and RAW_TURNS_TO_KEEP=5,
        after the first summarization at turn 11, the next batch
        shouldn't trigger until turn 16."""
        user = "test_user"
        # Trigger first summarization at turn 11 (> 10 threshold)
        for i in range(agent.MAX_TURNS_BEFORE_SUMMARY + 1):
            agent._add_to_history(user, f"question {i}", f"answer {i}")

        first_count = agent.summary_llm.invoke.call_count
        assert first_count == 1

        # Add 3 more turns — none should trigger summarization
        for i in range(3):
            agent._add_to_history(user, f"extra question {i}", f"extra answer {i}")

        assert agent.summary_llm.invoke.call_count == 1, \
            "Summarization should not fire again until the next batch threshold"


class TestSummarizeOldTurns:
    """Tests for the _summarize_old_turns method."""

    def test_does_nothing_when_under_keep_limit(self, agent):
        """Should not summarize when raw turns <= RAW_TURNS_TO_KEEP."""
        user = "test_user"
        hist = agent.conversation_history[user]
        for i in range(agent.RAW_TURNS_TO_KEEP):
            hist.raw.append({"user": f"q{i}", "assistant": f"a{i}"})

        agent._summarize_old_turns(user)
        assert agent.summary_llm.invoke.call_count == 0

    def test_summarizes_only_oldest_turns(self, agent):
        """Should summarize old turns and keep only RAW_TURNS_TO_KEEP recent ones."""
        user = "test_user"
        hist = agent.conversation_history[user]
        for i in range(8):
            hist.raw.append({"user": f"q{i}", "assistant": f"a{i}"})

        agent._summarize_old_turns(user)

        assert len(hist.raw) == agent.RAW_TURNS_TO_KEEP
        # The kept turns should be the most recent ones
        assert hist.raw[0]["user"] == "q3"
        assert hist.raw[-1]["user"] == "q7"
        assert hist.summary == "summary of old turns"

    def test_appends_to_existing_summary(self, agent):
        """New summary should be appended to existing summary."""
        user = "test_user"
        hist = agent.conversation_history[user]
        hist.summary = "previous summary"
        for i in range(8):
            hist.raw.append({"user": f"q{i}", "assistant": f"a{i}"})

        agent._summarize_old_turns(user)

        assert "previous summary" in hist.summary
        assert "summary of old turns" in hist.summary


class TestFormatHistory:
    """Tests for the _format_history method."""

    def test_no_history_returns_default(self, agent):
        """Should return 'No previous conversation.' for unknown user."""
        result = agent._format_history("unknown_user")
        assert result == "No previous conversation."

    def test_only_raw_turns(self, agent):
        """Should format only recent exchanges when no summary exists."""
        user = "test_user"
        hist = agent.conversation_history[user]
        hist.raw.append({"user": "hello", "assistant": "hi there"})

        result = agent._format_history(user)
        assert "Recent exchanges:" in result
        assert "User: hello" in result
        assert "Previous conversation summary:" not in result

    def test_summary_and_raw(self, agent):
        """Should include both summary and recent exchanges."""
        user = "test_user"
        hist = agent.conversation_history[user]
        hist.summary = "User asked about PDN codes"
        hist.raw.append({"user": "what next?", "assistant": "try this"})

        result = agent._format_history(user)
        assert "Previous conversation summary:" in result
        assert "User asked about PDN codes" in result
        assert "Recent exchanges:" in result
        assert "User: what next?" in result

    def test_only_summary_no_raw(self, agent):
        """Should show summary even when raw is empty."""
        user = "test_user"
        hist = agent.conversation_history[user]
        hist.summary = "Old conversation summary"

        result = agent._format_history(user)
        assert "Previous conversation summary:" in result
        assert "Recent exchanges:" not in result


class TestTokenBasedSummarization:
    """Tests for token-limit triggered summarization."""

    def test_token_limit_triggers_summarization(self, agent):
        """Summarization should fire when token estimate exceeds MAX_CONTEXT_TOKENS,
        but only if raw turns > RAW_TURNS_TO_KEEP."""
        user = "test_user"
        # Create messages large enough to exceed 3500 tokens total
        # Need > 5 turns so _summarize_old_turns doesn't bail out
        big_msg = "x" * 3000  # ~750 tokens per field, ~1500 per turn

        # Add 6 turns with big messages — tokens will exceed 3500 and turns > 5
        for i in range(6):
            agent._add_to_history(user, big_msg, big_msg)

        # Should have triggered summarization (both turn and token limits exceeded)
        assert agent.summary_llm.invoke.call_count >= 1


class TestPromptCaching:
    """Tests for Anthropic prompt caching via cache_control on system messages."""

    def test_anthropic_system_message_has_cache_control(self):
        """When using Anthropic, _build_system_message should use content blocks
        with cache_control (not additional_kwargs) since langchain-anthropic
        only reads cache_control from content block dicts."""
        with patch("app.pdn_chat_ai.binat_agents.pdn_agent.ChatOpenAI"), \
             patch("app.pdn_chat_ai.binat_agents.pdn_agent.ChatAnthropic") as mock_anthropic, \
             patch("app.pdn_chat_ai.binat_agents.pdn_agent.Config") as mock_config:

            cfg = mock_config.return_value
            cfg.LLM_PROVIDER = "anthropic"
            cfg.OPENAI_API_KEY = "fake-key"
            cfg.OPENAI_MODEL = "gpt-4o-mini"
            cfg.ANTHROPIC_API_KEY = "fake-key"
            cfg.ANTHROPIC_MODEL = "claude-3-sonnet-20240229"

            mock_anthropic.return_value = MagicMock()
            agent = PDNAgent()

            msg = agent._build_system_message("You are a helpful assistant.")
            # Content should be a list with a single content block dict
            assert isinstance(msg.content, list)
            assert len(msg.content) == 1
            block = msg.content[0]
            assert block["type"] == "text"
            assert block["text"] == "You are a helpful assistant."
            assert block["cache_control"] == {"type": "ephemeral"}

    def test_openai_system_message_no_cache_control(self):
        """When using OpenAI, _build_system_message should NOT add cache_control."""
        with patch("app.pdn_chat_ai.binat_agents.pdn_agent.ChatOpenAI") as mock_openai, \
             patch("app.pdn_chat_ai.binat_agents.pdn_agent.ChatAnthropic"), \
             patch("app.pdn_chat_ai.binat_agents.pdn_agent.Config") as mock_config:

            cfg = mock_config.return_value
            cfg.LLM_PROVIDER = "openai"
            cfg.OPENAI_API_KEY = "fake-key"
            cfg.OPENAI_MODEL = "gpt-4o-mini"
            cfg.ANTHROPIC_API_KEY = "fake-key"
            cfg.ANTHROPIC_MODEL = "claude-3"

            mock_openai.return_value = MagicMock()
            agent = PDNAgent()

            msg = agent._build_system_message("You are a helpful assistant.")
            assert "cache_control" not in msg.additional_kwargs


class TestSummaryLLMProviderSelection:
    """Tests that the summary LLM always uses gpt-4o-mini regardless of main provider."""

    def test_anthropic_provider_uses_gpt4o_mini_for_summary(self):
        """Even when main provider is Anthropic, summary_llm should be gpt-4o-mini."""
        with patch("app.pdn_chat_ai.binat_agents.pdn_agent.ChatOpenAI") as mock_openai, \
             patch("app.pdn_chat_ai.binat_agents.pdn_agent.ChatAnthropic") as mock_anthropic, \
             patch("app.pdn_chat_ai.binat_agents.pdn_agent.Config") as mock_config:

            cfg = mock_config.return_value
            cfg.LLM_PROVIDER = "anthropic"
            cfg.OPENAI_API_KEY = "fake-key"
            cfg.OPENAI_MODEL = "gpt-4o-mini"
            cfg.ANTHROPIC_API_KEY = "fake-key"
            cfg.ANTHROPIC_MODEL = "claude-3-sonnet-20240229"

            mock_anthropic.return_value = MagicMock()
            mock_openai.return_value = MagicMock()
            agent = PDNAgent()

            # ChatOpenAI should be called with gpt-4o-mini for summary LLM
            mini_calls = [
                call for call in mock_openai.call_args_list
                if call.kwargs.get("model") == "gpt-4o-mini"
            ]
            assert len(mini_calls) == 1, "Expected ChatOpenAI to be called with gpt-4o-mini for summary LLM"

    def test_openai_provider_uses_gpt4o_mini_for_summary(self):
        """When main provider is OpenAI, summary_llm should be gpt-4o-mini."""
        with patch("app.pdn_chat_ai.binat_agents.pdn_agent.ChatOpenAI") as mock_openai, \
             patch("app.pdn_chat_ai.binat_agents.pdn_agent.ChatAnthropic"), \
             patch("app.pdn_chat_ai.binat_agents.pdn_agent.Config") as mock_config:

            cfg = mock_config.return_value
            cfg.LLM_PROVIDER = "openai"
            cfg.OPENAI_API_KEY = "fake-key"
            cfg.OPENAI_MODEL = "gpt-4o"
            cfg.ANTHROPIC_API_KEY = "fake-key"
            cfg.ANTHROPIC_MODEL = "claude-3"

            mock_openai.return_value = MagicMock()
            agent = PDNAgent()

            # ChatOpenAI should be called twice: once for main LLM, once for summary
            mini_calls = [
                call for call in mock_openai.call_args_list
                if call.kwargs.get("model") == "gpt-4o-mini"
            ]
            assert len(mini_calls) == 1, "Expected ChatOpenAI to be called with gpt-4o-mini for summary LLM"
