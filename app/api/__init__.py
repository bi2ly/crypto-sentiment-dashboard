"""
Crypto Sentiment Dashboard - API Clients

This package contains wrapper modules for external API integrations:

- coingecko.py: CoinGecko API for market data
- fear_greed.py: Alternative.me Fear & Greed Index
- whale_alert.py: Whale Alert API for large transactions
- reddit_client.py: Reddit API (PRAW) for social sentiment
- news_api.py: NewsAPI for crypto news

Each module implements rate limiting, caching, and error handling.
"""

__all__ = [
    'coingecko',
    'fear_greed',
    'whale_alert',
    'reddit_client',
    'news_api'
]
