"""
Azure OpenAI provider (GPT-5 Mini).

Uses the OpenAI Python SDK with Azure configuration.
"""

import os

from openai import AzureOpenAI
from rich.console import Console

from ..cache import get_cached, set_cached
from .base import Provider, ProviderOptions

_console = Console(stderr=True)


# Model name mappings (alias -> deployment name)
OPENAI_MODELS = {
    "gpt5-mini": "gpt-5-mini",
    "gpt5": "gpt-5-mini",
    "mini": "gpt-5-mini",
    "gpt-5-mini": "gpt-5-mini",
}


class OpenAIProvider(Provider):
    """Azure OpenAI provider using the OpenAI SDK."""

    def __init__(self):
        # Load config from environment. There is deliberately no default
        # endpoint: bring your own Azure OpenAI resource.
        self.endpoint = os.environ.get("GPT5_MINI_ENDPOINT")
        self.api_key = os.environ.get("GPT5_MINI_API_KEY")
        self.deployment = os.environ.get("GPT5_MINI_DEPLOYMENT", "gpt-5-mini")
        self.api_version = os.environ.get("GPT5_MINI_API_VERSION", "2024-02-01")

        if not self.endpoint:
            raise ValueError(
                "GPT5_MINI_ENDPOINT environment variable required "
                "(e.g. https://<your-resource>.openai.azure.com)"
            )
        if not self.api_key:
            raise ValueError("GPT5_MINI_API_KEY environment variable required")

        self.client = AzureOpenAI(
            azure_endpoint=self.endpoint,
            api_key=self.api_key,
            api_version=self.api_version,
        )

    @property
    def name(self) -> str:
        return "openai"

    async def generate(
        self,
        prompt: str,
        model: str,
        options: ProviderOptions | None = None,
    ) -> str:
        """Generate response using Azure OpenAI."""
        options = options or ProviderOptions()

        # Resolve model name to deployment
        deployment = OPENAI_MODELS.get(model, self.deployment)

        # Build cache key including system prompt
        full_prompt = prompt
        if options.system_prompt:
            full_prompt = f"[SYSTEM]{options.system_prompt}[/SYSTEM]{prompt}"
        cache_key_model = f"openai:{deployment}"

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

        # Call Azure OpenAI (temperature=1.0 required for GPT-5)
        response = self.client.chat.completions.create(
            model=deployment,
            messages=messages,
            temperature=1.0,
        )

        result = response.choices[0].message.content or ""

        # Cache the result
        set_cached(full_prompt, cache_key_model, result)

        return result
