"""
Provider factory - creates and caches provider instances.
"""

from ..models import ModelSpec, ProviderType
from .base import Provider
from .claude import ClaudeProvider
from .gemini import GeminiProvider
from .kimi import KimiProvider
from .openai_azure import OpenAIProvider
from .openrouter import OpenRouterProvider

# Singleton instances
_providers: dict[ProviderType, Provider] = {}


def create_provider(provider_type: ProviderType) -> Provider:
    """Create a new provider instance."""
    if provider_type == ProviderType.CLAUDE:
        return ClaudeProvider()
    elif provider_type == ProviderType.GEMINI:
        return GeminiProvider()
    elif provider_type == ProviderType.OPENAI:
        return OpenAIProvider()
    elif provider_type == ProviderType.OPENROUTER:
        return OpenRouterProvider()
    elif provider_type == ProviderType.KIMI:
        return KimiProvider()
    else:
        raise ValueError(f"Unknown provider type: {provider_type}")


def get_provider(provider_type: ProviderType) -> Provider:
    """Get or create a cached provider instance."""
    if provider_type not in _providers:
        _providers[provider_type] = create_provider(provider_type)
    return _providers[provider_type]


def get_provider_for_model(model_spec: ModelSpec) -> Provider:
    """Get provider for a model specification."""
    return get_provider(model_spec.provider)
