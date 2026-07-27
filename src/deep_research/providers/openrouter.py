"""
OpenRouter provider (Grok, GPT, Claude, etc.).

Uses the OpenAI SDK with OpenRouter's base URL.
Gives access to many models through one API.
"""

import os

from openai import OpenAI
from rich.console import Console

from ..cache import get_cached, set_cached
from .base import Provider, ProviderOptions

_console = Console(stderr=True)


# Model name mappings (alias -> OpenRouter model ID)
# Format: provider/model-name
OPENROUTER_MODELS = {
    # Grok models (xAI)
    "grok": "x-ai/grok-3",
    "grok-3": "x-ai/grok-3",
    "grok-3-mini": "x-ai/grok-3-mini",
    "grok-4": "x-ai/grok-4",
    "grok-4-fast": "x-ai/grok-4-fast",
    # OpenAI via OpenRouter
    "gpt-4o": "openai/gpt-4o",
    # Anthropic via OpenRouter
    "claude-sonnet": "anthropic/claude-sonnet-4",
    # Meta
    "llama": "meta-llama/llama-4-maverick",
}


class OpenRouterProvider(Provider):
    """OpenRouter provider using the OpenAI SDK."""

    def __init__(self):
        # Load config from environment
        self.api_key = os.environ.get("OPENROUTER_API_KEY")
        self.base_url = os.environ.get("OPENROUTER_BASE_URL", "https://openrouter.ai/api/v1")
        self.default_model = os.environ.get("OPENROUTER_MODEL", "x-ai/grok-4.1-fast:free")

        if not self.api_key:
            raise ValueError("OPENROUTER_API_KEY environment variable required")

        self.client = OpenAI(
            base_url=self.base_url,
            api_key=self.api_key,
            default_headers={
                "HTTP-Referer": "https://github.com/Cranot/deep-research",
                "X-Title": "Deep Research",
            },
        )

    @property
    def name(self) -> str:
        return "openrouter"

    async def generate(
        self,
        prompt: str,
        model: str,
        options: ProviderOptions | None = None,
    ) -> str:
        """Generate response using OpenRouter."""
        options = options or ProviderOptions()

        # Resolve model name
        model_id = OPENROUTER_MODELS.get(model, model)
        # If still not found, use default
        if "/" not in model_id:
            model_id = self.default_model

        # Build cache key including system prompt
        full_prompt = prompt
        if options.system_prompt:
            full_prompt = f"[SYSTEM]{options.system_prompt}[/SYSTEM]{prompt}"
        cache_key_model = f"openrouter:{model_id}"

        # Check cache first
        cached = get_cached(full_prompt, cache_key_model)
        if cached:
            _console.print("[dim cyan]  (cached)[/dim cyan]", end="")
            return cached

        # Build messages
        messages = []
        if options.system_prompt:
            messages.append({"role": "system", "content": options.system_prompt})
        messages.append({"role": "user", "content": prompt})

        # Call OpenRouter (limit tokens to stay within budget)
        response = self.client.chat.completions.create(
            model=model_id,
            messages=messages,
            max_tokens=8000,  # Limit to prevent 402 errors
        )

        result = response.choices[0].message.content or ""

        # Cache the result
        set_cached(full_prompt, cache_key_model, result)

        return result
