"""
Crypto Sentiment Dashboard - Utility Modules

This package contains utility functions and classes:

- cache.py: Caching utilities for API responses
- rate_limiter.py: Rate limiting for API calls
- sentiment.py: Sentiment analysis (TextBlob, VADER)

These utilities are used across the application to ensure
efficient API usage and consistent data processing.
"""

__all__ = [
    'cache',
    'rate_limiter',
    'sentiment'
]
