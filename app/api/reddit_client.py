"""
Crypto Sentiment Dashboard - Reddit API Client

Sentiment analysis from crypto-related subreddits using PRAW.
"""

import logging
import os
from datetime import datetime
from typing import Dict, List, Optional

from app.utils.cache import cached, get_cache
from app.utils.rate_limiter import get_rate_limiters, setup_default_limiters
from app.utils.sentiment import get_analyzer

logger = logging.getLogger(__name__)

# Ensure rate limiters are set up
setup_default_limiters()

# Try to import PRAW
try:
    import praw
    PRAW_AVAILABLE = True
except ImportError:
    PRAW_AVAILABLE = False
    logger.warning("PRAW not installed. Reddit functionality will be limited.")


class RedditClient:
    """
    Reddit client for crypto sentiment analysis.

    Uses PRAW (Python Reddit API Wrapper) to fetch posts and comments
    from crypto-related subreddits.
    """

    # Default subreddits to monitor
    DEFAULT_SUBREDDITS = [
        'CryptoCurrency',
        'Bitcoin',
        'ethereum',
        'CryptoMoonShots',
        'altcoin',
        'defi'
    ]

    # Coin name/symbol mappings for detection
    COIN_ALIASES = {
        'bitcoin': ['btc', 'bitcoin', 'btfd'],
        'ethereum': ['eth', 'ethereum', 'ether'],
        'solana': ['sol', 'solana'],
        'cardano': ['ada', 'cardano'],
        'dogecoin': ['doge', 'dogecoin'],
        'ripple': ['xrp', 'ripple'],
        'polkadot': ['dot', 'polkadot'],
        'chainlink': ['link', 'chainlink'],
        'binancecoin': ['bnb', 'binance'],
        'avalanche': ['avax', 'avalanche']
    }

    def __init__(
        self,
        client_id: Optional[str] = None,
        client_secret: Optional[str] = None,
        user_agent: Optional[str] = None
    ):
        """
        Initialize Reddit client.

        Args:
            client_id: Reddit API client ID
            client_secret: Reddit API client secret
            user_agent: User agent string for API requests
        """
        self.client_id = client_id or os.getenv('REDDIT_CLIENT_ID')
        self.client_secret = client_secret or os.getenv('REDDIT_CLIENT_SECRET')
        self.user_agent = user_agent or os.getenv('REDDIT_USER_AGENT', 'crypto-sentiment-dashboard:v1.0')

        self._reddit = None
        self._rate_limiters = get_rate_limiters()
        self._cache = get_cache()
        self._sentiment_analyzer = get_analyzer()

        if PRAW_AVAILABLE and self.client_id and self.client_secret:
            try:
                self._reddit = praw.Reddit(
                    client_id=self.client_id,
                    client_secret=self.client_secret,
                    user_agent=self.user_agent
                )
                logger.info("Reddit client initialized successfully")
            except Exception as e:
                logger.error(f"Failed to initialize Reddit client: {e}")

    @property
    def is_configured(self) -> bool:
        """Check if Reddit client is properly configured."""
        return self._reddit is not None

    @cached(ttl=1800, key_prefix='reddit_sentiment')  # 30 minute cache
    def get_subreddit_sentiment(
        self,
        subreddit: str,
        coin_id: Optional[str] = None,
        limit: int = 50
    ) -> Optional[Dict]:
        """
        Analyze sentiment from a subreddit.

        Args:
            subreddit: Subreddit name (without r/)
            coin_id: Filter posts mentioning specific coin
            limit: Number of posts to analyze

        Returns:
            Sentiment analysis results or None on failure
        """
        if not self.is_configured:
            logger.warning("Reddit client not configured")
            return self._get_mock_sentiment(subreddit, coin_id)

        # Rate limit
        self._rate_limiters.acquire('reddit', blocking=True, timeout=30)

        try:
            sub = self._reddit.subreddit(subreddit)
            posts = []

            for post in sub.hot(limit=limit):
                # Filter by coin if specified
                if coin_id:
                    aliases = self.COIN_ALIASES.get(coin_id.lower(), [coin_id.lower()])
                    text = f"{post.title} {post.selftext}".lower()
                    if not any(alias in text for alias in aliases):
                        continue

                posts.append({
                    'title': post.title,
                    'text': post.selftext[:500] if post.selftext else '',
                    'score': post.score,
                    'upvote_ratio': post.upvote_ratio,
                    'num_comments': post.num_comments,
                    'created_utc': datetime.fromtimestamp(post.created_utc).isoformat()
                })

            if not posts:
                return {
                    'subreddit': subreddit,
                    'coin_id': coin_id,
                    'post_count': 0,
                    'sentiment': None,
                    'message': 'No matching posts found'
                }

            # Analyze sentiment
            texts = [f"{p['title']} {p['text']}" for p in posts]
            sentiment = self._sentiment_analyzer.aggregate_sentiment(texts)

            return {
                'subreddit': subreddit,
                'coin_id': coin_id,
                'post_count': len(posts),
                'sentiment': sentiment,
                'top_posts': posts[:5],
                'avg_score': sum(p['score'] for p in posts) / len(posts),
                'avg_comments': sum(p['num_comments'] for p in posts) / len(posts)
            }

        except Exception as e:
            logger.error(f"Failed to fetch Reddit data: {e}")
            return None

    @cached(ttl=1800, key_prefix='reddit_trending')  # 30 minute cache
    def get_trending_discussions(self, limit: int = 25) -> Optional[List[Dict]]:
        """
        Get trending crypto discussions across multiple subreddits.

        Args:
            limit: Number of posts per subreddit

        Returns:
            List of trending posts or None on failure
        """
        if not self.is_configured:
            logger.warning("Reddit client not configured")
            return self._get_mock_trending()

        all_posts = []

        for subreddit_name in self.DEFAULT_SUBREDDITS:
            self._rate_limiters.acquire('reddit', blocking=True, timeout=30)

            try:
                sub = self._reddit.subreddit(subreddit_name)

                for post in sub.hot(limit=limit):
                    # Analyze sentiment
                    text = f"{post.title} {post.selftext[:200] if post.selftext else ''}"
                    sentiment = self._sentiment_analyzer.analyze(text)

                    all_posts.append({
                        'subreddit': subreddit_name,
                        'title': post.title,
                        'score': post.score,
                        'upvote_ratio': post.upvote_ratio,
                        'num_comments': post.num_comments,
                        'sentiment_score': sentiment['compound'],
                        'url': f"https://reddit.com{post.permalink}",
                        'created_utc': datetime.fromtimestamp(post.created_utc).isoformat()
                    })

            except Exception as e:
                logger.error(f"Failed to fetch from r/{subreddit_name}: {e}")

        # Sort by engagement score
        all_posts.sort(key=lambda x: x['score'] + x['num_comments'] * 2, reverse=True)

        return all_posts[:50]

    def get_coin_mentions(self, coin_id: str, hours: int = 24) -> Optional[Dict]:
        """
        Count mentions of a coin across subreddits.

        Args:
            coin_id: Coin identifier
            hours: Time window in hours

        Returns:
            Mention statistics or None on failure
        """
        results = []

        for subreddit_name in self.DEFAULT_SUBREDDITS:
            sentiment_data = self.get_subreddit_sentiment(subreddit_name, coin_id, limit=100)
            if sentiment_data and sentiment_data.get('post_count', 0) > 0:
                results.append({
                    'subreddit': subreddit_name,
                    'mentions': sentiment_data['post_count'],
                    'sentiment': sentiment_data['sentiment']
                })

        if not results:
            return None

        total_mentions = sum(r['mentions'] for r in results)
        avg_sentiment = sum(r['sentiment']['avg_compound'] * r['mentions'] for r in results) / total_mentions

        return {
            'coin_id': coin_id,
            'total_mentions': total_mentions,
            'avg_sentiment': avg_sentiment,
            'subreddits': results
        }

    def _get_mock_sentiment(self, subreddit: str, coin_id: Optional[str]) -> Dict:
        """Return mock sentiment data when Reddit is not configured."""
        return {
            'subreddit': subreddit,
            'coin_id': coin_id,
            'post_count': 0,
            'sentiment': {
                'count': 0,
                'avg_compound': 0.0,
                'positive_ratio': 0.0,
                'negative_ratio': 0.0,
                'neutral_ratio': 1.0
            },
            'message': 'Reddit API not configured. Set REDDIT_CLIENT_ID and REDDIT_CLIENT_SECRET.',
            'mock_data': True
        }

    def _get_mock_trending(self) -> List[Dict]:
        """Return mock trending data when Reddit is not configured."""
        return [{
            'subreddit': 'CryptoCurrency',
            'title': 'Reddit API not configured',
            'score': 0,
            'upvote_ratio': 0,
            'num_comments': 0,
            'sentiment_score': 0,
            'url': '',
            'created_utc': datetime.utcnow().isoformat(),
            'mock_data': True,
            'message': 'Set REDDIT_CLIENT_ID and REDDIT_CLIENT_SECRET to enable.'
        }]

    def get_status(self) -> Dict:
        """Get API status and configuration."""
        return {
            'configured': self.is_configured,
            'praw_available': PRAW_AVAILABLE,
            'monitored_subreddits': self.DEFAULT_SUBREDDITS
        }


# Global client instance
_client: Optional[RedditClient] = None


def get_client() -> RedditClient:
    """Get or create the global Reddit client."""
    global _client
    if _client is None:
        _client = RedditClient()
    return _client


# Convenience functions
def get_subreddit_sentiment(subreddit: str, coin_id: Optional[str] = None) -> Optional[Dict]:
    """Get sentiment from a subreddit."""
    return get_client().get_subreddit_sentiment(subreddit, coin_id)


def get_trending_discussions() -> Optional[List[Dict]]:
    """Get trending crypto discussions."""
    return get_client().get_trending_discussions()
