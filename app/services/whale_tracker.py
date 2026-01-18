"""
Crypto Sentiment Dashboard - Whale Activity Tracker

Advanced whale transaction analysis and alerts.
"""

import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional
from collections import defaultdict

from app.api import whale_alert
from app.utils.cache import cached

logger = logging.getLogger(__name__)


class WhaleTracker:
    """
    Advanced whale activity tracking and analysis.

    Provides:
    - Transaction classification by type and size
    - Exchange flow analysis
    - Accumulation/distribution detection
    - Alert generation for significant movements
    """

    # Transaction size thresholds (USD)
    THRESHOLDS = {
        'small': 500_000,
        'medium': 1_000_000,
        'large': 5_000_000,
        'mega': 10_000_000,
        'whale': 50_000_000
    }

    def __init__(self):
        self._whale_alert = whale_alert.get_client()

    def classify_transaction(self, amount_usd: float) -> str:
        """Classify transaction by size."""
        if amount_usd >= self.THRESHOLDS['whale']:
            return 'WHALE'
        elif amount_usd >= self.THRESHOLDS['mega']:
            return 'MEGA'
        elif amount_usd >= self.THRESHOLDS['large']:
            return 'LARGE'
        elif amount_usd >= self.THRESHOLDS['medium']:
            return 'MEDIUM'
        elif amount_usd >= self.THRESHOLDS['small']:
            return 'SMALL'
        return 'MINOR'

    @cached(ttl=900, key_prefix='whale_analysis')
    def get_whale_analysis(self, min_value: int = 1_000_000) -> Optional[Dict]:
        """
        Get comprehensive whale activity analysis.

        Args:
            min_value: Minimum transaction value in USD

        Returns:
            Whale activity analysis with trends and signals
        """
        transactions = self._whale_alert.get_recent_transactions(min_value, limit=100)

        if not transactions:
            return {
                'status': 'unavailable',
                'message': 'Whale Alert API not configured or no data available',
                'configured': self._whale_alert.get_status()['configured']
            }

        # Analyze transactions
        analysis = self._analyze_transactions(transactions)

        return {
            'status': 'success',
            'timestamp': datetime.utcnow().isoformat(),
            'summary': analysis['summary'],
            'by_coin': analysis['by_coin'],
            'by_type': analysis['by_type'],
            'exchange_flow': analysis['exchange_flow'],
            'alerts': analysis['alerts'],
            'recent_transactions': transactions[:10]
        }

    def _analyze_transactions(self, transactions: List[Dict]) -> Dict:
        """Analyze list of transactions."""
        # Initialize counters
        by_coin = defaultdict(lambda: {
            'count': 0,
            'total_usd': 0,
            'inflow': 0,
            'outflow': 0
        })

        by_type = defaultdict(lambda: {'count': 0, 'total_usd': 0})

        exchange_inflow = 0
        exchange_outflow = 0
        total_volume = 0

        alerts = []

        for tx in transactions:
            symbol = tx.get('symbol', 'UNKNOWN')
            amount_usd = tx.get('amount_usd', 0)
            tx_type = tx.get('transaction_type', 'unknown')

            # Aggregate by coin
            by_coin[symbol]['count'] += 1
            by_coin[symbol]['total_usd'] += amount_usd

            # Aggregate by type
            by_type[tx_type]['count'] += 1
            by_type[tx_type]['total_usd'] += amount_usd

            # Track exchange flows
            if tx_type == 'exchange_deposit':
                exchange_inflow += amount_usd
                by_coin[symbol]['inflow'] += amount_usd
            elif tx_type == 'exchange_withdrawal':
                exchange_outflow += amount_usd
                by_coin[symbol]['outflow'] += amount_usd

            total_volume += amount_usd

            # Generate alerts for significant transactions
            size_class = self.classify_transaction(amount_usd)
            if size_class in ['WHALE', 'MEGA']:
                alerts.append({
                    'type': 'LARGE_TRANSACTION',
                    'severity': 'HIGH' if size_class == 'WHALE' else 'MEDIUM',
                    'symbol': symbol,
                    'amount_usd': amount_usd,
                    'transaction_type': tx_type,
                    'message': f"${amount_usd:,.0f} {symbol} {tx_type.replace('_', ' ')}"
                })

        # Calculate net flow
        net_flow = exchange_inflow - exchange_outflow

        # Determine market signal
        if net_flow > 100_000_000:  # $100M+ net inflow
            flow_signal = 'STRONGLY_BEARISH'
            flow_reason = 'Massive exchange inflows suggest selling pressure'
        elif net_flow > 10_000_000:
            flow_signal = 'BEARISH'
            flow_reason = 'Significant exchange inflows may indicate selling'
        elif net_flow < -100_000_000:
            flow_signal = 'STRONGLY_BULLISH'
            flow_reason = 'Massive exchange outflows suggest accumulation'
        elif net_flow < -10_000_000:
            flow_signal = 'BULLISH'
            flow_reason = 'Exchange outflows indicate accumulation'
        else:
            flow_signal = 'NEUTRAL'
            flow_reason = 'Exchange flows are balanced'

        # Check for accumulation alerts
        for symbol, data in by_coin.items():
            net_coin_flow = data['inflow'] - data['outflow']
            if net_coin_flow < -5_000_000:  # $5M+ net outflow
                alerts.append({
                    'type': 'ACCUMULATION',
                    'severity': 'MEDIUM',
                    'symbol': symbol,
                    'amount_usd': abs(net_coin_flow),
                    'message': f"{symbol} accumulation detected: ${abs(net_coin_flow):,.0f} leaving exchanges"
                })
            elif net_coin_flow > 5_000_000:  # $5M+ net inflow
                alerts.append({
                    'type': 'DISTRIBUTION',
                    'severity': 'MEDIUM',
                    'symbol': symbol,
                    'amount_usd': net_coin_flow,
                    'message': f"{symbol} distribution detected: ${net_coin_flow:,.0f} moving to exchanges"
                })

        return {
            'summary': {
                'total_transactions': len(transactions),
                'total_volume_usd': total_volume,
                'unique_coins': len(by_coin),
                'alert_count': len(alerts)
            },
            'by_coin': dict(by_coin),
            'by_type': dict(by_type),
            'exchange_flow': {
                'inflow_usd': exchange_inflow,
                'outflow_usd': exchange_outflow,
                'net_flow_usd': net_flow,
                'signal': flow_signal,
                'reason': flow_reason
            },
            'alerts': sorted(alerts, key=lambda x: x.get('amount_usd', 0), reverse=True)[:10]
        }

    @cached(ttl=1800, key_prefix='whale_coin_flow')
    def get_coin_flow_analysis(self, symbol: str) -> Optional[Dict]:
        """
        Get exchange flow analysis for a specific coin.

        Args:
            symbol: Coin symbol (e.g., 'BTC', 'ETH')

        Returns:
            Coin-specific flow analysis
        """
        # Get recent transactions for this coin
        transactions = self._whale_alert.get_recent_transactions(
            min_value=500_000,
            limit=100
        )

        if not transactions:
            return None

        # Filter by symbol
        coin_txs = [
            tx for tx in transactions
            if tx.get('symbol', '').upper() == symbol.upper()
        ]

        if not coin_txs:
            return {
                'symbol': symbol,
                'transaction_count': 0,
                'message': f'No whale transactions found for {symbol}'
            }

        inflow = sum(tx['amount_usd'] for tx in coin_txs if tx['transaction_type'] == 'exchange_deposit')
        outflow = sum(tx['amount_usd'] for tx in coin_txs if tx['transaction_type'] == 'exchange_withdrawal')
        total = sum(tx['amount_usd'] for tx in coin_txs)

        net_flow = inflow - outflow

        return {
            'symbol': symbol,
            'transaction_count': len(coin_txs),
            'total_volume_usd': total,
            'exchange_inflow_usd': inflow,
            'exchange_outflow_usd': outflow,
            'net_flow_usd': net_flow,
            'signal': 'ACCUMULATION' if net_flow < 0 else 'DISTRIBUTION' if net_flow > 0 else 'NEUTRAL',
            'recent_transactions': coin_txs[:5]
        }

    def get_whale_alerts(self, min_severity: str = 'MEDIUM') -> List[Dict]:
        """
        Get current whale alerts.

        Args:
            min_severity: Minimum alert severity (LOW, MEDIUM, HIGH)

        Returns:
            List of whale alerts
        """
        analysis = self.get_whale_analysis()

        if analysis.get('status') != 'success':
            return []

        severity_order = {'LOW': 0, 'MEDIUM': 1, 'HIGH': 2}
        min_level = severity_order.get(min_severity, 1)

        return [
            alert for alert in analysis.get('alerts', [])
            if severity_order.get(alert.get('severity', 'LOW'), 0) >= min_level
        ]


# Global tracker instance
_tracker: Optional[WhaleTracker] = None


def get_tracker() -> WhaleTracker:
    """Get or create the global whale tracker."""
    global _tracker
    if _tracker is None:
        _tracker = WhaleTracker()
    return _tracker


# Convenience functions
def get_whale_analysis(min_value: int = 1_000_000) -> Optional[Dict]:
    """Get comprehensive whale activity analysis."""
    return get_tracker().get_whale_analysis(min_value)


def get_coin_flow(symbol: str) -> Optional[Dict]:
    """Get exchange flow for a specific coin."""
    return get_tracker().get_coin_flow_analysis(symbol)


def get_whale_alerts() -> List[Dict]:
    """Get current whale alerts."""
    return get_tracker().get_whale_alerts()
