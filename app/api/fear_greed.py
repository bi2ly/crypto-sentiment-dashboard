"""
Crypto Sentiment Dashboard - Fear & Greed Index API Client

Data source for crypto market sentiment indicator.
"""

import logging
from datetime import datetime
from typing import Dict, List, Optional

import requests

from app.utils.cache import cached, get_cache
from app.utils.rate_limiter import get_rate_limiters, setup_default_limiters

logger = logging.getLogger(__name__)

# Ensure rate limiters are set up
setup_default_limiters()


class FearGreedClient:
    """
    Fear & Greed Index API client.

    The index is updated once daily. Values range from 0 (Extreme Fear)
    to 100 (Extreme Greed).

    Classifications:
    - 0-25: Extreme Fear
    - 26-46: Fear
    - 47-52: Neutral
    - 53-74: Greed
    - 75-100: Extreme Greed
    """

    BASE_URL = 'https://api.alternative.me/fng/'

    CLASSIFICATIONS = {
        (0, 25): 'Extreme Fear',
        (26, 46): 'Fear',
        (47, 52): 'Neutral',
        (53, 74): 'Greed',
        (75, 100): 'Extreme Greed'
    }

    def __init__(self):
        """Initialize Fear & Greed client."""
        self.session = requests.Session()
        self.session.headers.update({
            'Accept': 'application/json',
            'User-Agent': 'crypto-sentiment-dashboard/1.0'
        })
        self._rate_limiters = get_rate_limiters()
        self._cache = get_cache()

    def _request(self, params: Optional[Dict] = None) -> Optional[Dict]:
        """
        Make API request.

        Args:
            params: Query parameters

        Returns:
            JSON response or None on failure
        """
        # Wait for rate limit
        self._rate_limiters.acquire('fear_greed', blocking=True, timeout=30)

        try:
            response = self.session.get(self.BASE_URL, params=params, timeout=10)

            if response.status_code == 200:
                data = response.json()
                if data.get('metadata', {}).get('error') is None:
                    return data
                logger.error(f"Fear & Greed API error: {data.get('metadata', {}).get('error')}")
                return None

            logger.error(f"Fear & Greed API error: {response.status_code}")
            return None

        except requests.RequestException as e:
            logger.error(f"Fear & Greed request failed: {e}")
            return None

    @staticmethod
    def classify_value(value: int) -> str:
        """
        Get classification for a Fear & Greed value.

        Args:
            value: Index value (0-100)

        Returns:
            Classification string
        """
        for (low, high), classification in FearGreedClient.CLASSIFICATIONS.items():
            if low <= value <= high:
                return classification
        return 'Unknown'

    @cached(ttl=14400, key_prefix='fear_greed_current')  # 4 hour cache
    def get_current_index(self) -> Optional[Dict]:
        """
        Get current Fear & Greed Index.

        Returns:
            Current index data or None on failure
        """
        data = self._request({'limit': 1})
        if data and 'data' in data and len(data['data']) > 0:
            entry = data['data'][0]
            value = int(entry.get('value', 50))
            return {
                'value': value,
                'classification': entry.get('value_classification', self.classify_value(value)),
                'timestamp': datetime.fromtimestamp(int(entry.get('timestamp', 0))).isoformat(),
                'time_until_update': entry.get('time_until_update', 'Unknown')
            }
        return None

    @cached(ttl=14400, key_prefix='fear_greed_history')  # 4 hour cache
    def get_historical_index(self, days: int = 30) -> Optional[List[Dict]]:
        """
        Get historical Fear & Greed Index data.

        Args:
            days: Number of days of history (max varies by API)

        Returns:
            List of historical data points or None on failure
        """
        data = self._request({'limit': days})
        if data and 'data' in data:
            return [
                {
                    'value': int(entry.get('value', 50)),
                    'classification': entry.get('value_classification', self.classify_value(int(entry.get('value', 50)))),
                    'timestamp': datetime.fromtimestamp(int(entry.get('timestamp', 0))).isoformat()
                }
                for entry in data['data']
            ]
        return None

    def get_sentiment_signal(self) -> Optional[Dict]:
        """
        Get trading signal based on Fear & Greed.

        Contrarian strategy:
        - Extreme Fear = potential buying opportunity
        - Extreme Greed = potential selling opportunity

        Returns:
            Signal data with recommendation
        """
        current = self.get_current_index()
        if not current:
            return None

        value = current['value']

        if value <= 25:
            signal = 'BUY'
            strength = 'STRONG'
            reasoning = 'Extreme fear often indicates oversold conditions'
        elif value <= 40:
            signal = 'BUY'
            strength = 'MODERATE'
            reasoning = 'Fear may present buying opportunities'
        elif value <= 60:
            signal = 'HOLD'
            strength = 'NEUTRAL'
            reasoning = 'Market sentiment is neutral'
        elif value <= 75:
            signal = 'SELL'
            strength = 'MODERATE'
            reasoning = 'Greed may indicate overbought conditions'
        else:
            signal = 'SELL'
            strength = 'STRONG'
            reasoning = 'Extreme greed often precedes corrections'

        return {
            'current': current,
            'signal': signal,
            'strength': strength,
            'reasoning': reasoning
        }


# Global client instance
_client: Optional[FearGreedClient] = None


def get_client() -> FearGreedClient:
    """Get or create the global Fear & Greed client."""
    global _client
    if _client is None:
        _client = FearGreedClient()
    return _client


# Convenience functions
def get_current_index() -> Optional[Dict]:
    """Get current Fear & Greed Index."""
    return get_client().get_current_index()


def get_historical_index(days: int = 30) -> Optional[List[Dict]]:
    """Get historical Fear & Greed Index."""
    return get_client().get_historical_index(days)


def get_sentiment_signal() -> Optional[Dict]:
    """Get trading signal based on Fear & Greed."""
    return get_client().get_sentiment_signal()
