"""
Crypto Sentiment Dashboard - CoinGecko API Client

Primary data source for cryptocurrency market data.
"""

import logging
import time
from typing import Any, Dict, List, Optional

import requests

from app.utils.cache import cached, get_cache
from app.utils.rate_limiter import get_rate_limiters, setup_default_limiters

logger = logging.getLogger(__name__)

# Ensure rate limiters are set up
setup_default_limiters()


class CoinGeckoClient:
    """
    CoinGecko API client with rate limiting and caching.

    Free tier limits: 30 calls/minute
    """

    BASE_URL = 'https://api.coingecko.com/api/v3'

    def __init__(self, api_key: Optional[str] = None):
        """
        Initialize CoinGecko client.

        Args:
            api_key: Optional API key for Pro tier (higher rate limits)
        """
        self.api_key = api_key
        self.session = requests.Session()
        self.session.headers.update({
            'Accept': 'application/json',
            'User-Agent': 'crypto-sentiment-dashboard/1.0'
        })
        if api_key:
            self.session.headers['x-cg-demo-api-key'] = api_key

        self._rate_limiters = get_rate_limiters()
        self._cache = get_cache()
        self._max_retries = 3
        self._base_delay = 1.0

    def _request(self, endpoint: str, params: Optional[Dict] = None) -> Optional[Dict]:
        """
        Make rate-limited API request with exponential backoff.

        Args:
            endpoint: API endpoint path
            params: Query parameters

        Returns:
            JSON response or None on failure
        """
        url = f"{self.BASE_URL}/{endpoint}"

        for attempt in range(self._max_retries):
            # Wait for rate limit
            self._rate_limiters.acquire('coingecko', blocking=True, timeout=30)

            try:
                response = self.session.get(url, params=params, timeout=10)

                if response.status_code == 200:
                    return response.json()

                if response.status_code == 429:
                    # Rate limited - wait and retry
                    delay = self._base_delay * (2 ** attempt)
                    logger.warning(f"CoinGecko rate limited. Waiting {delay}s...")
                    time.sleep(delay)
                    continue

                logger.error(f"CoinGecko API error: {response.status_code} - {response.text}")
                return None

            except requests.RequestException as e:
                logger.error(f"CoinGecko request failed: {e}")
                if attempt < self._max_retries - 1:
                    delay = self._base_delay * (2 ** attempt)
                    time.sleep(delay)

        return None

    @cached(ttl=60, key_prefix='coingecko_trending')
    def get_trending_coins(self) -> Optional[Dict]:
        """
        Get trending cryptocurrencies (updated every ~10 minutes on CoinGecko).

        Returns:
            Trending coins data or None on failure
        """
        data = self._request('search/trending')
        if data and 'coins' in data:
            return {
                'coins': [
                    {
                        'id': item['item']['id'],
                        'name': item['item']['name'],
                        'symbol': item['item']['symbol'],
                        'market_cap_rank': item['item'].get('market_cap_rank'),
                        'thumb': item['item'].get('thumb'),
                        'score': item['item'].get('score')
                    }
                    for item in data['coins']
                ]
            }
        return None

    @cached(ttl=300, key_prefix='coingecko_markets')
    def get_market_data(
        self,
        coin_ids: Optional[List[str]] = None,
        vs_currency: str = 'usd',
        per_page: int = 100,
        page: int = 1,
        order: str = 'market_cap_desc'
    ) -> Optional[List[Dict]]:
        """
        Get market data for coins.

        Args:
            coin_ids: List of coin IDs (e.g., ['bitcoin', 'ethereum'])
            vs_currency: Target currency for prices
            per_page: Results per page (max 250)
            page: Page number
            order: Sort order

        Returns:
            List of coin market data or None on failure
        """
        params = {
            'vs_currency': vs_currency,
            'order': order,
            'per_page': min(per_page, 250),
            'page': page,
            'sparkline': 'false',
            'price_change_percentage': '24h,7d'
        }

        if coin_ids:
            params['ids'] = ','.join(coin_ids)

        return self._request('coins/markets', params)

    @cached(ttl=300, key_prefix='coingecko_coin')
    def get_coin_details(self, coin_id: str) -> Optional[Dict]:
        """
        Get detailed information for a specific coin.

        Args:
            coin_id: CoinGecko coin ID (e.g., 'bitcoin')

        Returns:
            Detailed coin data or None on failure
        """
        params = {
            'localization': 'false',
            'tickers': 'false',
            'community_data': 'true',
            'developer_data': 'false',
            'sparkline': 'false'
        }

        data = self._request(f'coins/{coin_id}', params)
        if data:
            return {
                'id': data.get('id'),
                'symbol': data.get('symbol'),
                'name': data.get('name'),
                'description': data.get('description', {}).get('en', ''),
                'image': data.get('image', {}),
                'market_data': data.get('market_data', {}),
                'community_data': data.get('community_data', {}),
                'market_cap_rank': data.get('market_cap_rank'),
                'categories': data.get('categories', [])
            }
        return None

    @cached(ttl=300, key_prefix='coingecko_history')
    def get_price_history(
        self,
        coin_id: str,
        days: int = 7,
        vs_currency: str = 'usd'
    ) -> Optional[Dict]:
        """
        Get historical price data.

        Args:
            coin_id: CoinGecko coin ID
            days: Number of days (1, 7, 14, 30, 90, 180, 365, max)
            vs_currency: Target currency

        Returns:
            Historical price data or None on failure
        """
        params = {
            'vs_currency': vs_currency,
            'days': days
        }

        data = self._request(f'coins/{coin_id}/market_chart', params)
        if data:
            return {
                'prices': data.get('prices', []),
                'market_caps': data.get('market_caps', []),
                'total_volumes': data.get('total_volumes', [])
            }
        return None

    @cached(ttl=300, key_prefix='coingecko_prices')
    def get_simple_prices(
        self,
        coin_ids: List[str],
        vs_currencies: List[str] = None,
        include_24h_change: bool = True
    ) -> Optional[Dict]:
        """
        Get simple price data for multiple coins.

        Args:
            coin_ids: List of coin IDs
            vs_currencies: List of target currencies
            include_24h_change: Include 24h price change

        Returns:
            Price data or None on failure
        """
        if vs_currencies is None:
            vs_currencies = ['usd']

        params = {
            'ids': ','.join(coin_ids),
            'vs_currencies': ','.join(vs_currencies),
            'include_24hr_change': str(include_24h_change).lower()
        }

        return self._request('simple/price', params)

    def ping(self) -> bool:
        """Check if CoinGecko API is reachable."""
        data = self._request('ping')
        return data is not None and 'gecko_says' in data


# Global client instance
_client: Optional[CoinGeckoClient] = None


def get_client(api_key: Optional[str] = None) -> CoinGeckoClient:
    """Get or create the global CoinGecko client."""
    global _client
    if _client is None:
        _client = CoinGeckoClient(api_key)
    return _client


# Convenience functions
def get_trending_coins() -> Optional[Dict]:
    """Get trending cryptocurrencies."""
    return get_client().get_trending_coins()


def get_market_data(coin_ids: Optional[List[str]] = None, vs_currency: str = 'usd') -> Optional[List[Dict]]:
    """Get market data for coins."""
    return get_client().get_market_data(coin_ids, vs_currency)


def get_coin_details(coin_id: str) -> Optional[Dict]:
    """Get detailed information for a coin."""
    return get_client().get_coin_details(coin_id)


def get_price_history(coin_id: str, days: int = 7) -> Optional[Dict]:
    """Get historical price data."""
    return get_client().get_price_history(coin_id, days)


def get_simple_prices(coin_ids: List[str], vs_currencies: List[str] = None) -> Optional[Dict]:
    """Get simple price data."""
    return get_client().get_simple_prices(coin_ids, vs_currencies)
