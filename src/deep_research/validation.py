"""
Input validation for deep-research.

Provides upfront validation of:
- Questions (non-empty, length limits, encoding)
- Model specifications (valid providers, known models)
- Configuration (depth, parallel limits, output dirs)
- API keys (existence before running)
"""

import os
import re
from pathlib import Path

from .exceptions import (
    APIKeyError,
    ConfigValidationError,
    ModelValidationError,
    QuestionValidationError,
)
from .models import ModelSpec, ProviderType, ResearchConfig

# =============================================================================
# Constants
# =============================================================================

# Maximum question length (characters)
MAX_QUESTION_LENGTH = 10000

# Minimum question length
MIN_QUESTION_LENGTH = 3

# Maximum recursion depth
MAX_DEPTH_LIMIT = 20

# Maximum parallel agents
MAX_PARALLEL_LIMIT = 100

# Known models per provider (for validation warnings, not hard blocks)
KNOWN_MODELS = {
    ProviderType.CLAUDE: ["opus", "sonnet", "haiku"],
    ProviderType.GEMINI: ["flash", "pro", "gemini-3-flash-preview", "gemini-3-pro-preview"],
    ProviderType.OPENAI: ["gpt5-mini", "gpt-5-mini"],
    ProviderType.OPENROUTER: ["grok", "grok-3", "grok-4"],
    ProviderType.KIMI: ["kimi", "kimi-k2-thinking"],
}

# Required environment variables per provider
# NOTE: Claude and Gemini use CLI (subscription-based), no API key needed
REQUIRED_ENV_VARS = {
    ProviderType.OPENAI: "GPT5_MINI_API_KEY",
    ProviderType.OPENROUTER: "OPENROUTER_API_KEY",
    ProviderType.KIMI: "KIMI_API_KEY",
}

# For display purposes (includes CLI-based providers)
ALL_ENV_VARS = {
    ProviderType.CLAUDE: "ANTHROPIC_API_KEY (optional - uses CLI)",
    ProviderType.GEMINI: "GEMINI_API_KEY (optional - uses CLI)",
    ProviderType.OPENAI: "GPT5_MINI_API_KEY",
    ProviderType.OPENROUTER: "OPENROUTER_API_KEY",
    ProviderType.KIMI: "KIMI_API_KEY",
}


# =============================================================================
# Question Validation
# =============================================================================


def validate_question(question: str) -> str:
    """
    Validate a research question.

    Args:
        question: The question to validate

    Returns:
        The cleaned/normalized question

    Raises:
        QuestionValidationError: If validation fails
    """
    # Check for None
    if question is None:
        raise QuestionValidationError(
            "Question cannot be None",
            question=None,
            reason="null_question",
        )

    # Strip whitespace
    question = question.strip()

    # Check empty
    if not question:
        raise QuestionValidationError(
            "Question cannot be empty",
            question="",
            reason="empty_question",
        )

    # Check minimum length
    if len(question) < MIN_QUESTION_LENGTH:
        raise QuestionValidationError(
            f"Question too short (minimum {MIN_QUESTION_LENGTH} characters)",
            question=question,
            reason="too_short",
        )

    # Check maximum length
    if len(question) > MAX_QUESTION_LENGTH:
        raise QuestionValidationError(
            f"Question too long (maximum {MAX_QUESTION_LENGTH} characters, got {len(question)})",
            question=question[:100] + "...",
            reason="too_long",
        )

    # Check for problematic patterns
    # Very long lines without spaces (could be binary/encoded data)
    lines = question.split("\n")
    for line in lines:
        if len(line) > 500 and " " not in line:
            raise QuestionValidationError(
                "Question appears to contain binary or encoded data",
                question=question[:100] + "...",
                reason="binary_data",
            )

    # Check for control characters (except newlines/tabs)
    control_chars = re.findall(r"[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]", question)
    if control_chars:
        raise QuestionValidationError(
            "Question contains invalid control characters",
            question=question[:100] + "...",
            reason="control_characters",
        )

    return question


# =============================================================================
# Model Validation
# =============================================================================


def validate_model_spec(spec: str) -> tuple[ModelSpec, list[str]]:
    """
    Validate and parse a model specification.

    Args:
        spec: Model spec like "opus" or "gemini:flash"

    Returns:
        Tuple of (ModelSpec, warnings list)

    Raises:
        ModelValidationError: If spec is invalid
    """
    warnings: list[str] = []

    if not spec or not spec.strip():
        raise ModelValidationError(
            "Model specification cannot be empty",
            model_spec=spec,
        )

    spec = spec.strip()

    try:
        model_spec = ModelSpec.parse(spec)
    except ValueError as e:
        # Invalid provider
        if ":" in spec:
            provider_str = spec.split(":")[0]
            valid_providers = [p.value for p in ProviderType]
            raise ModelValidationError(
                f"Unknown provider '{provider_str}'",
                model_spec=spec,
                valid_models=valid_providers,
            )
        raise ModelValidationError(str(e), model_spec=spec)

    # Check if model is known (warning, not error)
    known = KNOWN_MODELS.get(model_spec.provider, [])
    if known and model_spec.model not in known:
        warnings.append(
            f"Model '{model_spec.model}' not in known models for {model_spec.provider.value}: {known}"
        )

    return model_spec, warnings


def validate_leaf_models(specs: list[str]) -> tuple[list[ModelSpec], list[str]]:
    """
    Validate a list of leaf model specifications.

    Args:
        specs: List of model specs

    Returns:
        Tuple of (list of ModelSpec, warnings list)

    Raises:
        ModelValidationError: If any spec is invalid
    """
    models: list[ModelSpec] = []
    warnings: list[str] = []

    for spec in specs:
        model, model_warnings = validate_model_spec(spec)
        models.append(model)
        warnings.extend(model_warnings)

    return models, warnings


# =============================================================================
# Configuration Validation
# =============================================================================


def validate_depth(depth: int) -> int:
    """
    Validate max_depth setting.

    Args:
        depth: Depth value (0 = unlimited)

    Returns:
        Validated depth

    Raises:
        ConfigValidationError: If invalid
    """
    if not isinstance(depth, int):
        raise ConfigValidationError(
            f"Depth must be an integer, got {type(depth).__name__}",
            field="depth",
            value=depth,
            expected="integer >= 0",
        )

    if depth < 0:
        raise ConfigValidationError(
            "Depth cannot be negative",
            field="depth",
            value=depth,
            expected="integer >= 0",
        )

    if depth > MAX_DEPTH_LIMIT:
        raise ConfigValidationError(
            f"Depth exceeds maximum ({MAX_DEPTH_LIMIT})",
            field="depth",
            value=depth,
            expected=f"integer 0-{MAX_DEPTH_LIMIT}",
        )

    return depth


def validate_parallel(parallel: int) -> int:
    """
    Validate max_parallel setting.

    Args:
        parallel: Number of parallel agents

    Returns:
        Validated parallel value

    Raises:
        ConfigValidationError: If invalid
    """
    if not isinstance(parallel, int):
        raise ConfigValidationError(
            f"Parallel must be an integer, got {type(parallel).__name__}",
            field="parallel",
            value=parallel,
            expected="integer 1-100",
        )

    if parallel < 1:
        raise ConfigValidationError(
            "Parallel must be at least 1",
            field="parallel",
            value=parallel,
            expected="integer 1-100",
        )

    if parallel > MAX_PARALLEL_LIMIT:
        raise ConfigValidationError(
            f"Parallel exceeds maximum ({MAX_PARALLEL_LIMIT})",
            field="parallel",
            value=parallel,
            expected=f"integer 1-{MAX_PARALLEL_LIMIT}",
        )

    return parallel


def validate_output_dir(output_dir: Path | str | None) -> Path | None:
    """
    Validate output directory.

    Args:
        output_dir: Output directory path

    Returns:
        Validated Path or None

    Raises:
        ConfigValidationError: If invalid
    """
    if output_dir is None:
        return None

    if isinstance(output_dir, str):
        output_dir = Path(output_dir)

    # Check if parent is writable (for new directories)
    parent = output_dir.parent
    if parent.exists() and not os.access(parent, os.W_OK):
        raise ConfigValidationError(
            f"Cannot write to directory: {parent}",
            field="output_dir",
            value=str(output_dir),
            expected="writable directory",
        )

    return output_dir


# =============================================================================
# API Key Validation
# =============================================================================


def validate_api_key(provider: ProviderType) -> str:
    """
    Validate that an API key exists for a provider.

    Args:
        provider: The provider type

    Returns:
        The API key value

    Raises:
        APIKeyError: If key not found
    """
    env_var = REQUIRED_ENV_VARS.get(provider)
    if not env_var:
        return ""  # No API key required

    value = os.environ.get(env_var)
    if not value or not value.strip():
        raise APIKeyError(provider.value, env_var)

    return value.strip()


def validate_api_keys_for_config(config: ResearchConfig) -> list[str]:
    """
    Validate all required API keys for a research config.

    Args:
        config: The research configuration

    Returns:
        List of warnings

    Raises:
        APIKeyError: If a required key is missing
    """
    warnings: list[str] = []

    # Collect all providers used
    providers_used: set[ProviderType] = {
        config.orchestrator.provider,
        config.researcher.provider,
    }

    for leaf in config.leaf_models:
        providers_used.add(leaf.provider)

    if config.merger:
        providers_used.add(config.merger.provider)

    # Validate each provider's API key
    for provider in providers_used:
        validate_api_key(provider)

    return warnings


# =============================================================================
# Full Config Validation
# =============================================================================


def validate_research_config(config: ResearchConfig) -> list[str]:
    """
    Validate a complete research configuration.

    Args:
        config: The configuration to validate

    Returns:
        List of warnings (validation passes if no exception)

    Raises:
        ValidationError subclass: If validation fails
    """
    warnings: list[str] = []

    # Validate question
    validate_question(config.question)

    # Validate models
    _, orch_warnings = validate_model_spec(str(config.orchestrator))
    warnings.extend(orch_warnings)

    _, res_warnings = validate_model_spec(str(config.researcher))
    warnings.extend(res_warnings)

    # Validate leaf models if specified
    if config.leaf_models:
        for leaf in config.leaf_models:
            _, leaf_warnings = validate_model_spec(str(leaf))
            warnings.extend(leaf_warnings)

    # Validate merger if specified
    if config.merger:
        _, merger_warnings = validate_model_spec(str(config.merger))
        warnings.extend(merger_warnings)

    # Validate depth and parallel
    validate_depth(config.max_depth)
    validate_parallel(config.max_parallel)

    # Validate output directory
    validate_output_dir(config.output_dir)

    # Validate API keys
    key_warnings = validate_api_keys_for_config(config)
    warnings.extend(key_warnings)

    return warnings
