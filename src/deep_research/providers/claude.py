"""
Claude provider using the claude CLI (subscription-based).

Uses the `claude` command which leverages your Claude subscription,
not API credits.
"""

import asyncio
import shutil
import sys
import tempfile
from datetime import datetime
from pathlib import Path

from rich.console import Console

from ..cache import get_cached, set_cached
from ..exceptions import (
    APIResponseError,
    APITimeoutError,
    EmptyResponseError,
)
from ..logging import get_logger
from .base import Provider, ProviderOptions

_console = Console(stderr=True)


# Model name mappings
CLAUDE_MODELS = {
    "opus": "opus",
    "sonnet": "sonnet",
    "haiku": "haiku",
}

# Timeout for Claude CLI calls (seconds)
DEFAULT_TIMEOUT = 300


class ClaudeProvider(Provider):
    """Claude provider using the claude CLI (subscription-based)."""

    def __init__(self, timeout: float = DEFAULT_TIMEOUT):
        self.timeout = timeout

    @property
    def name(self) -> str:
        return "claude"

    async def generate(
        self,
        prompt: str,
        model: str,
        options: ProviderOptions | None = None,
    ) -> str:
        """Generate response using claude CLI."""
        options = options or ProviderOptions()
        logger = get_logger()
        start_time = datetime.now()

        # Build cache key including system prompt
        full_prompt = prompt
        if options.system_prompt:
            full_prompt = f"[SYSTEM]{options.system_prompt}[/SYSTEM]{prompt}"
        cache_key_model = f"claude:{model}"

        # Check cache first
        cached = get_cached(full_prompt, cache_key_model)
        if cached:
            logger.api_call(
                provider="claude",
                model=model,
                operation="generate",
                prompt=prompt,
                response=cached,
                cached=True,
            )
            return cached

        # Resolve model name
        model_name = CLAUDE_MODELS.get(model, model)

        # Build command - use stdin for prompt to avoid quoting issues
        cmd = [
            "claude",
            "-p",  # Print mode
            "--model",
            model_name,
            "--max-turns",
            "1",
            "--tools",
            "",  # Disable all tools
        ]

        # Handle system prompt - always use file to avoid quoting issues
        prompt_file = None
        if options.system_prompt:
            with tempfile.NamedTemporaryFile(
                mode="w",
                suffix=".txt",
                delete=False,
                encoding="utf-8",
            ) as f:
                f.write(options.system_prompt)
                prompt_file = f.name
            cmd.extend(["--system-prompt-file", prompt_file])

        # Add web search tools if enabled
        if options.web_search:
            cmd.extend(["--allowedTools", "WebSearch,WebFetch"])

        # Create a clean temp directory to avoid picking up local CLAUDE.md
        clean_dir = tempfile.mkdtemp(prefix="deep-research-")

        try:
            # Run claude CLI from clean directory, pipe prompt via stdin
            if sys.platform == "win32":
                # On Windows, use shell with proper quoting
                import subprocess

                shell_cmd = subprocess.list2cmdline(cmd)
                process = await asyncio.create_subprocess_shell(
                    shell_cmd,
                    stdin=asyncio.subprocess.PIPE,
                    stdout=asyncio.subprocess.PIPE,
                    stderr=asyncio.subprocess.PIPE,
                    cwd=clean_dir,
                )
            else:
                process = await asyncio.create_subprocess_exec(
                    *cmd,
                    stdin=asyncio.subprocess.PIPE,
                    stdout=asyncio.subprocess.PIPE,
                    stderr=asyncio.subprocess.PIPE,
                    cwd=clean_dir,
                )

            try:
                # Send prompt via stdin
                stdout, stderr = await asyncio.wait_for(
                    process.communicate(input=prompt.encode("utf-8")),
                    timeout=self.timeout,
                )
            except asyncio.TimeoutError:
                process.kill()
                await process.wait()
                duration_ms = int((datetime.now() - start_time).total_seconds() * 1000)
                logger.api_call(
                    provider="claude",
                    model=model,
                    operation="generate",
                    prompt=prompt,
                    duration_ms=duration_ms,
                    error="Timeout",
                )
                raise APITimeoutError("claude", model, self.timeout)

            result = stdout.decode("utf-8", errors="replace").strip()
            stderr_text = stderr.decode("utf-8", errors="replace").strip()

            duration_ms = int((datetime.now() - start_time).total_seconds() * 1000)

            # Check for errors
            if process.returncode != 0:
                error_msg = stderr_text or f"CLI returned exit code {process.returncode}"
                logger.api_call(
                    provider="claude",
                    model=model,
                    operation="generate",
                    prompt=prompt,
                    duration_ms=duration_ms,
                    error=error_msg,
                )
                raise APIResponseError(
                    error_msg,
                    provider="claude",
                    model=model,
                )

            # Check for empty response
            if not result:
                logger.api_call(
                    provider="claude",
                    model=model,
                    operation="generate",
                    prompt=prompt,
                    duration_ms=duration_ms,
                    error="Empty response",
                )
                raise EmptyResponseError("claude", model, prompt)

            # Log the successful call
            logger.api_call(
                provider="claude",
                model=model,
                operation="generate",
                prompt=prompt,
                response=result,
                duration_ms=duration_ms,
            )

            # Cache the result
            set_cached(full_prompt, cache_key_model, result)

            return result

        except (FileNotFoundError, PermissionError):
            raise APIResponseError(
                "Claude CLI not found. Install it with: npm install -g @anthropic-ai/claude-code",
                provider="claude",
                model=model,
            )

        finally:
            # Clean up temp directory and prompt file
            shutil.rmtree(clean_dir, ignore_errors=True)
            if prompt_file:
                Path(prompt_file).unlink(missing_ok=True)
