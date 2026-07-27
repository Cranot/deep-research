"""
Tests for cache.py - response caching.
"""

import json
from unittest.mock import MagicMock, patch

import pytest

from deep_research.cache import (
    _get_cache_key,
    _load_cache,
    cache_stats,
    clear_cache,
    get_cached,
    set_cached,
)


class TestCacheKey:
    """Tests for cache key generation."""

    def test_same_input_same_key(self):
        """Same input should produce same key."""
        key1 = _get_cache_key("prompt", "model")
        key2 = _get_cache_key("prompt", "model")
        assert key1 == key2

    def test_different_prompt_different_key(self):
        """Different prompts should produce different keys."""
        key1 = _get_cache_key("prompt1", "model")
        key2 = _get_cache_key("prompt2", "model")
        assert key1 != key2

    def test_different_model_different_key(self):
        """Different models should produce different keys."""
        key1 = _get_cache_key("prompt", "model1")
        key2 = _get_cache_key("prompt", "model2")
        assert key1 != key2

    def test_key_is_short_hash(self):
        """Key should be a short hash."""
        key = _get_cache_key("prompt", "model")
        assert len(key) == 16
        assert all(c in "0123456789abcdef" for c in key)


class TestCacheOperations:
    """Tests for cache get/set operations."""

    @pytest.fixture
    def temp_cache(self, tmp_path):
        """Create a temporary cache directory."""
        cache_dir = tmp_path / "cache"
        cache_dir.mkdir()
        cache_file = cache_dir / "responses.json"

        # Mock the settings to use temp directory
        mock_settings = MagicMock()
        mock_settings.cache_enabled = True
        mock_settings.cache_dir = cache_dir

        with patch("deep_research.cache._get_cache_dir", return_value=cache_dir):
            with patch("deep_research.cache._is_cache_enabled", return_value=True):
                yield cache_file

    def test_set_and_get(self, temp_cache):
        """Set and retrieve a cached value."""
        set_cached("test prompt", "test-model", "test response")
        result = get_cached("test prompt", "test-model")
        assert result == "test response"

    def test_get_missing(self, temp_cache):
        """Get non-existent key returns None."""
        result = get_cached("nonexistent", "model")
        assert result is None

    def test_cache_disabled_get(self):
        """Get with cache disabled returns None."""
        with patch("deep_research.cache._is_cache_enabled", return_value=False):
            result = get_cached("prompt", "model")
            assert result is None

    def test_cache_disabled_set(self, tmp_path):
        """Set with cache disabled does nothing."""
        with patch("deep_research.cache._is_cache_enabled", return_value=False):
            set_cached("prompt", "model", "response")
            # Should not raise and not cache

    def test_clear_cache(self, temp_cache):
        """Clear cache removes all entries."""
        set_cached("prompt1", "model", "response1")
        set_cached("prompt2", "model", "response2")

        count = clear_cache()
        assert count == 2

        assert get_cached("prompt1", "model") is None
        assert get_cached("prompt2", "model") is None


class TestCacheStats:
    """Tests for cache statistics."""

    @pytest.fixture
    def temp_cache_with_data(self, tmp_path):
        """Create a temporary cache with some data."""
        cache_dir = tmp_path / "cache"
        cache_dir.mkdir()
        cache_file = cache_dir / "responses.json"

        # Create some cached data
        cache_data = {
            "key1": {"model": "opus", "response": "response1"},
            "key2": {"model": "haiku", "response": "response2"},
        }
        cache_file.write_text(json.dumps(cache_data))

        with patch("deep_research.cache._get_cache_dir", return_value=cache_dir):
            with patch("deep_research.cache._is_cache_enabled", return_value=True):
                yield cache_file

    def test_stats_with_data(self, temp_cache_with_data):
        """Stats should report correct entry count."""
        stats = cache_stats()
        assert stats["entries"] == 2
        assert stats["enabled"] is True
        assert stats["size_bytes"] > 0

    def test_stats_empty_cache(self, tmp_path):
        """Stats for empty cache."""
        cache_dir = tmp_path / "cache"
        cache_dir.mkdir()

        with patch("deep_research.cache._get_cache_dir", return_value=cache_dir):
            with patch("deep_research.cache._is_cache_enabled", return_value=True):
                stats = cache_stats()
                assert stats["entries"] == 0
                assert stats["size_bytes"] == 0


class TestCachePersistence:
    """Tests for cache file persistence."""

    def test_cache_survives_reload(self, tmp_path):
        """Cache should persist across function calls."""
        cache_dir = tmp_path / "cache"
        cache_dir.mkdir()

        with patch("deep_research.cache._get_cache_dir", return_value=cache_dir):
            with patch("deep_research.cache._is_cache_enabled", return_value=True):
                # Set a value
                set_cached("persistent", "model", "I should persist")

                # Clear any in-memory state (simulated)
                # The file should still contain the data

                # Get the value
                result = get_cached("persistent", "model")
                assert result == "I should persist"

    def test_corrupted_cache_handled(self, tmp_path):
        """Corrupted cache file should not crash."""
        cache_dir = tmp_path / "cache"
        cache_dir.mkdir()
        cache_file = cache_dir / "responses.json"

        # Write invalid JSON
        cache_file.write_text("{invalid json")

        with patch("deep_research.cache._get_cache_dir", return_value=cache_dir):
            with patch("deep_research.cache._is_cache_enabled", return_value=True):
                # Should return empty dict, not crash
                cache = _load_cache()
                assert cache == {}

                # Should be able to get (returns None)
                result = get_cached("test", "model")
                assert result is None


class TestCacheContentStorage:
    """Tests for what gets stored in cache."""

    @pytest.fixture
    def temp_cache(self, tmp_path):
        """Create a temporary cache directory."""
        cache_dir = tmp_path / "cache"
        cache_dir.mkdir()

        with patch("deep_research.cache._get_cache_dir", return_value=cache_dir):
            with patch("deep_research.cache._is_cache_enabled", return_value=True):
                yield cache_dir / "responses.json"

    def test_stores_model_info(self, temp_cache):
        """Cache should store model information."""
        set_cached("test prompt", "claude:opus", "response")

        # Read the raw cache file
        cache_data = json.loads(temp_cache.read_text())
        entry = list(cache_data.values())[0]

        assert entry["model"] == "claude:opus"
        assert entry["response"] == "response"

    def test_stores_prompt_preview(self, temp_cache):
        """Long prompts should be truncated in preview."""
        long_prompt = "x" * 200
        set_cached(long_prompt, "model", "response")

        cache_data = json.loads(temp_cache.read_text())
        entry = list(cache_data.values())[0]

        assert "prompt_preview" in entry
        assert len(entry["prompt_preview"]) <= 103  # 100 + "..."
        assert entry["prompt_preview"].endswith("...")

    def test_short_prompt_not_truncated(self, temp_cache):
        """Short prompts should not be truncated."""
        short_prompt = "short"
        set_cached(short_prompt, "model", "response")

        cache_data = json.loads(temp_cache.read_text())
        entry = list(cache_data.values())[0]

        assert entry["prompt_preview"] == "short"
