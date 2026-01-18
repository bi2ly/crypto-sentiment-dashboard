"""
Crypto Sentiment Dashboard - Sector/Category Analysis

Analyzes cryptocurrency market by sectors and categories.
"""

import logging
from datetime import datetime
from typing import Dict, List, Optional
from collections import defaultdict

from app.api import coingecko
from app.utils.cache import cached

logger = logging.getLogger(__name__)


class SectorAnalyzer:
    """
    Cryptocurrency sector and category analysis.

    Provides:
    - Sector performance comparison
    - Category market cap analysis
    - Top performers by sector
    - Sector sentiment indicators
    """

    # Major crypto sectors/categories
    SECTORS = {
        'layer-1': {
            'name': 'Layer 1',
            'description': 'Base layer blockchain protocols',
            'coins': ['bitcoin', 'ethereum', 'solana', 'cardano', 'avalanche-2', 'polkadot']
        },
        'layer-2': {
            'name': 'Layer 2',
            'description': 'Scaling solutions',
            'coins': ['matic-network', 'arbitrum', 'optimism', 'immutable-x']
        },
        'defi': {
            'name': 'DeFi',
            'description': 'Decentralized finance protocols',
            'coins': ['uniswap', 'aave', 'chainlink', 'maker', 'compound-governance-token', 'curve-dao-token']
        },
        'exchange': {
            'name': 'Exchange Tokens',
            'description': 'Centralized exchange tokens',
            'coins': ['binancecoin', 'crypto-com-chain', 'kucoin-shares', 'ftx-token']
        },
        'gaming': {
            'name': 'Gaming & Metaverse',
            'description': 'Gaming and virtual world tokens',
            'coins': ['axie-infinity', 'the-sandbox', 'decentraland', 'gala', 'illuvium']
        },
        'meme': {
            'name': 'Meme Coins',
            'description': 'Community-driven meme tokens',
            'coins': ['dogecoin', 'shiba-inu', 'pepe', 'floki', 'bonk']
        },
        'ai': {
            'name': 'AI & Big Data',
            'description': 'Artificial intelligence tokens',
            'coins': ['render-token', 'fetch-ai', 'singularitynet', 'ocean-protocol', 'the-graph']
        },
        'privacy': {
            'name': 'Privacy',
            'description': 'Privacy-focused cryptocurrencies',
            'coins': ['monero', 'zcash', 'dash', 'secret']
        },
        'stablecoin': {
            'name': 'Stablecoins',
            'description': 'Price-stable cryptocurrencies',
            'coins': ['tether', 'usd-coin', 'dai', 'frax', 'true-usd']
        },
        'storage': {
            'name': 'Storage',
            'description': 'Decentralized storage solutions',
            'coins': ['filecoin', 'arweave', 'storj', 'siacoin']
        }
    }

    def __init__(self):
        self._coingecko = coingecko.get_client()

    @cached(ttl=600, key_prefix='sector_overview')
    def get_sector_overview(self) -> Dict:
        """
        Get overview of all sectors with performance metrics.

        Returns:
            Sector overview with market data
        """
        sectors_data = {}

        for sector_id, sector_info in self.SECTORS.items():
            sector_data = self._analyze_sector(sector_id, sector_info)
            if sector_data:
                sectors_data[sector_id] = sector_data

        # Sort by 24h performance
        sorted_sectors = sorted(
            sectors_data.items(),
            key=lambda x: x[1].get('avg_change_24h', 0),
            reverse=True
        )

        # Determine best and worst performers
        best_sector = sorted_sectors[0] if sorted_sectors else None
        worst_sector = sorted_sectors[-1] if sorted_sectors else None

        return {
            'timestamp': datetime.utcnow().isoformat(),
            'sectors': dict(sorted_sectors),
            'summary': {
                'total_sectors': len(sectors_data),
                'best_performer': {
                    'id': best_sector[0],
                    'name': best_sector[1]['name'],
                    'change_24h': best_sector[1]['avg_change_24h']
                } if best_sector else None,
                'worst_performer': {
                    'id': worst_sector[0],
                    'name': worst_sector[1]['name'],
                    'change_24h': worst_sector[1]['avg_change_24h']
                } if worst_sector else None
            }
        }

    def _analyze_sector(self, sector_id: str, sector_info: Dict) -> Optional[Dict]:
        """Analyze a single sector."""
        coins = sector_info.get('coins', [])
        if not coins:
            return None

        # Fetch market data for sector coins
        market_data = self._coingecko.get_market_data(coins)
        if not market_data:
            return None

        total_market_cap = 0
        total_volume = 0
        price_changes = []
        top_coins = []

        for coin in market_data:
            market_cap = coin.get('market_cap', 0) or 0
            volume = coin.get('total_volume', 0) or 0
            change_24h = coin.get('price_change_percentage_24h', 0) or 0

            total_market_cap += market_cap
            total_volume += volume
            price_changes.append(change_24h)

            top_coins.append({
                'id': coin.get('id'),
                'name': coin.get('name'),
                'symbol': coin.get('symbol'),
                'price': coin.get('current_price'),
                'change_24h': change_24h,
                'market_cap': market_cap,
                'image': coin.get('image')
            })

        # Sort by market cap
        top_coins.sort(key=lambda x: x['market_cap'], reverse=True)

        avg_change = sum(price_changes) / len(price_changes) if price_changes else 0

        # Determine sector sentiment
        if avg_change > 5:
            sentiment = 'VERY_BULLISH'
        elif avg_change > 2:
            sentiment = 'BULLISH'
        elif avg_change > -2:
            sentiment = 'NEUTRAL'
        elif avg_change > -5:
            sentiment = 'BEARISH'
        else:
            sentiment = 'VERY_BEARISH'

        return {
            'name': sector_info['name'],
            'description': sector_info['description'],
            'coin_count': len(top_coins),
            'total_market_cap': total_market_cap,
            'total_volume_24h': total_volume,
            'avg_change_24h': round(avg_change, 2),
            'sentiment': sentiment,
            'top_coins': top_coins[:5]
        }

    @cached(ttl=600, key_prefix='sector_detail')
    def get_sector_detail(self, sector_id: str) -> Optional[Dict]:
        """
        Get detailed analysis for a specific sector.

        Args:
            sector_id: Sector identifier

        Returns:
            Detailed sector analysis
        """
        if sector_id not in self.SECTORS:
            return None

        sector_info = self.SECTORS[sector_id]
        return self._analyze_sector(sector_id, sector_info)

    @cached(ttl=600, key_prefix='sector_comparison')
    def compare_sectors(self, sector_ids: List[str]) -> Dict:
        """
        Compare multiple sectors.

        Args:
            sector_ids: List of sector IDs to compare

        Returns:
            Comparison data
        """
        comparison = {}

        for sector_id in sector_ids:
            if sector_id in self.SECTORS:
                data = self.get_sector_detail(sector_id)
                if data:
                    comparison[sector_id] = {
                        'name': data['name'],
                        'market_cap': data['total_market_cap'],
                        'volume_24h': data['total_volume_24h'],
                        'change_24h': data['avg_change_24h'],
                        'sentiment': data['sentiment'],
                        'coin_count': data['coin_count']
                    }

        return {
            'timestamp': datetime.utcnow().isoformat(),
            'sectors': comparison
        }

    def get_sector_leaders(self, limit: int = 5) -> Dict:
        """
        Get top performing coins from each sector.

        Args:
            limit: Number of coins per sector

        Returns:
            Top performers by sector
        """
        overview = self.get_sector_overview()
        leaders = {}

        for sector_id, sector_data in overview.get('sectors', {}).items():
            top_coins = sector_data.get('top_coins', [])[:limit]
            if top_coins:
                # Sort by 24h change
                sorted_coins = sorted(top_coins, key=lambda x: x.get('change_24h', 0), reverse=True)
                leaders[sector_id] = {
                    'name': sector_data['name'],
                    'leaders': sorted_coins[:limit]
                }

        return {
            'timestamp': datetime.utcnow().isoformat(),
            'sectors': leaders
        }


# Global analyzer instance
_analyzer: Optional[SectorAnalyzer] = None


def get_analyzer() -> SectorAnalyzer:
    """Get or create the global sector analyzer."""
    global _analyzer
    if _analyzer is None:
        _analyzer = SectorAnalyzer()
    return _analyzer


# Convenience functions
def get_sector_overview() -> Dict:
    """Get overview of all sectors."""
    return get_analyzer().get_sector_overview()


def get_sector_detail(sector_id: str) -> Optional[Dict]:
    """Get detailed sector analysis."""
    return get_analyzer().get_sector_detail(sector_id)


def get_sector_leaders(limit: int = 5) -> Dict:
    """Get top performers by sector."""
    return get_analyzer().get_sector_leaders(limit)
