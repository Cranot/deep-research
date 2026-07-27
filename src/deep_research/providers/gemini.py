"""
Gemini provider using the Gemini CLI (supports OAuth).

Uses subprocess to call the gemini CLI, which supports OAuth authentication.
This matches the bash script behavior.
"""

import asyncio
import shutil
import subprocess
import sys

from rich.console import Console

from ..cache import get_cached, set_cached
from .base import Provider, ProviderOptions

_console = Console(stderr=True)


def _find_gemini_cmd() -> str:
    """Find the gemini command, handling Windows .cmd extension."""
    # Try gemini directly
    gemini = shutil.which("gemini")
    if gemini:
        return gemini

    # On Windows, try gemini.cmd
    if sys.platform == "win32":
        gemini_cmd = shutil.which("gemini.cmd")
        if gemini_cmd:
            return gemini_cmd

    # Fallback to just "gemini" and hope it's in PATH
    return "gemini"


# Model name mappings
GEMINI_MODELS = {
    "flash": "gemini-3-flash-preview",
    "pro": "gemini-3-pro-preview",
    "gemini-3-flash-preview": "gemini-3-flash-preview",
    "gemini-3-pro-preview": "gemini-3-pro-preview",
    # Legacy aliases
    "gemini-2.5-flash": "gemini-2.5-flash",
    "gemini-2.5-pro": "gemini-2.5-pro",
}


class GeminiProvider(Provider):
    """Gemini provider using the Gemini CLI (OAuth supported)."""

    @property
    def name(self) -> str:
        return "gemini"

    async def generate(
        self,
        prompt: str,
        model: str,
        options: ProviderOptions | None = None,
    ) -> str:
        """Generate response using Gemini CLI."""
        options = options or ProviderOptions()

        # Resolve model name
        model_name = GEMINI_MODELS.get(model, model)

        # Gemini CLI doesn't have system prompt flag - embed in question
        if options.system_prompt:
            full_prompt = f"""INSTRUCTIONS:
{options.system_prompt}

QUESTION:
{prompt}"""
        else:
            full_prompt = prompt

        # Check cache first (key by full model name)
        cache_key_model = f"gemini:{model_name}"
        cached = get_cached(full_prompt, cache_key_model)
        if cached:
            _console.print("[dim cyan]  (cached)[/dim cyan]", end="")
            return cached

        # Run gemini CLI in subprocess
        # Use asyncio.to_thread to not block the event loop
        result = await asyncio.to_thread(
            self._call_gemini_cli,
            full_prompt,
            model_name,
        )

        # Cache the result
        set_cached(full_prompt, cache_key_model, result)

        return result

    def _call_gemini_cli(self, prompt: str, model: str) -> str:
        """Call gemini CLI synchronously."""
        gemini_cmd = _find_gemini_cmd()

        # Always use stdin for prompts to avoid escaping issues
        # This works on all platforms and handles any prompt content
        result = subprocess.run(
            [gemini_cmd, "-m", model, "-o", "text"],
            input=prompt,
            capture_output=True,
            text=True,
            encoding="utf-8",
        )

        if result.returncode != 0:
            error = result.stderr or result.stdout or "Unknown error"
            raise RuntimeError(f"Gemini CLI failed: {error}")

        # Filter out startup debug messages (lines starting with [STARTUP] or "Loaded cached")
        output_lines = []
        for line in result.stdout.split("\n"):
            if line.startswith("[STARTUP]") or line.startswith("Loaded cached"):
                continue
            output_lines.append(line)

        return "\n".join(output_lines).strip()
