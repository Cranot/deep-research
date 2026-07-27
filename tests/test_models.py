"""
Tests for models.py - data models and parsing.
"""

from datetime import datetime

import pytest

from deep_research.models import (
    AgentConfig,
    AgentState,
    AgentStatus,
    ExplorationResult,
    ModelSpec,
    ProviderType,
    ResearchConfig,
)


class TestModelSpec:
    """Tests for ModelSpec parsing."""

    def test_parse_simple_model(self):
        """Parse a simple model name (defaults to Claude)."""
        spec = ModelSpec.parse("opus")
        assert spec.provider == ProviderType.CLAUDE
        assert spec.model == "opus"

    def test_parse_haiku(self):
        """Parse haiku model."""
        spec = ModelSpec.parse("haiku")
        assert spec.provider == ProviderType.CLAUDE
        assert spec.model == "haiku"

    def test_parse_sonnet(self):
        """Parse sonnet model."""
        spec = ModelSpec.parse("sonnet")
        assert spec.provider == ProviderType.CLAUDE
        assert spec.model == "sonnet"

    def test_parse_with_provider(self):
        """Parse model with explicit provider."""
        spec = ModelSpec.parse("gemini:flash")
        assert spec.provider == ProviderType.GEMINI
        assert spec.model == "flash"

    def test_parse_gemini_pro(self):
        """Parse Gemini Pro model."""
        spec = ModelSpec.parse("gemini:pro")
        assert spec.provider == ProviderType.GEMINI
        assert spec.model == "pro"

    def test_parse_openai(self):
        """Parse OpenAI model."""
        spec = ModelSpec.parse("openai:gpt5-mini")
        assert spec.provider == ProviderType.OPENAI
        assert spec.model == "gpt5-mini"

    def test_parse_openrouter(self):
        """Parse OpenRouter model."""
        spec = ModelSpec.parse("openrouter:grok")
        assert spec.provider == ProviderType.OPENROUTER
        assert spec.model == "grok"

    def test_parse_kimi(self):
        """Parse Kimi model."""
        spec = ModelSpec.parse("kimi:kimi")
        assert spec.provider == ProviderType.KIMI
        assert spec.model == "kimi"

    def test_parse_invalid_provider(self):
        """Invalid provider should raise ValueError."""
        with pytest.raises(ValueError):
            ModelSpec.parse("unknown:model")

    def test_str_representation(self):
        """String representation should be provider:model."""
        spec = ModelSpec(provider=ProviderType.GEMINI, model="flash")
        assert str(spec) == "gemini:flash"

    def test_parse_with_multiple_colons(self):
        """Model name with colons should be preserved."""
        spec = ModelSpec.parse("openai:gpt-4:latest")
        assert spec.provider == ProviderType.OPENAI
        assert spec.model == "gpt-4:latest"


class TestExplorationResult:
    """Tests for ExplorationResult parsing."""

    def test_parse_empty_output(self):
        """Empty output should return no questions."""
        result = ExplorationResult.from_output("")
        assert result.questions == []
        assert result.raw_output == ""

    def test_parse_single_question(self):
        """Parse a single Q: line."""
        output = "Q: What is the meaning of life?"
        result = ExplorationResult.from_output(output)
        assert len(result.questions) == 1
        assert result.questions[0].question == "What is the meaning of life?"

    def test_parse_multiple_questions(self):
        """Parse multiple Q: lines."""
        output = """Some preamble text
Q: First question?
Some explanation
Q: Second question?
Q: Third question?
Closing text"""
        result = ExplorationResult.from_output(output)
        assert len(result.questions) == 3
        assert result.questions[0].question == "First question?"
        assert result.questions[1].question == "Second question?"
        assert result.questions[2].question == "Third question?"

    def test_parse_with_whitespace(self):
        """Q: lines with extra whitespace should be trimmed."""
        output = "  Q:   Question with spaces?  "
        result = ExplorationResult.from_output(output)
        assert len(result.questions) == 1
        assert result.questions[0].question == "Question with spaces?"

    def test_parse_no_q_lines(self):
        """Output without Q: lines should return empty list."""
        output = "This is just regular text without any questions."
        result = ExplorationResult.from_output(output)
        assert result.questions == []
        assert result.raw_output == output

    def test_raw_output_preserved(self):
        """Raw output should be preserved."""
        output = "Q: Question?\nSome text"
        result = ExplorationResult.from_output(output)
        assert result.raw_output == output

    def test_parse_question_without_text(self):
        """Q: with no text should be skipped."""
        output = "Q: \nQ: Real question?"
        result = ExplorationResult.from_output(output)
        # Empty Q: lines should not create empty questions
        assert len(result.questions) >= 1
        # The real question should be captured
        assert any(q.question == "Real question?" for q in result.questions)


class TestAgentConfig:
    """Tests for AgentConfig."""

    def test_agent_id_format(self):
        """Agent ID should be dN-NNN format."""
        config = AgentConfig(
            question="Test?",
            model=ModelSpec.parse("opus"),
            depth=2,
            max_depth=5,
            agent_num=42,
        )
        assert config.agent_id == "d2-042"

    def test_agent_id_padding(self):
        """Agent number should be zero-padded to 3 digits."""
        config = AgentConfig(
            question="Test?",
            model=ModelSpec.parse("opus"),
            depth=0,
            max_depth=5,
            agent_num=1,
        )
        assert config.agent_id == "d0-001"

    def test_is_leaf_at_max_depth(self):
        """Agent at max_depth - 1 should be a leaf."""
        config = AgentConfig(
            question="Test?",
            model=ModelSpec.parse("opus"),
            depth=4,
            max_depth=5,
            agent_num=1,
        )
        assert config.is_leaf is True

    def test_is_not_leaf_before_max_depth(self):
        """Agent before max_depth should not be a leaf."""
        config = AgentConfig(
            question="Test?",
            model=ModelSpec.parse("opus"),
            depth=2,
            max_depth=5,
            agent_num=1,
        )
        assert config.is_leaf is False

    def test_unlimited_depth_not_leaf(self):
        """With max_depth=0 (unlimited), no agent should be a leaf."""
        config = AgentConfig(
            question="Test?",
            model=ModelSpec.parse("opus"),
            depth=100,
            max_depth=0,
            agent_num=1,
        )
        assert config.is_leaf is False


class TestAgentState:
    """Tests for AgentState."""

    def test_default_status(self):
        """Default status should be PENDING."""
        config = AgentConfig(
            question="Test?",
            model=ModelSpec.parse("opus"),
            depth=0,
            max_depth=5,
            agent_num=1,
        )
        state = AgentState(config=config)
        assert state.status == AgentStatus.PENDING

    def test_duration_ms_calculation(self):
        """Duration should be calculated from start and end times."""
        config = AgentConfig(
            question="Test?",
            model=ModelSpec.parse("opus"),
            depth=0,
            max_depth=5,
            agent_num=1,
        )
        state = AgentState(config=config)
        state.start_time = datetime(2024, 1, 1, 12, 0, 0)
        state.end_time = datetime(2024, 1, 1, 12, 0, 5)  # 5 seconds later
        assert state.duration_ms == 5000

    def test_duration_ms_none_without_times(self):
        """Duration should be None if times not set."""
        config = AgentConfig(
            question="Test?",
            model=ModelSpec.parse("opus"),
            depth=0,
            max_depth=5,
            agent_num=1,
        )
        state = AgentState(config=config)
        assert state.duration_ms is None


class TestResearchConfig:
    """Tests for ResearchConfig."""

    def test_default_output_dir(self):
        """Output directory should be auto-generated if not provided."""
        config = ResearchConfig(
            question="What makes startups successful?",
            orchestrator=ModelSpec.parse("opus"),
            researcher=ModelSpec.parse("haiku"),
        )
        assert config.output_dir is not None
        assert "reports" in str(config.output_dir)
        assert "what-makes-startups-successful" in str(config.output_dir)

    def test_slugify(self):
        """Slugify should create URL-safe slugs."""
        slug = ResearchConfig._slugify("What is 2+2?")
        assert " " not in slug
        assert "+" not in slug
        assert "?" not in slug
        assert slug == "what-is-2-2"

    def test_slugify_max_length(self):
        """Slugify should respect max length."""
        long_text = "a" * 100
        slug = ResearchConfig._slugify(long_text, max_len=20)
        assert len(slug) <= 20

    def test_custom_output_dir(self):
        """Custom output directory should be used."""
        from pathlib import Path

        config = ResearchConfig(
            question="Test?",
            orchestrator=ModelSpec.parse("opus"),
            researcher=ModelSpec.parse("haiku"),
            output_dir=Path("/custom/path"),
        )
        assert config.output_dir == Path("/custom/path")


class TestAgentStatus:
    """Tests for AgentStatus enum."""

    def test_status_values(self):
        """All expected status values should exist."""
        assert AgentStatus.PENDING.value == "pending"
        assert AgentStatus.EXPLORING.value == "exploring"
        assert AgentStatus.ANSWERING.value == "answering"
        assert AgentStatus.WAITING_FOR_CHILDREN.value == "waiting_for_children"
        assert AgentStatus.SYNTHESIZING.value == "synthesizing"
        assert AgentStatus.COMPLETE.value == "complete"
        assert AgentStatus.FAILED.value == "failed"

    def test_status_is_string_enum(self):
        """AgentStatus should be usable as a string."""
        status = AgentStatus.COMPLETE
        assert status == "complete"
        assert status.upper() == "COMPLETE"


class TestProviderType:
    """Tests for ProviderType enum."""

    def test_all_providers_exist(self):
        """All expected providers should exist."""
        assert ProviderType.CLAUDE.value == "claude"
        assert ProviderType.GEMINI.value == "gemini"
        assert ProviderType.OPENAI.value == "openai"
        assert ProviderType.OPENROUTER.value == "openrouter"
        assert ProviderType.KIMI.value == "kimi"

    def test_provider_from_string(self):
        """Should be able to create provider from string."""
        provider = ProviderType("claude")
        assert provider == ProviderType.CLAUDE
