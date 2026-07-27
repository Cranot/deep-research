"""
Central settings for deep-research.

Supports:
- Environment variables (DEEP_RESEARCH_*)
- Sensible defaults
- Runtime overrides

Usage:
    from deep_research.settings import settings

    model = settings.default_orchestrator
    cache_enabled = settings.cache_enabled
"""

import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any


@dataclass
class Settings:
    """Global settings with environment variable support."""

    # Model defaults
    default_orchestrator: str = "opus"
    default_researcher: str = "haiku"
    default_provider: str = "claude"

    # Recursion limits
    max_depth: int = 5
    max_parallel: int = 10

    # Cache settings
    cache_enabled: bool = True
    cache_dir: Path = field(default_factory=lambda: Path.home() / ".cache" / "deep-research")
    cache_ttl_hours: int = 24 * 7  # 1 week

    # Output settings
    output_base_dir: Path = field(default_factory=lambda: Path("reports"))
    verbose: bool = False

    # Provider settings
    claude_max_turns: int = 1
    gemini_timeout: int = 120

    # Perspective expansion settings
    perspective_models: str = "opus,gemini:flash,kimi:kimi"  # Comma-separated
    perspective_picker: str = "sonnet"
    perspective_depth: int = 1  # How many levels of recursive perspective expansion
    perspective_min_count: int = 5  # Minimum perspectives to select
    perspective_max_count: int = 8  # Maximum perspectives to select
    perspective_blind_spot_check: bool = True  # Run blind spot detection
    perspective_cache_enabled: bool = True  # Cache perspectives for similar questions

    # Model-perspective matching (JSON-like string for env var compatibility)
    # Format: "perspective_type:model,perspective_type:model"
    perspective_model_matching: str = ""  # Empty means auto-assign

    def __post_init__(self):
        """Load from environment variables."""
        self._load_from_env()

    def _load_from_env(self):
        """Override defaults from DEEP_RESEARCH_* environment variables."""
        env_map = {
            "DEEP_RESEARCH_ORCHESTRATOR": ("default_orchestrator", str),
            "DEEP_RESEARCH_RESEARCHER": ("default_researcher", str),
            "DEEP_RESEARCH_PROVIDER": ("default_provider", str),
            "DEEP_RESEARCH_MAX_DEPTH": ("max_depth", int),
            "DEEP_RESEARCH_MAX_PARALLEL": ("max_parallel", int),
            "DEEP_RESEARCH_CACHE_ENABLED": ("cache_enabled", lambda x: x.lower() == "true"),
            "DEEP_RESEARCH_CACHE_DIR": ("cache_dir", Path),
            "DEEP_RESEARCH_OUTPUT_DIR": ("output_base_dir", Path),
            "DEEP_RESEARCH_VERBOSE": ("verbose", lambda x: x.lower() == "true"),
            # Perspective settings
            "DEEP_RESEARCH_PERSPECTIVE_MODELS": ("perspective_models", str),
            "DEEP_RESEARCH_PERSPECTIVE_PICKER": ("perspective_picker", str),
            "DEEP_RESEARCH_PERSPECTIVE_DEPTH": ("perspective_depth", int),
            "DEEP_RESEARCH_PERSPECTIVE_MIN_COUNT": ("perspective_min_count", int),
            "DEEP_RESEARCH_PERSPECTIVE_MAX_COUNT": ("perspective_max_count", int),
            "DEEP_RESEARCH_PERSPECTIVE_BLIND_SPOT": (
                "perspective_blind_spot_check",
                lambda x: x.lower() == "true",
            ),
            "DEEP_RESEARCH_PERSPECTIVE_CACHE": (
                "perspective_cache_enabled",
                lambda x: x.lower() == "true",
            ),
            "DEEP_RESEARCH_PERSPECTIVE_MATCHING": ("perspective_model_matching", str),
        }

        for env_var, (attr, converter) in env_map.items():
            value = os.environ.get(env_var)
            if value is not None:
                try:
                    setattr(self, attr, converter(value))
                except (ValueError, TypeError):
                    pass  # Keep default if conversion fails

    def get_perspective_models_list(self) -> list[str]:
        """Get perspective models as a list."""
        return [m.strip() for m in self.perspective_models.split(",") if m.strip()]

    def get_perspective_model_matching(self) -> dict[str, str]:
        """Parse perspective model matching into a dictionary."""
        if not self.perspective_model_matching:
            return {}
        result = {}
        for pair in self.perspective_model_matching.split(","):
            if ":" in pair:
                perspective_type, model = pair.split(":", 1)
                result[perspective_type.strip().lower()] = model.strip()
        return result

    def to_dict(self) -> dict[str, Any]:
        """Export settings as dictionary."""
        return {
            "default_orchestrator": self.default_orchestrator,
            "default_researcher": self.default_researcher,
            "default_provider": self.default_provider,
            "max_depth": self.max_depth,
            "max_parallel": self.max_parallel,
            "cache_enabled": self.cache_enabled,
            "cache_dir": str(self.cache_dir),
            "cache_ttl_hours": self.cache_ttl_hours,
            "output_base_dir": str(self.output_base_dir),
            "verbose": self.verbose,
            # Perspective settings
            "perspective_models": self.perspective_models,
            "perspective_picker": self.perspective_picker,
            "perspective_depth": self.perspective_depth,
            "perspective_min_count": self.perspective_min_count,
            "perspective_max_count": self.perspective_max_count,
            "perspective_blind_spot_check": self.perspective_blind_spot_check,
            "perspective_cache_enabled": self.perspective_cache_enabled,
        }


# Singleton instance
settings = Settings()


def get_settings() -> Settings:
    """Get global settings instance."""
    return settings


def configure(**kwargs) -> None:
    """Override settings at runtime."""
    global settings
    for key, value in kwargs.items():
        if hasattr(settings, key):
            setattr(settings, key, value)
