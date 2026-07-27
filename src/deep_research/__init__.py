"""
Deep Research - Fractal exploration of any question through recursive AI agents.

A question spawns angles. Each angle spawns deeper angles. The tree grows until
questions become atomic - then everything synthesizes back up into one comprehensive answer.

Public API:
    - Orchestrator: Main research orchestrator
    - ResearchConfig: Configuration for research runs
    - ModelSpec: Model specification (provider:model)

Exceptions:
    - DeepResearchError: Base exception class
    - ValidationError: Input validation errors
    - ProviderError: Provider-related errors

Utilities:
    - validate_question: Validate a research question
    - validate_model_spec: Validate a model specification
"""

__version__ = "0.1.0"

# Main classes
# Exceptions
from .exceptions import (
    AgentError,
    APIConnectionError,
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

# Logging
from .logging import (
    ResearchLogger,
    ResearchMetrics,
    get_logger,
    init_logger,
)
from .models import (
    AgentConfig,
    AgentState,
    AgentStatus,
    ExplorationResult,
    ModelSpec,
    ProviderType,
    ResearchConfig,
    ResearchQuestion,
)
from .orchestrator import Orchestrator

# Settings
from .settings import configure, settings

# Validation utilities
from .validation import (
    validate_api_key,
    validate_depth,
    validate_model_spec,
    validate_parallel,
    validate_question,
    validate_research_config,
)

__all__ = [
    # Version
    "__version__",
    # Main classes
    "Orchestrator",
    "ResearchConfig",
    "ModelSpec",
    "AgentConfig",
    "AgentState",
    "AgentStatus",
    "ProviderType",
    "ExplorationResult",
    "ResearchQuestion",
    # Exceptions
    "DeepResearchError",
    "ValidationError",
    "QuestionValidationError",
    "ConfigValidationError",
    "ModelValidationError",
    "ProviderError",
    "APIKeyError",
    "APIConnectionError",
    "APITimeoutError",
    "APIRateLimitError",
    "APIResponseError",
    "EmptyResponseError",
    "OrchestrationError",
    "AgentError",
    "ChildFailureError",
    "ParsingError",
    "CacheError",
    # Validation
    "validate_question",
    "validate_model_spec",
    "validate_depth",
    "validate_parallel",
    "validate_api_key",
    "validate_research_config",
    # Logging
    "ResearchLogger",
    "init_logger",
    "get_logger",
    "ResearchMetrics",
    # Settings
    "settings",
    "configure",
]
