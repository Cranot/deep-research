"""
Base utilities for operation implementations.
"""

from typing import Any

from ...models import ModelSpec
from ...providers.base import Provider, ProviderOptions
from ...providers.factory import get_provider_for_model
from ..operation import OperationRegistry, OperationType


def get_model_from_context(context: dict[str, Any]) -> ModelSpec:
    """Extract model spec from context."""
    model = context.get("model")
    if model is None:
        # Default to Claude haiku
        return ModelSpec.parse("haiku")
    if isinstance(model, str):
        return ModelSpec.parse(model)
    return model


def get_provider_from_context(context: dict[str, Any]) -> Provider:
    """Get provider from context model."""
    model = get_model_from_context(context)
    return get_provider_for_model(model)


def get_web_search_from_context(context: dict[str, Any]) -> bool:
    """Check if web search is enabled in context."""
    return context.get("web_search", False)


def make_provider_options(
    context: dict[str, Any],
    system_prompt: str | None = None,
) -> ProviderOptions:
    """Create ProviderOptions from context."""
    return ProviderOptions(
        system_prompt=system_prompt,
        web_search=get_web_search_from_context(context),
    )


def register_all_operations() -> None:
    """Register all concrete operations with the registry."""
    from .answer import AnswerOperation
    from .decompose import DecomposeOperation
    from .detect import DetectOperation
    from .ground import GroundOperation
    from .synthesize import SynthesizeOperation

    registry = OperationRegistry.instance()
    registry.register(OperationType.DECOMPOSE, DecomposeOperation)
    registry.register(OperationType.EXPAND, DecomposeOperation)  # Alias
    registry.register(OperationType.ANSWER, AnswerOperation)
    registry.register(OperationType.SYNTHESIZE, SynthesizeOperation)
    registry.register(OperationType.MERGE, SynthesizeOperation)  # Alias
    registry.register(OperationType.DETECT, DetectOperation)
    registry.register(OperationType.GROUND, GroundOperation)
