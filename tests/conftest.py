"""
Pytest configuration and fixtures.
"""

import os
from unittest.mock import patch

import pytest


@pytest.fixture
def temp_output_dir(tmp_path):
    """Create a temporary output directory for tests."""
    output_dir = tmp_path / "output"
    output_dir.mkdir()
    return output_dir


@pytest.fixture
def mock_api_keys():
    """Mock all API keys as present."""
    env_vars = {
        "ANTHROPIC_API_KEY": "test-anthropic-key",
        "GEMINI_API_KEY": "test-gemini-key",
        "GPT5_MINI_API_KEY": "test-openai-key",
        "OPENROUTER_API_KEY": "test-openrouter-key",
        "KIMI_API_KEY": "test-kimi-key",
    }
    with patch.dict(os.environ, env_vars):
        yield env_vars


@pytest.fixture
def mock_no_api_keys():
    """Mock all API keys as missing."""
    # Clear all API-related env vars
    env_vars_to_clear = [
        "ANTHROPIC_API_KEY",
        "GEMINI_API_KEY",
        "GPT5_MINI_API_KEY",
        "OPENROUTER_API_KEY",
        "KIMI_API_KEY",
    ]
    cleaned = {k: "" for k in env_vars_to_clear if k in os.environ}
    with patch.dict(os.environ, {}, clear=False):
        for key in env_vars_to_clear:
            os.environ.pop(key, None)
        yield
        # Restore
        for key, value in cleaned.items():
            os.environ[key] = value


@pytest.fixture
def sample_research_config(temp_output_dir, mock_api_keys):
    """Create a sample ResearchConfig for testing."""
    from deep_research.models import ModelSpec, ResearchConfig

    return ResearchConfig(
        question="What is the meaning of life?",
        orchestrator=ModelSpec.parse("opus"),
        researcher=ModelSpec.parse("haiku"),
        max_depth=2,
        max_parallel=5,
        output_dir=temp_output_dir,
    )


@pytest.fixture
def sample_exploration_output():
    """Sample exploration output with Q: lines."""
    return """Let me explore this question from multiple angles.

Q: What are the philosophical perspectives on meaning?
This explores classical and modern philosophical views.

Q: How do different cultures define life's purpose?
Cross-cultural examination of meaning.

Q: What does science tell us about consciousness and meaning?
Neuroscience and cognitive science perspectives.

Q: How do personal experiences shape our sense of meaning?
Individual psychology and lived experience.

These angles should provide comprehensive coverage."""


@pytest.fixture
def sample_empty_exploration():
    """Sample exploration output with no Q: lines."""
    return """This is just a regular answer without any sub-questions.
The meaning of life is subjective and varies by individual."""
