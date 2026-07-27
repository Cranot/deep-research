"""
Tests for exceptions.py - custom exception classes.
"""

import pytest

from deep_research.exceptions import (
    AgentError,
    APIKeyError,
    APIRateLimitError,
    APIResponseError,
    APITimeoutError,
    CacheError,
    ChildFailureError,
    ConfigValidationError,
    DeepResearchError,
    EmptyResponseError,
    ModelValidationError,
    OrchestrationError,
    ParsingError,
    ProviderError,
    QuestionValidationError,
    ValidationError,
)


class TestDeepResearchError:
    """Tests for base exception class."""

    def test_basic_creation(self):
        """Create exception with just message."""
        error = DeepResearchError("Something went wrong")
        assert str(error) == "Something went wrong"
        assert error.message == "Something went wrong"
        assert error.details == {}

    def test_with_details(self):
        """Create exception with details."""
        error = DeepResearchError("Error", {"key": "value"})
        assert error.details == {"key": "value"}

    def test_inheritance(self):
        """All custom exceptions should inherit from base."""
        assert issubclass(ValidationError, DeepResearchError)
        assert issubclass(ProviderError, DeepResearchError)
        assert issubclass(OrchestrationError, DeepResearchError)
        assert issubclass(ParsingError, DeepResearchError)
        assert issubclass(CacheError, DeepResearchError)


class TestQuestionValidationError:
    """Tests for question validation error."""

    def test_creation(self):
        """Create with all fields."""
        error = QuestionValidationError(
            "Question is empty",
            question="",
            reason="empty_question",
        )
        assert error.message == "Question is empty"
        assert error.question == ""
        assert error.reason == "empty_question"
        assert error.details["question"] == ""
        assert error.details["reason"] == "empty_question"

    def test_optional_fields(self):
        """Fields can be None."""
        error = QuestionValidationError("Error")
        assert error.question is None
        assert error.reason is None


class TestConfigValidationError:
    """Tests for config validation error."""

    def test_creation(self):
        """Create with all fields."""
        error = ConfigValidationError(
            "Invalid depth",
            field="depth",
            value=-1,
            expected="positive integer",
        )
        assert error.field == "depth"
        assert error.value == -1
        assert error.expected == "positive integer"


class TestModelValidationError:
    """Tests for model validation error."""

    def test_creation(self):
        """Create with all fields."""
        error = ModelValidationError(
            "Unknown provider",
            model_spec="unknown:model",
            valid_models=["claude", "gemini"],
        )
        assert error.model_spec == "unknown:model"
        assert error.valid_models == ["claude", "gemini"]


class TestAPIKeyError:
    """Tests for API key error."""

    def test_creation(self):
        """Create with provider and env var."""
        error = APIKeyError("claude", "ANTHROPIC_API_KEY")
        assert error.provider == "claude"
        assert error.env_var == "ANTHROPIC_API_KEY"
        assert "ANTHROPIC_API_KEY" in str(error)

    def test_without_env_var(self):
        """Create without env var hint."""
        error = APIKeyError("custom")
        assert error.env_var is None
        assert "custom" in str(error)


class TestAPITimeoutError:
    """Tests for API timeout error."""

    def test_creation(self):
        """Create with timeout."""
        error = APITimeoutError("claude", "opus", 30.0)
        assert error.provider == "claude"
        assert error.model == "opus"
        assert error.timeout_seconds == 30.0
        assert "30" in str(error)

    def test_without_timeout(self):
        """Create without specific timeout."""
        error = APITimeoutError("claude")
        assert error.timeout_seconds is None


class TestAPIRateLimitError:
    """Tests for API rate limit error."""

    def test_creation(self):
        """Create with retry after."""
        error = APIRateLimitError("claude", "opus", 60.0)
        assert error.provider == "claude"
        assert error.retry_after == 60.0
        assert "60" in str(error)


class TestAPIResponseError:
    """Tests for API response error."""

    def test_creation(self):
        """Create with full details."""
        error = APIResponseError(
            "Server error",
            provider="claude",
            model="opus",
            status_code=500,
            response_body='{"error": "internal"}',
        )
        assert error.status_code == 500
        assert error.response_body == '{"error": "internal"}'


class TestEmptyResponseError:
    """Tests for empty response error."""

    def test_creation(self):
        """Create with prompt."""
        error = EmptyResponseError("claude", "opus", "What is 2+2?")
        assert error.provider == "claude"
        assert error.model == "opus"
        assert "claude" in str(error)


class TestAgentError:
    """Tests for agent error."""

    def test_creation(self):
        """Create with all fields."""
        original = ValueError("original error")
        error = AgentError(
            "Agent failed",
            agent_id="d1-001",
            question="What is this?",
            original_error=original,
        )
        assert error.agent_id == "d1-001"
        assert error.question == "What is this?"
        assert error.original_error is original


class TestChildFailureError:
    """Tests for child failure error."""

    def test_creation(self):
        """Create with failure details."""
        error = ChildFailureError(
            "Children failed",
            parent_id="d0-001",
            failed_children=["d1-001", "d1-002"],
            total_children=5,
        )
        assert error.parent_id == "d0-001"
        assert len(error.failed_children) == 2
        assert error.total_children == 5


class TestExceptionRaising:
    """Test that exceptions can be properly raised and caught."""

    def test_raise_and_catch_base(self):
        """Base exception can be caught."""
        with pytest.raises(DeepResearchError):
            raise DeepResearchError("test")

    def test_catch_by_parent(self):
        """Child exceptions can be caught by parent type."""
        with pytest.raises(ValidationError):
            raise QuestionValidationError("test")

        with pytest.raises(DeepResearchError):
            raise QuestionValidationError("test")

    def test_provider_error_hierarchy(self):
        """Provider errors can be caught by parent."""
        with pytest.raises(ProviderError):
            raise APITimeoutError("claude")

        with pytest.raises(ProviderError):
            raise APIRateLimitError("claude")

        with pytest.raises(DeepResearchError):
            raise APITimeoutError("claude")
