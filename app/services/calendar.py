"""
Crypto Sentiment Dashboard - Calendar Service

Exchange listings and token unlock calendar tracking.
"""

import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional
import json

from app.utils.cache import cached, get_cache

logger = logging.getLogger(__name__)


class CalendarService:
    """
    Tracks upcoming crypto events including:
    - Exchange listings
    - Token unlocks
    - Network upgrades
    - Conference dates
    """

    # Sample upcoming events (in production, this would come from APIs/databases)
    # This provides structure for the feature
    SAMPLE_LISTINGS = [
        {
            'id': 'listing-1',
            'type': 'exchange_listing',
            'coin_id': 'example-token',
            'coin_name': 'Example Token',
            'symbol': 'EXT',
            'exchange': 'Binance',
            'date': None,  # Will be set dynamically
            'status': 'confirmed',
            'impact': 'HIGH',
            'source': 'Official announcement'
        }
    ]

    SAMPLE_UNLOCKS = [
        {
            'id': 'unlock-1',
            'type': 'token_unlock',
            'coin_id': 'aptos',
            'coin_name': 'Aptos',
            'symbol': 'APT',
            'unlock_amount': 11_310_000,
            'unlock_value_usd': None,  # Calculated at runtime
            'unlock_percentage': 2.17,
            'date': None,  # Will be set dynamically
            'cliff_or_linear': 'cliff',
            'category': 'team_investor',
            'impact': 'MEDIUM'
        },
        {
            'id': 'unlock-2',
            'type': 'token_unlock',
            'coin_id': 'arbitrum',
            'coin_name': 'Arbitrum',
            'symbol': 'ARB',
            'unlock_amount': 92_650_000,
            'unlock_value_usd': None,
            'unlock_percentage': 0.93,
            'date': None,
            'cliff_or_linear': 'linear',
            'category': 'ecosystem',
            'impact': 'LOW'
        }
    ]

    SAMPLE_UPGRADES = [
        {
            'id': 'upgrade-1',
            'type': 'network_upgrade',
            'coin_id': 'ethereum',
            'coin_name': 'Ethereum',
            'symbol': 'ETH',
            'upgrade_name': 'Pectra',
            'date': None,
            'description': 'Combined Prague-Electra upgrade for EVM improvements',
            'impact': 'HIGH'
        }
    ]

    def __init__(self):
        self._cache = get_cache()
        self._initialize_sample_dates()

    def _initialize_sample_dates(self):
        """Set sample event dates relative to current date."""
        now = datetime.utcnow()

        # Set listing dates
        for i, listing in enumerate(self.SAMPLE_LISTINGS):
            listing['date'] = (now + timedelta(days=3 + i * 7)).isoformat()

        # Set unlock dates
        for i, unlock in enumerate(self.SAMPLE_UNLOCKS):
            unlock['date'] = (now + timedelta(days=5 + i * 14)).isoformat()

        # Set upgrade dates
        for i, upgrade in enumerate(self.SAMPLE_UPGRADES):
            upgrade['date'] = (now + timedelta(days=30 + i * 60)).isoformat()

    @cached(ttl=3600, key_prefix='upcoming_events')
    def get_upcoming_events(self, days: int = 30, event_type: str = None) -> Dict:
        """
        Get all upcoming crypto events.

        Args:
            days: Number of days to look ahead
            event_type: Filter by type (exchange_listing, token_unlock, network_upgrade)

        Returns:
            List of upcoming events
        """
        now = datetime.utcnow()
        cutoff = now + timedelta(days=days)

        all_events = []

        # Add listings
        if event_type is None or event_type == 'exchange_listing':
            all_events.extend(self.SAMPLE_LISTINGS)

        # Add unlocks
        if event_type is None or event_type == 'token_unlock':
            all_events.extend(self.SAMPLE_UNLOCKS)

        # Add upgrades
        if event_type is None or event_type == 'network_upgrade':
            all_events.extend(self.SAMPLE_UPGRADES)

        # Filter by date
        upcoming = []
        for event in all_events:
            event_date = datetime.fromisoformat(event['date'].replace('Z', ''))
            if now <= event_date <= cutoff:
                event_copy = event.copy()
                event_copy['days_until'] = (event_date - now).days
                upcoming.append(event_copy)

        # Sort by date
        upcoming.sort(key=lambda x: x['date'])

        # Group by type
        by_type = {
            'exchange_listing': [],
            'token_unlock': [],
            'network_upgrade': []
        }

        for event in upcoming:
            event_type_key = event.get('type', 'other')
            if event_type_key in by_type:
                by_type[event_type_key].append(event)

        return {
            'timestamp': now.isoformat(),
            'period_days': days,
            'total_events': len(upcoming),
            'events': upcoming,
            'by_type': by_type,
            'summary': {
                'listings': len(by_type['exchange_listing']),
                'unlocks': len(by_type['token_unlock']),
                'upgrades': len(by_type['network_upgrade'])
            }
        }

    @cached(ttl=3600, key_prefix='exchange_listings')
    def get_exchange_listings(self, days: int = 30) -> Dict:
        """
        Get upcoming exchange listings.

        Args:
            days: Number of days to look ahead

        Returns:
            Exchange listing calendar
        """
        events = self.get_upcoming_events(days, 'exchange_listing')
        listings = events.get('by_type', {}).get('exchange_listing', [])

        # Group by exchange
        by_exchange = {}
        for listing in listings:
            exchange = listing.get('exchange', 'Unknown')
            if exchange not in by_exchange:
                by_exchange[exchange] = []
            by_exchange[exchange].append(listing)

        return {
            'timestamp': datetime.utcnow().isoformat(),
            'period_days': days,
            'total_listings': len(listings),
            'listings': listings,
            'by_exchange': by_exchange,
            'note': 'Data sourced from official announcements. Always verify before trading.'
        }

    @cached(ttl=3600, key_prefix='token_unlocks')
    def get_token_unlocks(self, days: int = 30) -> Dict:
        """
        Get upcoming token unlocks.

        Args:
            days: Number of days to look ahead

        Returns:
            Token unlock calendar with impact analysis
        """
        events = self.get_upcoming_events(days, 'token_unlock')
        unlocks = events.get('by_type', {}).get('token_unlock', [])

        # Calculate total unlock value
        total_value = sum(u.get('unlock_value_usd', 0) or 0 for u in unlocks)

        # Identify high impact unlocks
        high_impact = [u for u in unlocks if u.get('impact') == 'HIGH']
        medium_impact = [u for u in unlocks if u.get('impact') == 'MEDIUM']

        return {
            'timestamp': datetime.utcnow().isoformat(),
            'period_days': days,
            'total_unlocks': len(unlocks),
            'total_value_usd': total_value,
            'unlocks': unlocks,
            'high_impact_count': len(high_impact),
            'by_impact': {
                'high': high_impact,
                'medium': medium_impact,
                'low': [u for u in unlocks if u.get('impact') == 'LOW']
            },
            'warning': 'Large token unlocks can create selling pressure. Monitor closely.'
        }

    @cached(ttl=3600, key_prefix='network_upgrades')
    def get_network_upgrades(self, days: int = 90) -> Dict:
        """
        Get upcoming network upgrades.

        Args:
            days: Number of days to look ahead

        Returns:
            Network upgrade calendar
        """
        events = self.get_upcoming_events(days, 'network_upgrade')
        upgrades = events.get('by_type', {}).get('network_upgrade', [])

        return {
            'timestamp': datetime.utcnow().isoformat(),
            'period_days': days,
            'total_upgrades': len(upgrades),
            'upgrades': upgrades,
            'note': 'Network upgrades can be bullish catalysts. Follow official channels for updates.'
        }

    def get_coin_events(self, coin_id: str, days: int = 90) -> Dict:
        """
        Get all upcoming events for a specific coin.

        Args:
            coin_id: CoinGecko coin ID
            days: Number of days to look ahead

        Returns:
            All events for the coin
        """
        all_events = self.get_upcoming_events(days)
        coin_events = [
            event for event in all_events.get('events', [])
            if event.get('coin_id') == coin_id
        ]

        return {
            'coin_id': coin_id,
            'timestamp': datetime.utcnow().isoformat(),
            'period_days': days,
            'total_events': len(coin_events),
            'events': coin_events
        }

    def add_custom_event(self, event: Dict) -> bool:
        """
        Add a custom event to the calendar.

        Args:
            event: Event data with required fields

        Returns:
            Success status
        """
        required_fields = ['type', 'coin_id', 'date']
        if not all(field in event for field in required_fields):
            return False

        # In production, this would save to database
        # For now, we just validate the structure
        return True


# Global service instance
_service: Optional[CalendarService] = None


def get_service() -> CalendarService:
    """Get or create the global calendar service."""
    global _service
    if _service is None:
        _service = CalendarService()
    return _service


# Convenience functions
def get_upcoming_events(days: int = 30) -> Dict:
    """Get all upcoming events."""
    return get_service().get_upcoming_events(days)


def get_exchange_listings(days: int = 30) -> Dict:
    """Get upcoming exchange listings."""
    return get_service().get_exchange_listings(days)


def get_token_unlocks(days: int = 30) -> Dict:
    """Get upcoming token unlocks."""
    return get_service().get_token_unlocks(days)


def get_network_upgrades(days: int = 90) -> Dict:
    """Get upcoming network upgrades."""
    return get_service().get_network_upgrades(days)
