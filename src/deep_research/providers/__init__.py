"""
LLM Provider abstractions.

Supports:
- Claude (via claude-agent-sdk)
- Gemini (via CLI)
- OpenAI/Azure (GPT-5 Mini)
- OpenRouter (Grok, etc.)
- Kimi (via Azure AI Services)
"""

from .base import Provider
from .claude import ClaudeProvider
from .factory import create_provider, get_provider, get_provider_for_model
from .gemini import GeminiProvider
from .kimi import KimiProvider
from .openai_azure import OpenAIProvider
from .openrouter import OpenRouterProvider

__all__ = [
    "Provider",
    "ClaudeProvider",
    "GeminiProvider",
    "OpenAIProvider",
    "OpenRouterProvider",
    "KimiProvider",
    "create_provider",
    "get_provider",
    "get_provider_for_model",
]
