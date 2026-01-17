"""
Crypto Sentiment Dashboard - News API Client

Fetches and analyzes crypto news articles.
"""

import logging
import os
from datetime import datetime, timedelta
from typing import Dict, List, Optional

import requests

from app.utils.cache import cached, get_cache
from app.utils.rate_limiter import get_rate_limiters, setup_default_limiters
from app.utils.sentiment import get_analyzer

logger = logging.getLogger(__name__)

# Ensure rate limiters are set up
setup_default_limiters()


class NewsAPIClient:
    """
    NewsAPI client for crypto news fetching and sentiment analysis.

    Free tier limits: 100 requests/day
    """

    BASE_URL = 'https://newsapi.org/v2'

    # Crypto-related sources
    CRYPTO_SOURCES = [
        'crypto-coins-news',
        'the-next-web',
        'techcrunch',
        'wired',
        'ars-technica',
        'reuters',
        'bloomberg'
    ]

    def __init__(self, api_key: Optional[str] = None):
        """
        Initialize NewsAPI client.

        Args:
            api_key: NewsAPI key (from environment if not provided)
        """
        self.api_key = api_key or os.getenv('NEWS_API_KEY')
        self.session = requests.Session()
        self.session.headers.update({
            'Accept': 'application/json',
            'User-Agent': 'crypto-sentiment-dashboard/1.0'
        })
        if self.api_key:
            self.session.headers['X-Api-Key'] = self.api_key

        self._rate_limiters = get_rate_limiters()
        self._cache = get_cache()
        self._sentiment_analyzer = get_analyzer()

    def _request(self, endpoint: str, params: Dict) -> Optional[Dict]:
        """
        Make API request.

        Args:
            endpoint: API endpoint path
            params: Query parameters

        Returns:
            JSON response or None on failure
        """
        if not self.api_key:
            logger.warning("NewsAPI key not configured")
            return None

        # Wait for rate limit
        self._rate_limiters.acquire('newsapi', blocking=True, timeout=30)

        url = f"{self.BASE_URL}/{endpoint}"

        try:
            response = self.session.get(url, params=params, timeout=15)

            if response.status_code == 200:
                data = response.json()
                if data.get('status') == 'ok':
                    return data
                logger.error(f"NewsAPI error: {data.get('message')}")
                return None

            if response.status_code == 401:
                logger.error("NewsAPI key invalid")
            elif response.status_code == 429:
                logger.warning("NewsAPI rate limit exceeded")
            else:
                logger.error(f"NewsAPI error: {response.status_code}")

            return None

        except requests.RequestException as e:
            logger.error(f"NewsAPI request failed: {e}")
            return None

    @cached(ttl=3600, key_prefix='news_crypto')  # 1 hour cache
    def get_crypto_news(
        self,
        query: str = 'cryptocurrency OR bitcoin OR ethereum',
        limit: int = 20,
        language: str = 'en',
        sort_by: str = 'publishedAt'
    ) -> Optional[List[Dict]]:
        """
        Get crypto-related news articles.

        Args:
            query: Search query
            limit: Maximum number of articles
            language: Language code
            sort_by: Sort order (publishedAt, relevancy, popularity)

        Returns:
            List of articles with sentiment or None on failure
        """
        # NewsAPI free tier only allows 1 month old articles
        from_date = (datetime.utcnow() - timedelta(days=7)).strftime('%Y-%m-%d')

        params = {
            'q': query,
            'language': language,
            'sortBy': sort_by,
            'pageSize': min(limit, 100),
            'from': from_date
        }

        data = self._request('everything', params)
        if data and 'articles' in data:
            articles = []
            for article in data['articles'][:limit]:
                # Analyze sentiment
                text = f"{article.get('title', '')} {article.get('description', '')}"
                sentiment = self._sentiment_analyzer.analyze(text)
                label, confidence = self._sentiment_analyzer.classify(text)

                articles.append({
                    'title': article.get('title'),
                    'description': article.get('description'),
                    'url': article.get('url'),
                    'source': article.get('source', {}).get('name'),
                    'author': article.get('author'),
                    'published_at': article.get('publishedAt'),
                    'image_url': article.get('urlToImage'),
                    'sentiment': {
                        'score': sentiment['compound'],
                        'label': label,
                        'confidence': confidence
                    }
                })

            return articles
        return None

    @cached(ttl=3600, key_prefix='news_coin')  # 1 hour cache
    def get_coin_news(self, coin_name: str, limit: int = 10) -> Optional[List[Dict]]:
        """
        Get news for a specific cryptocurrency.

        Args:
            coin_name: Coin name (e.g., 'Bitcoin', 'Ethereum')
            limit: Maximum number of articles

        Returns:
            List of articles or None on failure
        """
        query = f'"{coin_name}" cryptocurrency'
        return self.get_crypto_news(query=query, limit=limit)

    def analyze_sentiment(self, articles: List[Dict]) -> Dict:
        """
        Aggregate sentiment analysis across articles.

        Args:
            articles: List of articles with sentiment data

        Returns:
            Aggregated sentiment statistics
        """
        if not articles:
            return {
                'count': 0,
                'avg_sentiment': 0.0,
                'positive_count': 0,
                'negative_count': 0,
                'neutral_count': 0
            }

        sentiments = [a.get('sentiment', {}) for a in articles if a.get('sentiment')]
        scores = [s.get('score', 0) for s in sentiments]

        positive = sum(1 for s in sentiments if s.get('label') == 'positive')
        negative = sum(1 for s in sentiments if s.get('label') == 'negative')
        neutral = len(sentiments) - positive - negative

        return {
            'count': len(articles),
            'avg_sentiment': sum(scores) / len(scores) if scores else 0.0,
            'positive_count': positive,
            'negative_count': negative,
            'neutral_count': neutral,
            'positive_ratio': positive / len(sentiments) if sentiments else 0,
            'negative_ratio': negative / len(sentiments) if sentiments else 0
        }

    @cached(ttl=3600, key_prefix='news_headlines')  # 1 hour cache
    def get_top_headlines(self, category: str = 'technology', country: str = 'us') -> Optional[List[Dict]]:
        """
        Get top headlines in a category.

        Args:
            category: News category
            country: Country code

        Returns:
            List of headlines or None on failure
        """
        params = {
            'category': category,
            'country': country,
            'pageSize': 20
        }

        data = self._request('top-headlines', params)
        if data and 'articles' in data:
            # Filter for crypto-related headlines
            crypto_keywords = ['crypto', 'bitcoin', 'ethereum', 'blockchain', 'defi', 'nft']
            articles = []

            for article in data['articles']:
                title = (article.get('title') or '').lower()
                desc = (article.get('description') or '').lower()

                if any(kw in title or kw in desc for kw in crypto_keywords):
                    text = f"{article.get('title', '')} {article.get('description', '')}"
                    sentiment = self._sentiment_analyzer.analyze(text)

                    articles.append({
                        'title': article.get('title'),
                        'description': article.get('description'),
                        'url': article.get('url'),
                        'source': article.get('source', {}).get('name'),
                        'published_at': article.get('publishedAt'),
                        'sentiment_score': sentiment['compound']
                    })

            return articles
        return None

    def get_news_summary(self) -> Dict:
        """
        Get overall crypto news sentiment summary.

        Returns:
            News sentiment summary
        """
        articles = self.get_crypto_news(limit=50)
        if not articles:
            return {
                'status': 'unavailable',
                'message': 'Could not fetch news articles'
            }

        sentiment_stats = self.analyze_sentiment(articles)

        # Determine overall sentiment
        avg = sentiment_stats['avg_sentiment']
        if avg >= 0.1:
            overall = 'positive'
        elif avg <= -0.1:
            overall = 'negative'
        else:
            overall = 'neutral'

        return {
            'status': 'success',
            'overall_sentiment': overall,
            'sentiment_score': avg,
            'article_count': sentiment_stats['count'],
            'positive_articles': sentiment_stats['positive_count'],
            'negative_articles': sentiment_stats['negative_count'],
            'neutral_articles': sentiment_stats['neutral_count'],
            'top_articles': articles[:5]
        }

    def get_status(self) -> Dict:
        """Get API status and configuration."""
        return {
            'configured': self.api_key is not None,
            'rate_limit': '100/day (free tier)'
        }


# Global client instance
_client: Optional[NewsAPIClient] = None


def get_client(api_key: Optional[str] = None) -> NewsAPIClient:
    """Get or create the global NewsAPI client."""
    global _client
    if _client is None:
        _client = NewsAPIClient(api_key)
    return _client


# Convenience functions
def get_crypto_news(query: str = 'cryptocurrency', limit: int = 10) -> Optional[List[Dict]]:
    """Get crypto news articles."""
    return get_client().get_crypto_news(query, limit)


def get_coin_news(coin_name: str, limit: int = 10) -> Optional[List[Dict]]:
    """Get news for a specific coin."""
    return get_client().get_coin_news(coin_name, limit)


def analyze_sentiment(articles: List[Dict]) -> Dict:
    """Analyze sentiment of articles."""
    return get_client().analyze_sentiment(articles)
