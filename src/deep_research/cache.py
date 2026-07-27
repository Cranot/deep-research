"""
Response caching for LLM calls.

Avoids repeated API calls for identical prompts.
Uses a simple JSON file cache with prompt hashing.
"""

import hashlib
import json
from pathlib import Path
from typing import Any


def _get_cache_dir() -> Path:
    """Get cache directory from settings."""
    try:
        from .settings import settings

        return settings.cache_dir
    except ImportError:
        return Path.home() / ".cache" / "deep-research"


def _is_cache_enabled() -> bool:
    """Check if caching is enabled in settings."""
    try:
        from .settings import settings

        return settings.cache_enabled
    except ImportError:
        return True


def _get_cache_file() -> Path:
    """Get cache file path."""
    return _get_cache_dir() / "responses.json"


def _get_cache_key(prompt: str, model: str) -> str:
    """Generate a cache key from prompt and model."""
    content = f"{model}:{prompt}"
    return hashlib.sha256(content.encode()).hexdigest()[:16]


def _load_cache() -> dict[str, Any]:
    """Load cache from disk."""
    cache_file = _get_cache_file()
    if not cache_file.exists():
        return {}
    try:
        with open(cache_file, "r", encoding="utf-8") as f:
            return json.load(f)
    except (json.JSONDecodeError, IOError):
        return {}


def _save_cache(cache: dict[str, Any]) -> None:
    """Save cache to disk."""
    cache_dir = _get_cache_dir()
    cache_file = _get_cache_file()
    cache_dir.mkdir(parents=True, exist_ok=True)
    with open(cache_file, "w", encoding="utf-8") as f:
        json.dump(cache, f, indent=2, ensure_ascii=False)


def get_cached(prompt: str, model: str) -> str | None:
    """Get cached response if available."""
    if not _is_cache_enabled():
        return None
    cache = _load_cache()
    key = _get_cache_key(prompt, model)
    entry = cache.get(key)
    if entry:
        return entry.get("response")
    return None


def set_cached(prompt: str, model: str, response: str) -> None:
    """Cache a response."""
    if not _is_cache_enabled():
        return
    cache = _load_cache()
    key = _get_cache_key(prompt, model)
    cache[key] = {
        "model": model,
        "prompt_preview": prompt[:100] + "..." if len(prompt) > 100 else prompt,
        "response": response,
    }
    _save_cache(cache)


def clear_cache() -> int:
    """Clear all cached responses. Returns count of cleared entries."""
    cache_file = _get_cache_file()
    cache = _load_cache()
    count = len(cache)
    if cache_file.exists():
        cache_file.unlink()
    return count


def cache_stats() -> dict[str, Any]:
    """Get cache statistics."""
    cache_file = _get_cache_file()
    cache = _load_cache()
    return {
        "entries": len(cache),
        "file": str(cache_file),
        "size_bytes": cache_file.stat().st_size if cache_file.exists() else 0,
        "enabled": _is_cache_enabled(),
    }
