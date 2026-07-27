"""
Kimi provider (Azure AI Services).

Uses the OpenAI SDK with Azure AI Services endpoint.
"""

import os

from openai import OpenAI
from rich.console import Console

from ..cache import get_cached, set_cached
from .base import Provider, ProviderOptions

_console = Console(stderr=True)


# Model name mappings
KIMI_MODELS = {
    "kimi": "Kimi-K2-Thinking",
    "kimi-k2": "Kimi-K2-Thinking",
    "kimi-k2-thinking": "Kimi-K2-Thinking",
    "Kimi-K2-Thinking": "Kimi-K2-Thinking",
}


class KimiProvider(Provider):
    """Kimi provider using Azure AI Services."""

    def __init__(self):
        # Load config from environment. There is deliberately no default
        # endpoint: bring your own Azure AI Services resource.
        self.endpoint = os.environ.get("KIMI_ENDPOINT")
        self.api_key = os.environ.get("KIMI_API_KEY")
        self.default_model = os.environ.get("KIMI_MODEL", "Kimi-K2-Thinking")

        if not self.endpoint:
            raise ValueError(
                "KIMI_ENDPOINT environment variable required "
                "(e.g. https://<your-resource>.services.ai.azure.com/openai/v1/)"
            )
        if not self.api_key:
            raise ValueError("KIMI_API_KEY environment variable required")

        self.client = OpenAI(
            base_url=self.endpoint,
            api_key=self.api_key,
        )

    @property
    def name(self) -> str:
        return "kimi"

    async def generate(
        self,
        prompt: str,
        model: str,
        options: ProviderOptions | None = None,
    ) -> str:
        """Generate response using Kimi."""
        options = options or ProviderOptions()

        # Resolve model name
        model_id = KIMI_MODELS.get(model, self.default_model)

        # Build cache key including system prompt
        full_prompt = prompt
        if options.system_prompt:
            full_prompt = f"[SYSTEM]{options.system_prompt}[/SYSTEM]{prompt}"
        cache_key_model = f"kimi:{model_id}"

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

        # Call Kimi
        response = self.client.chat.completions.create(
            model=model_id,
            messages=messages,
        )

        result = response.choices[0].message.content or ""

        # Cache the result
        set_cached(full_prompt, cache_key_model, result)

        return result
