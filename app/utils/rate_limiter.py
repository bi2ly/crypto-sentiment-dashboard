"""
Crypto Sentiment Dashboard - Rate Limiting Utilities

Token bucket algorithm for API rate limiting.
"""

import threading
import time
from typing import Dict, Optional


class RateLimiter:
    """
    Token bucket rate limiter.

    Allows bursts up to bucket capacity while maintaining
    average rate over time.

    Usage:
        limiter = RateLimiter(rate=30, per=60)  # 30 requests per 60 seconds
        if limiter.acquire():
            make_api_call()
    """

    def __init__(self, rate: int, per: int = 60, burst: Optional[int] = None):
        """
        Initialize rate limiter.

        Args:
            rate: Number of allowed requests
            per: Time period in seconds
            burst: Maximum burst size (defaults to rate)
        """
        self.rate = rate
        self.per = per
        self.burst = burst or rate
        self.tokens = float(self.burst)
        self.last_update = time.time()
        self._lock = threading.Lock()

    def _add_tokens(self) -> None:
        """Add tokens based on elapsed time."""
        now = time.time()
        elapsed = now - self.last_update
        self.tokens = min(self.burst, self.tokens + elapsed * (self.rate / self.per))
        self.last_update = now

    def acquire(self, tokens: int = 1, blocking: bool = True, timeout: Optional[float] = None) -> bool:
        """
        Acquire tokens from the bucket.

        Args:
            tokens: Number of tokens to acquire
            blocking: If True, wait until tokens are available
            timeout: Maximum time to wait (only if blocking=True)

        Returns:
            True if tokens were acquired, False otherwise
        """
        start_time = time.time()

        while True:
            with self._lock:
                self._add_tokens()

                if self.tokens >= tokens:
                    self.tokens -= tokens
                    return True

                if not blocking:
                    return False

            # Calculate wait time
            wait_time = (tokens - self.tokens) * (self.per / self.rate)

            # Check timeout
            if timeout is not None:
                elapsed = time.time() - start_time
                if elapsed + wait_time > timeout:
                    return False
                wait_time = min(wait_time, timeout - elapsed)

            time.sleep(min(wait_time, 0.1))  # Sleep in small increments

    def wait_time(self) -> float:
        """
        Get estimated wait time for next token.

        Returns:
            Seconds until a token is available (0 if available now)
        """
        with self._lock:
            self._add_tokens()
            if self.tokens >= 1:
                return 0.0
            return (1 - self.tokens) * (self.per / self.rate)

    @property
    def available_tokens(self) -> float:
        """Get current number of available tokens."""
        with self._lock:
            self._add_tokens()
            return self.tokens


class MultiRateLimiter:
    """
    Manages rate limiters for multiple APIs.

    Usage:
        limiters = MultiRateLimiter()
        limiters.add('coingecko', rate=30, per=60)
        limiters.add('newsapi', rate=100, per=3600)

        if limiters.acquire('coingecko'):
            call_coingecko_api()
    """

    def __init__(self):
        self._limiters: Dict[str, RateLimiter] = {}
        self._lock = threading.Lock()

    def add(self, name: str, rate: int, per: int = 60, burst: Optional[int] = None) -> None:
        """
        Add a new rate limiter.

        Args:
            name: Identifier for this limiter
            rate: Number of allowed requests
            per: Time period in seconds
            burst: Maximum burst size
        """
        with self._lock:
            self._limiters[name] = RateLimiter(rate, per, burst)

    def get(self, name: str) -> Optional[RateLimiter]:
        """Get a rate limiter by name."""
        return self._limiters.get(name)

    def acquire(self, name: str, tokens: int = 1, blocking: bool = True, timeout: Optional[float] = None) -> bool:
        """
        Acquire tokens from a named limiter.

        Args:
            name: Limiter identifier
            tokens: Number of tokens to acquire
            blocking: If True, wait until tokens are available
            timeout: Maximum time to wait

        Returns:
            True if tokens were acquired, False otherwise

        Raises:
            KeyError: If limiter name not found
        """
        limiter = self._limiters.get(name)
        if limiter is None:
            raise KeyError(f"Rate limiter '{name}' not found")
        return limiter.acquire(tokens, blocking, timeout)

    def wait_time(self, name: str) -> float:
        """Get wait time for a named limiter."""
        limiter = self._limiters.get(name)
        if limiter is None:
            raise KeyError(f"Rate limiter '{name}' not found")
        return limiter.wait_time()

    def stats(self) -> Dict[str, dict]:
        """Get statistics for all limiters."""
        return {
            name: {
                'available_tokens': limiter.available_tokens,
                'rate': limiter.rate,
                'per': limiter.per,
                'burst': limiter.burst
            }
            for name, limiter in self._limiters.items()
        }


# Global rate limiters instance
_rate_limiters = MultiRateLimiter()


def get_rate_limiters() -> MultiRateLimiter:
    """Get the global rate limiters instance."""
    return _rate_limiters


def setup_default_limiters() -> None:
    """Set up rate limiters for known APIs."""
    _rate_limiters.add('coingecko', rate=30, per=60)  # 30/min
    _rate_limiters.add('fear_greed', rate=10, per=60)  # 10/min
    _rate_limiters.add('whale_alert', rate=10, per=60)  # 10/min (free tier)
    _rate_limiters.add('newsapi', rate=100, per=3600)  # 100/hour
    _rate_limiters.add('reddit', rate=60, per=60)  # 60/min
