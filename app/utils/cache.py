"""
Crypto Sentiment Dashboard - Caching Utilities

In-memory cache with TTL support for API response caching.
"""

import functools
import hashlib
import json
import threading
import time
from typing import Any, Callable, Optional


class CacheEntry:
    """Single cache entry with value and expiration time."""

    def __init__(self, value: Any, ttl: int):
        self.value = value
        self.expires_at = time.time() + ttl

    def is_expired(self) -> bool:
        return time.time() > self.expires_at


class Cache:
    """
    Thread-safe in-memory cache with TTL support.

    Usage:
        cache = Cache()
        cache.set('key', 'value', ttl=300)
        value = cache.get('key')
    """

    def __init__(self, default_ttl: int = 300):
        """
        Initialize cache.

        Args:
            default_ttl: Default time-to-live in seconds (default: 5 minutes)
        """
        self._cache: dict[str, CacheEntry] = {}
        self._lock = threading.Lock()
        self._default_ttl = default_ttl

    def get(self, key: str) -> Optional[Any]:
        """
        Get value from cache.

        Args:
            key: Cache key

        Returns:
            Cached value or None if not found/expired
        """
        with self._lock:
            entry = self._cache.get(key)
            if entry is None:
                return None
            if entry.is_expired():
                del self._cache[key]
                return None
            return entry.value

    def set(self, key: str, value: Any, ttl: Optional[int] = None) -> None:
        """
        Set value in cache.

        Args:
            key: Cache key
            value: Value to cache
            ttl: Time-to-live in seconds (uses default if not specified)
        """
        with self._lock:
            self._cache[key] = CacheEntry(value, ttl or self._default_ttl)

    def delete(self, key: str) -> bool:
        """
        Delete key from cache.

        Args:
            key: Cache key

        Returns:
            True if key was deleted, False if not found
        """
        with self._lock:
            if key in self._cache:
                del self._cache[key]
                return True
            return False

    def clear(self) -> None:
        """Clear all cached values."""
        with self._lock:
            self._cache.clear()

    def cleanup(self) -> int:
        """
        Remove all expired entries.

        Returns:
            Number of entries removed
        """
        with self._lock:
            expired = [k for k, v in self._cache.items() if v.is_expired()]
            for key in expired:
                del self._cache[key]
            return len(expired)

    def stats(self) -> dict:
        """Get cache statistics."""
        with self._lock:
            valid = sum(1 for v in self._cache.values() if not v.is_expired())
            return {
                'total_entries': len(self._cache),
                'valid_entries': valid,
                'expired_entries': len(self._cache) - valid
            }


# Global cache instance
_cache = Cache()


def get_cache() -> Cache:
    """Get the global cache instance."""
    return _cache


def cached(ttl: int = 300, key_prefix: str = ''):
    """
    Decorator for caching function results.

    Args:
        ttl: Time-to-live in seconds
        key_prefix: Optional prefix for cache key

    Usage:
        @cached(ttl=300, key_prefix='coingecko')
        def get_prices(coins):
            return api_call(coins)
    """
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            # Generate cache key from function name and arguments
            key_data = {
                'func': func.__name__,
                'args': args,
                'kwargs': kwargs
            }
            key_hash = hashlib.md5(
                json.dumps(key_data, sort_keys=True, default=str).encode()
            ).hexdigest()
            cache_key = f"{key_prefix}:{key_hash}" if key_prefix else key_hash

            # Check cache
            cached_value = _cache.get(cache_key)
            if cached_value is not None:
                return cached_value

            # Call function and cache result
            result = func(*args, **kwargs)
            if result is not None:
                _cache.set(cache_key, result, ttl)
            return result

        # Add method to clear this function's cache
        wrapper.clear_cache = lambda: _cache.clear()
        return wrapper

    return decorator
