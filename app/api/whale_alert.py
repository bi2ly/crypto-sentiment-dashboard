"""
Crypto Sentiment Dashboard - Whale Alert API Client

Tracks large cryptocurrency transactions.
"""

import logging
import os
from datetime import datetime, timedelta
from typing import Dict, List, Optional

import requests

from app.utils.cache import cached, get_cache
from app.utils.rate_limiter import get_rate_limiters, setup_default_limiters

logger = logging.getLogger(__name__)

# Ensure rate limiters are set up
setup_default_limiters()


class WhaleAlertClient:
    """
    Whale Alert API client for tracking large crypto transactions.

    Free tier limits: 10 requests/minute, 500 historical requests/month
    """

    BASE_URL = 'https://api.whale-alert.io/v1'

    # Known exchange wallets for flow analysis
    EXCHANGES = [
        'binance', 'coinbase', 'kraken', 'bitfinex', 'huobi',
        'okex', 'kucoin', 'ftx', 'bybit', 'gate.io', 'bitstamp'
    ]

    def __init__(self, api_key: Optional[str] = None):
        """
        Initialize Whale Alert client.

        Args:
            api_key: Whale Alert API key (from environment if not provided)
        """
        self.api_key = api_key or os.getenv('WHALE_ALERT_API_KEY')
        self.session = requests.Session()
        self.session.headers.update({
            'Accept': 'application/json',
            'User-Agent': 'crypto-sentiment-dashboard/1.0'
        })
        self._rate_limiters = get_rate_limiters()
        self._cache = get_cache()

    def _request(self, endpoint: str, params: Optional[Dict] = None) -> Optional[Dict]:
        """
        Make API request.

        Args:
            endpoint: API endpoint path
            params: Query parameters

        Returns:
            JSON response or None on failure
        """
        if not self.api_key:
            logger.warning("Whale Alert API key not configured")
            return None

        # Wait for rate limit
        self._rate_limiters.acquire('whale_alert', blocking=True, timeout=30)

        url = f"{self.BASE_URL}/{endpoint}"
        params = params or {}
        params['api_key'] = self.api_key

        try:
            response = self.session.get(url, params=params, timeout=10)

            if response.status_code == 200:
                data = response.json()
                if data.get('result') == 'success':
                    return data
                logger.error(f"Whale Alert API error: {data.get('message')}")
                return None

            if response.status_code == 401:
                logger.error("Whale Alert API key invalid or expired")
            elif response.status_code == 429:
                logger.warning("Whale Alert rate limit exceeded")
            else:
                logger.error(f"Whale Alert API error: {response.status_code}")

            return None

        except requests.RequestException as e:
            logger.error(f"Whale Alert request failed: {e}")
            return None

    @cached(ttl=900, key_prefix='whale_transactions')  # 15 minute cache
    def get_recent_transactions(
        self,
        min_value: int = 1_000_000,
        limit: int = 100,
        currency: Optional[str] = None
    ) -> Optional[List[Dict]]:
        """
        Get recent large transactions.

        Args:
            min_value: Minimum transaction value in USD
            limit: Maximum number of transactions (max 100)
            currency: Filter by currency (e.g., 'bitcoin', 'ethereum')

        Returns:
            List of transactions or None on failure
        """
        # Calculate start time (last hour)
        start = int((datetime.utcnow() - timedelta(hours=1)).timestamp())

        params = {
            'min_value': min_value,
            'start': start,
            'limit': min(limit, 100)
        }

        if currency:
            params['currency'] = currency

        data = self._request('transactions', params)
        if data and 'transactions' in data:
            return [
                self._format_transaction(tx)
                for tx in data['transactions']
            ]
        return None

    def _format_transaction(self, tx: Dict) -> Dict:
        """Format raw transaction data."""
        return {
            'hash': tx.get('hash', ''),
            'blockchain': tx.get('blockchain', ''),
            'symbol': tx.get('symbol', ''),
            'amount': tx.get('amount', 0),
            'amount_usd': tx.get('amount_usd', 0),
            'from': {
                'address': tx.get('from', {}).get('address', ''),
                'owner': tx.get('from', {}).get('owner', 'unknown'),
                'type': tx.get('from', {}).get('owner_type', 'unknown')
            },
            'to': {
                'address': tx.get('to', {}).get('address', ''),
                'owner': tx.get('to', {}).get('owner', 'unknown'),
                'type': tx.get('to', {}).get('owner_type', 'unknown')
            },
            'timestamp': datetime.fromtimestamp(tx.get('timestamp', 0)).isoformat(),
            'transaction_type': self._classify_transaction(tx)
        }

    def _classify_transaction(self, tx: Dict) -> str:
        """
        Classify transaction type based on from/to addresses.

        Returns:
            Transaction type (exchange_deposit, exchange_withdrawal,
            exchange_to_exchange, wallet_to_wallet)
        """
        from_type = tx.get('from', {}).get('owner_type', '')
        to_type = tx.get('to', {}).get('owner_type', '')

        if from_type == 'exchange' and to_type == 'exchange':
            return 'exchange_to_exchange'
        elif from_type == 'exchange':
            return 'exchange_withdrawal'
        elif to_type == 'exchange':
            return 'exchange_deposit'
        else:
            return 'wallet_to_wallet'

    @cached(ttl=1800, key_prefix='whale_flows')  # 30 minute cache
    def get_exchange_flows(self, hours: int = 24) -> Optional[Dict]:
        """
        Analyze exchange inflow/outflow over time period.

        Args:
            hours: Time period in hours

        Returns:
            Exchange flow analysis or None on failure
        """
        transactions = self.get_recent_transactions(min_value=500_000)
        if not transactions:
            return None

        inflow = 0.0
        outflow = 0.0
        deposit_count = 0
        withdrawal_count = 0

        for tx in transactions:
            tx_type = tx['transaction_type']
            amount_usd = tx['amount_usd']

            if tx_type == 'exchange_deposit':
                inflow += amount_usd
                deposit_count += 1
            elif tx_type == 'exchange_withdrawal':
                outflow += amount_usd
                withdrawal_count += 1

        net_flow = inflow - outflow

        return {
            'period_hours': hours,
            'inflow_usd': inflow,
            'outflow_usd': outflow,
            'net_flow_usd': net_flow,
            'deposit_count': deposit_count,
            'withdrawal_count': withdrawal_count,
            'signal': 'BEARISH' if net_flow > 0 else 'BULLISH' if net_flow < 0 else 'NEUTRAL',
            'reasoning': self._get_flow_reasoning(net_flow)
        }

    def _get_flow_reasoning(self, net_flow: float) -> str:
        """Get explanation for exchange flow signal."""
        if net_flow > 1_000_000_000:
            return 'Very high exchange inflows - potential selling pressure'
        elif net_flow > 100_000_000:
            return 'High exchange inflows - bearish signal'
        elif net_flow < -1_000_000_000:
            return 'Very high exchange outflows - accumulation signal'
        elif net_flow < -100_000_000:
            return 'High exchange outflows - bullish signal'
        else:
            return 'Exchange flows are balanced'

    def get_status(self) -> Dict:
        """Get API status and configuration."""
        return {
            'configured': self.api_key is not None,
            'rate_limit': '10/minute (free tier)'
        }


# Global client instance
_client: Optional[WhaleAlertClient] = None


def get_client(api_key: Optional[str] = None) -> WhaleAlertClient:
    """Get or create the global Whale Alert client."""
    global _client
    if _client is None:
        _client = WhaleAlertClient(api_key)
    return _client


# Convenience functions
def get_recent_transactions(min_value: int = 1_000_000, limit: int = 10) -> Optional[List[Dict]]:
    """Get recent whale transactions."""
    return get_client().get_recent_transactions(min_value, limit)


def get_exchange_flows() -> Optional[Dict]:
    """Get exchange inflow/outflow analysis."""
    return get_client().get_exchange_flows()
