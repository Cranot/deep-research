"""
Tests for validation.py - input validation.
"""

import os
from pathlib import Path
from unittest.mock import patch

import pytest

from deep_research.exceptions import (
    APIKeyError,
    ConfigValidationError,
    ModelValidationError,
    QuestionValidationError,
)
from deep_research.models import ProviderType
from deep_research.validation import (
    MAX_DEPTH_LIMIT,
    MAX_PARALLEL_LIMIT,
    MAX_QUESTION_LENGTH,
    REQUIRED_ENV_VARS,
    validate_api_key,
    validate_depth,
    validate_model_spec,
    validate_output_dir,
    validate_parallel,
    validate_question,
)


class TestValidateQuestion:
    """Tests for question validation."""

    def test_valid_question(self):
        """Valid question should be returned stripped."""
        result = validate_question("  What is the meaning of life?  ")
        assert result == "What is the meaning of life?"

    def test_empty_question(self):
        """Empty question should raise error."""
        with pytest.raises(QuestionValidationError) as exc_info:
            validate_question("")
        assert exc_info.value.reason == "empty_question"

    def test_whitespace_only(self):
        """Whitespace-only question should raise error."""
        with pytest.raises(QuestionValidationError) as exc_info:
            validate_question("   \n\t   ")
        assert exc_info.value.reason == "empty_question"

    def test_none_question(self):
        """None question should raise error."""
        with pytest.raises(QuestionValidationError) as exc_info:
            validate_question(None)
        assert exc_info.value.reason == "null_question"

    def test_too_short(self):
        """Question shorter than minimum should raise error."""
        with pytest.raises(QuestionValidationError) as exc_info:
            validate_question("Hi")
        assert exc_info.value.reason == "too_short"

    def test_exactly_minimum_length(self):
        """Question exactly at minimum should be valid."""
        result = validate_question("Why")  # 3 characters
        assert result == "Why"

    def test_too_long(self):
        """Question longer than maximum should raise error."""
        long_question = "x" * (MAX_QUESTION_LENGTH + 1)
        with pytest.raises(QuestionValidationError) as exc_info:
            validate_question(long_question)
        assert exc_info.value.reason == "too_long"

    def test_exactly_maximum_length(self):
        """Question exactly at maximum should be valid."""
        # Use words with spaces to avoid binary data detection
        # End with 'x' to prevent strip() from reducing length
        word = "word "
        repeat = (MAX_QUESTION_LENGTH - 1) // len(word)
        base = word * repeat
        # Pad to exactly MAX_QUESTION_LENGTH ending with non-space
        max_question = base + "x" * (MAX_QUESTION_LENGTH - len(base))
        result = validate_question(max_question)
        assert len(result) == MAX_QUESTION_LENGTH

    def test_binary_data_detection(self):
        """Long lines without spaces should be detected as binary."""
        binary_like = "a" * 600  # > 500 characters without spaces
        with pytest.raises(QuestionValidationError) as exc_info:
            validate_question(binary_like)
        assert exc_info.value.reason == "binary_data"

    def test_control_characters(self):
        """Control characters should raise error."""
        with pytest.raises(QuestionValidationError) as exc_info:
            validate_question("What is\x00this?")
        assert exc_info.value.reason == "control_characters"

    def test_newlines_allowed(self):
        """Newlines should be allowed in questions."""
        question = "What is:\n1. First thing\n2. Second thing?"
        result = validate_question(question)
        assert "\n" in result

    def test_tabs_allowed(self):
        """Tabs should be allowed in questions."""
        question = "What is\tthis\tthing?"
        result = validate_question(question)
        assert "\t" in result


class TestValidateModelSpec:
    """Tests for model specification validation."""

    def test_valid_simple_model(self):
        """Simple model name should be valid."""
        spec, warnings = validate_model_spec("opus")
        assert spec.provider == ProviderType.CLAUDE
        assert spec.model == "opus"
        assert not warnings

    def test_valid_with_provider(self):
        """Model with provider should be valid."""
        spec, warnings = validate_model_spec("gemini:flash")
        assert spec.provider == ProviderType.GEMINI
        assert spec.model == "flash"
        assert not warnings

    def test_empty_model(self):
        """Empty model should raise error."""
        with pytest.raises(ModelValidationError):
            validate_model_spec("")

    def test_whitespace_model(self):
        """Whitespace-only model should raise error."""
        with pytest.raises(ModelValidationError):
            validate_model_spec("   ")

    def test_unknown_provider(self):
        """Unknown provider should raise error."""
        with pytest.raises(ModelValidationError) as exc_info:
            validate_model_spec("unknown:model")
        assert "unknown" in exc_info.value.message.lower()

    def test_unknown_model_warning(self):
        """Unknown model should produce warning but not error."""
        spec, warnings = validate_model_spec("claude:unknown-model")
        assert spec.model == "unknown-model"
        assert len(warnings) == 1
        assert "not in known models" in warnings[0]

    def test_known_models_no_warning(self):
        """Known models should not produce warnings."""
        # Claude models
        _, w1 = validate_model_spec("opus")
        _, w2 = validate_model_spec("haiku")
        _, w3 = validate_model_spec("sonnet")
        assert not w1 and not w2 and not w3

        # Gemini models
        _, w4 = validate_model_spec("gemini:flash")
        _, w5 = validate_model_spec("gemini:pro")
        assert not w4 and not w5


class TestValidateDepth:
    """Tests for depth validation."""

    def test_valid_depth(self):
        """Valid depth should be returned."""
        assert validate_depth(0) == 0
        assert validate_depth(5) == 5
        assert validate_depth(MAX_DEPTH_LIMIT) == MAX_DEPTH_LIMIT

    def test_negative_depth(self):
        """Negative depth should raise error."""
        with pytest.raises(ConfigValidationError) as exc_info:
            validate_depth(-1)
        assert exc_info.value.field == "depth"

    def test_too_large_depth(self):
        """Depth exceeding maximum should raise error."""
        with pytest.raises(ConfigValidationError) as exc_info:
            validate_depth(MAX_DEPTH_LIMIT + 1)
        assert exc_info.value.field == "depth"

    def test_non_integer_depth(self):
        """Non-integer depth should raise error."""
        with pytest.raises(ConfigValidationError) as exc_info:
            validate_depth(3.5)
        assert exc_info.value.field == "depth"


class TestValidateParallel:
    """Tests for parallel validation."""

    def test_valid_parallel(self):
        """Valid parallel should be returned."""
        assert validate_parallel(1) == 1
        assert validate_parallel(10) == 10
        assert validate_parallel(MAX_PARALLEL_LIMIT) == MAX_PARALLEL_LIMIT

    def test_zero_parallel(self):
        """Zero parallel should raise error."""
        with pytest.raises(ConfigValidationError) as exc_info:
            validate_parallel(0)
        assert exc_info.value.field == "parallel"

    def test_negative_parallel(self):
        """Negative parallel should raise error."""
        with pytest.raises(ConfigValidationError) as exc_info:
            validate_parallel(-1)
        assert exc_info.value.field == "parallel"

    def test_too_large_parallel(self):
        """Parallel exceeding maximum should raise error."""
        with pytest.raises(ConfigValidationError) as exc_info:
            validate_parallel(MAX_PARALLEL_LIMIT + 1)
        assert exc_info.value.field == "parallel"


class TestValidateOutputDir:
    """Tests for output directory validation."""

    def test_none_output_dir(self):
        """None should return None."""
        assert validate_output_dir(None) is None

    def test_valid_path(self):
        """Valid path should be returned as Path."""
        result = validate_output_dir("./reports")
        assert isinstance(result, Path)
        assert result == Path("./reports")

    def test_string_to_path(self):
        """String should be converted to Path."""
        result = validate_output_dir("/tmp/output")
        assert isinstance(result, Path)

    def test_path_remains_path(self):
        """Path should remain Path."""
        p = Path("./output")
        result = validate_output_dir(p)
        assert result == p


class TestValidateAPIKey:
    """Tests for API key validation."""

    def test_missing_key(self):
        """Missing API key should raise error."""
        with patch.dict(os.environ, {}, clear=True):
            with pytest.raises(APIKeyError) as exc_info:
                validate_api_key(ProviderType.OPENAI)
            assert exc_info.value.provider == "openai"
            assert exc_info.value.env_var == "GPT5_MINI_API_KEY"

    def test_present_key(self):
        """Present API key should return the key."""
        with patch.dict(os.environ, {"GPT5_MINI_API_KEY": "test-key"}):
            result = validate_api_key(ProviderType.OPENAI)
            assert result == "test-key"

    def test_whitespace_key(self):
        """Whitespace-only key should raise error."""
        with patch.dict(os.environ, {"GPT5_MINI_API_KEY": "   "}):
            with pytest.raises(APIKeyError):
                validate_api_key(ProviderType.OPENAI)

    def test_key_stripped(self):
        """Key should be stripped of whitespace."""
        with patch.dict(os.environ, {"GPT5_MINI_API_KEY": "  test-key  "}):
            result = validate_api_key(ProviderType.OPENAI)
            assert result == "test-key"

    def test_claude_no_key_required(self):
        """Claude uses CLI subscription, no API key needed."""
        with patch.dict(os.environ, {}, clear=True):
            # Should return empty string, not raise error
            result = validate_api_key(ProviderType.CLAUDE)
            assert result == ""

    def test_gemini_no_key_required(self):
        """Gemini uses the local gemini CLI, no API key needed."""
        with patch.dict(os.environ, {}, clear=True):
            result = validate_api_key(ProviderType.GEMINI)
            assert result == ""

    def test_all_provider_env_vars(self):
        """Each key-based provider should have the correct env var."""
        env_vars = {
            ProviderType.OPENAI: "GPT5_MINI_API_KEY",
            ProviderType.OPENROUTER: "OPENROUTER_API_KEY",
            ProviderType.KIMI: "KIMI_API_KEY",
        }
        assert set(env_vars) == set(REQUIRED_ENV_VARS), (
            "REQUIRED_ENV_VARS changed; CLI-based providers (claude, gemini) must stay out of it."
        )
        for provider, env_var in env_vars.items():
            assert REQUIRED_ENV_VARS[provider] == env_var
            with patch.dict(os.environ, {env_var: "test-key"}):
                result = validate_api_key(provider)
                assert result == "test-key"
