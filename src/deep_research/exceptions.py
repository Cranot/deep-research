"""
Custom exceptions for deep-research.

Provides specific exception types for different failure modes,
enabling targeted error handling and recovery.
"""

from typing import Any


class DeepResearchError(Exception):
    """Base exception for all deep-research errors."""

    def __init__(self, message: str, details: dict[str, Any] | None = None):
        super().__init__(message)
        self.message = message
        self.details = details or {}


# =============================================================================
# Validation Errors
# =============================================================================


class ValidationError(DeepResearchError):
    """Input validation failed."""

    pass


class QuestionValidationError(ValidationError):
    """Question validation failed."""

    def __init__(
        self,
        message: str,
        question: str | None = None,
        reason: str | None = None,
    ):
        super().__init__(message, {"question": question, "reason": reason})
        self.question = question
        self.reason = reason


class ConfigValidationError(ValidationError):
    """Configuration validation failed."""

    def __init__(
        self,
        message: str,
        field: str | None = None,
        value: Any = None,
        expected: str | None = None,
    ):
        super().__init__(message, {"field": field, "value": value, "expected": expected})
        self.field = field
        self.value = value
        self.expected = expected


class ModelValidationError(ValidationError):
    """Model specification validation failed."""

    def __init__(
        self,
        message: str,
        model_spec: str | None = None,
        valid_models: list[str] | None = None,
    ):
        super().__init__(message, {"model_spec": model_spec, "valid_models": valid_models})
        self.model_spec = model_spec
        self.valid_models = valid_models


# =============================================================================
# Provider Errors
# =============================================================================


class ProviderError(DeepResearchError):
    """Base class for provider-related errors."""

    def __init__(
        self,
        message: str,
        provider: str | None = None,
        model: str | None = None,
        details: dict[str, Any] | None = None,
    ):
        full_details = {"provider": provider, "model": model}
        if details:
            full_details.update(details)
        super().__init__(message, full_details)
        self.provider = provider
        self.model = model


class APIKeyError(ProviderError):
    """API key is missing or invalid."""

    def __init__(self, provider: str, env_var: str | None = None):
        message = f"API key not found for provider '{provider}'"
        if env_var:
            message += f". Set the {env_var} environment variable."
        super().__init__(message, provider=provider)
        self.env_var = env_var


class APIConnectionError(ProviderError):
    """Failed to connect to API."""

    def __init__(
        self,
        message: str,
        provider: str,
        model: str | None = None,
        endpoint: str | None = None,
    ):
        super().__init__(message, provider=provider, model=model, details={"endpoint": endpoint})
        self.endpoint = endpoint


class APITimeoutError(ProviderError):
    """API request timed out."""

    def __init__(
        self,
        provider: str,
        model: str | None = None,
        timeout_seconds: float | None = None,
    ):
        message = f"API request timed out for {provider}"
        if timeout_seconds:
            message += f" after {timeout_seconds}s"
        super().__init__(
            message,
            provider=provider,
            model=model,
            details={"timeout_seconds": timeout_seconds},
        )
        self.timeout_seconds = timeout_seconds


class APIRateLimitError(ProviderError):
    """API rate limit exceeded."""

    def __init__(
        self,
        provider: str,
        model: str | None = None,
        retry_after: float | None = None,
    ):
        message = f"Rate limit exceeded for {provider}"
        if retry_after:
            message += f". Retry after {retry_after}s"
        super().__init__(
            message,
            provider=provider,
            model=model,
            details={"retry_after": retry_after},
        )
        self.retry_after = retry_after


class APIResponseError(ProviderError):
    """API returned an error response."""

    def __init__(
        self,
        message: str,
        provider: str,
        model: str | None = None,
        status_code: int | None = None,
        response_body: str | None = None,
    ):
        super().__init__(
            message,
            provider=provider,
            model=model,
            details={"status_code": status_code, "response_body": response_body},
        )
        self.status_code = status_code
        self.response_body = response_body


class EmptyResponseError(ProviderError):
    """Provider returned empty response."""

    def __init__(self, provider: str, model: str | None = None, prompt: str | None = None):
        message = f"Empty response from {provider}"
        super().__init__(
            message,
            provider=provider,
            model=model,
            details={"prompt_preview": prompt[:100] if prompt else None},
        )


# =============================================================================
# Orchestration Errors
# =============================================================================


class OrchestrationError(DeepResearchError):
    """Base class for orchestration errors."""

    pass


class AgentError(OrchestrationError):
    """An agent failed during execution."""

    def __init__(
        self,
        message: str,
        agent_id: str,
        question: str | None = None,
        original_error: Exception | None = None,
    ):
        super().__init__(
            message,
            {
                "agent_id": agent_id,
                "question": question,
                "original_error": str(original_error) if original_error else None,
            },
        )
        self.agent_id = agent_id
        self.question = question
        self.original_error = original_error


class ChildFailureError(OrchestrationError):
    """One or more child agents failed."""

    def __init__(
        self,
        message: str,
        parent_id: str,
        failed_children: list[str],
        total_children: int,
    ):
        super().__init__(
            message,
            {
                "parent_id": parent_id,
                "failed_children": failed_children,
                "total_children": total_children,
            },
        )
        self.parent_id = parent_id
        self.failed_children = failed_children
        self.total_children = total_children


class MaxDepthExceededError(OrchestrationError):
    """Maximum recursion depth exceeded."""

    def __init__(self, current_depth: int, max_depth: int):
        message = f"Maximum depth {max_depth} exceeded at depth {current_depth}"
        super().__init__(message, {"current_depth": current_depth, "max_depth": max_depth})
        self.current_depth = current_depth
        self.max_depth = max_depth


# =============================================================================
# Parsing Errors
# =============================================================================


class ParsingError(DeepResearchError):
    """Failed to parse output."""

    pass


class ExplorationParsingError(ParsingError):
    """Failed to parse exploration output for Q: lines."""

    def __init__(self, output: str | None = None, expected_format: str | None = None):
        message = "Failed to parse exploration output"
        super().__init__(
            message,
            {
                "output_preview": output[:200] if output else None,
                "expected_format": expected_format,
            },
        )


# =============================================================================
# Cache Errors
# =============================================================================


class CacheError(DeepResearchError):
    """Cache operation failed."""

    pass


class CacheCorruptedError(CacheError):
    """Cache file is corrupted."""

    def __init__(self, cache_file: str, original_error: Exception | None = None):
        message = f"Cache file corrupted: {cache_file}"
        super().__init__(
            message,
            {"cache_file": cache_file, "original_error": str(original_error)},
        )
        self.cache_file = cache_file
        self.original_error = original_error
