"""
Crypto Sentiment Dashboard - Influencer Tracker

Tracks crypto influencer/celebrity mentions and sentiment.
"""

import logging
import os
from datetime import datetime, timedelta
from typing import Dict, List, Optional
import re

from app.utils.cache import cached
from app.utils.sentiment import get_analyzer

logger = logging.getLogger(__name__)


class InfluencerTracker:
    """
    Tracks crypto influencer activity and sentiment.

    In production, this would integrate with Twitter/X API, YouTube API, etc.
    Currently provides structure and sample data for the feature.
    """

    # Notable crypto influencers/celebrities (sample list)
    INFLUENCERS = {
        'elon_musk': {
            'name': 'Elon Musk',
            'handle': '@elonmusk',
            'platform': 'twitter',
            'followers': 170_000_000,
            'influence_score': 100,
            'category': 'celebrity',
            'associated_coins': ['dogecoin', 'bitcoin']
        },
        'michael_saylor': {
            'name': 'Michael Saylor',
            'handle': '@saylor',
            'platform': 'twitter',
            'followers': 3_500_000,
            'influence_score': 85,
            'category': 'institutional',
            'associated_coins': ['bitcoin']
        },
        'vitalik_buterin': {
            'name': 'Vitalik Buterin',
            'handle': '@VitalikButerin',
            'platform': 'twitter',
            'followers': 5_200_000,
            'influence_score': 95,
            'category': 'founder',
            'associated_coins': ['ethereum']
        },
        'cz_binance': {
            'name': 'CZ (Changpeng Zhao)',
            'handle': '@caborz',
            'platform': 'twitter',
            'followers': 8_900_000,
            'influence_score': 90,
            'category': 'exchange',
            'associated_coins': ['binancecoin']
        },
        'brian_armstrong': {
            'name': 'Brian Armstrong',
            'handle': '@brian_armstrong',
            'platform': 'twitter',
            'followers': 1_500_000,
            'influence_score': 80,
            'category': 'exchange',
            'associated_coins': ['bitcoin', 'ethereum']
        },
        'cathie_wood': {
            'name': 'Cathie Wood',
            'handle': '@CathieDWood',
            'platform': 'twitter',
            'followers': 1_600_000,
            'influence_score': 75,
            'category': 'institutional',
            'associated_coins': ['bitcoin', 'ethereum']
        },
        'raoul_pal': {
            'name': 'Raoul Pal',
            'handle': '@RaoulGMI',
            'platform': 'twitter',
            'followers': 1_100_000,
            'influence_score': 70,
            'category': 'analyst',
            'associated_coins': ['bitcoin', 'ethereum', 'solana']
        },
        'plan_b': {
            'name': 'PlanB',
            'handle': '@100trillionUSD',
            'platform': 'twitter',
            'followers': 1_900_000,
            'influence_score': 72,
            'category': 'analyst',
            'associated_coins': ['bitcoin']
        }
    }

    # Sample recent mentions (structure for real-time tracking)
    SAMPLE_MENTIONS = []

    def __init__(self):
        self._sentiment_analyzer = get_analyzer()
        self._generate_sample_mentions()

    def _generate_sample_mentions(self):
        """Generate sample mention data for demonstration."""
        now = datetime.utcnow()

        self.SAMPLE_MENTIONS = [
            {
                'id': 'mention-1',
                'influencer_id': 'elon_musk',
                'text': 'Dogecoin to the moon!',
                'coins_mentioned': ['dogecoin'],
                'timestamp': (now - timedelta(hours=2)).isoformat(),
                'engagement': {'likes': 450000, 'retweets': 85000, 'replies': 42000},
                'sentiment': 'BULLISH',
                'sentiment_score': 0.85
            },
            {
                'id': 'mention-2',
                'influencer_id': 'michael_saylor',
                'text': 'Bitcoin is digital property. The most secure network in history.',
                'coins_mentioned': ['bitcoin'],
                'timestamp': (now - timedelta(hours=6)).isoformat(),
                'engagement': {'likes': 28000, 'retweets': 5200, 'replies': 1800},
                'sentiment': 'BULLISH',
                'sentiment_score': 0.72
            },
            {
                'id': 'mention-3',
                'influencer_id': 'vitalik_buterin',
                'text': 'Excited about the upcoming network improvements.',
                'coins_mentioned': ['ethereum'],
                'timestamp': (now - timedelta(hours=12)).isoformat(),
                'engagement': {'likes': 45000, 'retweets': 8500, 'replies': 3200},
                'sentiment': 'BULLISH',
                'sentiment_score': 0.65
            }
        ]

    @cached(ttl=900, key_prefix='influencer_activity')
    def get_recent_activity(self, hours: int = 24) -> Dict:
        """
        Get recent influencer activity.

        Args:
            hours: Look back period in hours

        Returns:
            Recent influencer mentions and analysis
        """
        cutoff = datetime.utcnow() - timedelta(hours=hours)

        recent_mentions = []
        for mention in self.SAMPLE_MENTIONS:
            mention_time = datetime.fromisoformat(mention['timestamp'].replace('Z', ''))
            if mention_time >= cutoff:
                # Add influencer details
                influencer = self.INFLUENCERS.get(mention['influencer_id'], {})
                mention_copy = mention.copy()
                mention_copy['influencer'] = {
                    'name': influencer.get('name'),
                    'handle': influencer.get('handle'),
                    'influence_score': influencer.get('influence_score')
                }
                recent_mentions.append(mention_copy)

        # Sort by engagement
        recent_mentions.sort(
            key=lambda x: sum(x.get('engagement', {}).values()),
            reverse=True
        )

        # Aggregate sentiment
        bullish = sum(1 for m in recent_mentions if m.get('sentiment') == 'BULLISH')
        bearish = sum(1 for m in recent_mentions if m.get('sentiment') == 'BEARISH')

        # Coins mentioned
        coins_mentioned = {}
        for mention in recent_mentions:
            for coin in mention.get('coins_mentioned', []):
                if coin not in coins_mentioned:
                    coins_mentioned[coin] = {'count': 0, 'sentiment_sum': 0}
                coins_mentioned[coin]['count'] += 1
                coins_mentioned[coin]['sentiment_sum'] += mention.get('sentiment_score', 0)

        # Calculate average sentiment per coin
        for coin, data in coins_mentioned.items():
            data['avg_sentiment'] = round(data['sentiment_sum'] / data['count'], 2) if data['count'] > 0 else 0
            del data['sentiment_sum']

        return {
            'timestamp': datetime.utcnow().isoformat(),
            'period_hours': hours,
            'total_mentions': len(recent_mentions),
            'sentiment_summary': {
                'bullish': bullish,
                'bearish': bearish,
                'neutral': len(recent_mentions) - bullish - bearish,
                'overall': 'BULLISH' if bullish > bearish else 'BEARISH' if bearish > bullish else 'NEUTRAL'
            },
            'coins_mentioned': coins_mentioned,
            'mentions': recent_mentions,
            'note': 'Influencer sentiment can be a leading indicator but should not be the sole basis for trading decisions.'
        }

    def get_influencer_list(self, category: str = None) -> Dict:
        """
        Get list of tracked influencers.

        Args:
            category: Filter by category

        Returns:
            List of influencers
        """
        influencers = []

        for inf_id, inf_data in self.INFLUENCERS.items():
            if category is None or inf_data.get('category') == category:
                influencers.append({
                    'id': inf_id,
                    **inf_data
                })

        # Sort by influence score
        influencers.sort(key=lambda x: x.get('influence_score', 0), reverse=True)

        # Group by category
        by_category = {}
        for inf in influencers:
            cat = inf.get('category', 'other')
            if cat not in by_category:
                by_category[cat] = []
            by_category[cat].append(inf)

        return {
            'timestamp': datetime.utcnow().isoformat(),
            'total_influencers': len(influencers),
            'influencers': influencers,
            'by_category': by_category,
            'categories': list(by_category.keys())
        }

    @cached(ttl=1800, key_prefix='coin_influencer_sentiment')
    def get_coin_influencer_sentiment(self, coin_id: str) -> Dict:
        """
        Get influencer sentiment for a specific coin.

        Args:
            coin_id: Coin identifier

        Returns:
            Influencer sentiment analysis for the coin
        """
        # Find influencers associated with this coin
        relevant_influencers = []
        for inf_id, inf_data in self.INFLUENCERS.items():
            if coin_id in inf_data.get('associated_coins', []):
                relevant_influencers.append({
                    'id': inf_id,
                    'name': inf_data['name'],
                    'influence_score': inf_data['influence_score']
                })

        # Find recent mentions of this coin
        mentions = [
            m for m in self.SAMPLE_MENTIONS
            if coin_id in m.get('coins_mentioned', [])
        ]

        # Calculate sentiment
        if mentions:
            avg_sentiment = sum(m.get('sentiment_score', 0) for m in mentions) / len(mentions)
            total_engagement = sum(sum(m.get('engagement', {}).values()) for m in mentions)
        else:
            avg_sentiment = 0
            total_engagement = 0

        return {
            'coin_id': coin_id,
            'timestamp': datetime.utcnow().isoformat(),
            'relevant_influencers': relevant_influencers,
            'recent_mentions': len(mentions),
            'avg_sentiment_score': round(avg_sentiment, 2),
            'total_engagement': total_engagement,
            'sentiment_label': 'BULLISH' if avg_sentiment > 0.3 else 'BEARISH' if avg_sentiment < -0.3 else 'NEUTRAL'
        }

    def get_trending_topics(self) -> Dict:
        """
        Get trending topics from influencer mentions.

        Returns:
            Trending crypto topics
        """
        # Extract topics from recent mentions
        topics = {}

        for mention in self.SAMPLE_MENTIONS:
            for coin in mention.get('coins_mentioned', []):
                if coin not in topics:
                    topics[coin] = {
                        'mention_count': 0,
                        'total_engagement': 0,
                        'sentiment_scores': []
                    }
                topics[coin]['mention_count'] += 1
                topics[coin]['total_engagement'] += sum(mention.get('engagement', {}).values())
                topics[coin]['sentiment_scores'].append(mention.get('sentiment_score', 0))

        # Calculate averages and rank
        trending = []
        for topic, data in topics.items():
            avg_sentiment = sum(data['sentiment_scores']) / len(data['sentiment_scores']) if data['sentiment_scores'] else 0
            trending.append({
                'topic': topic,
                'mentions': data['mention_count'],
                'engagement': data['total_engagement'],
                'avg_sentiment': round(avg_sentiment, 2),
                'trend_score': data['mention_count'] * 100 + data['total_engagement'] / 1000
            })

        trending.sort(key=lambda x: x['trend_score'], reverse=True)

        return {
            'timestamp': datetime.utcnow().isoformat(),
            'trending_topics': trending[:10]
        }


# Global tracker instance
_tracker: Optional[InfluencerTracker] = None


def get_tracker() -> InfluencerTracker:
    """Get or create the global influencer tracker."""
    global _tracker
    if _tracker is None:
        _tracker = InfluencerTracker()
    return _tracker


# Convenience functions
def get_recent_activity(hours: int = 24) -> Dict:
    """Get recent influencer activity."""
    return get_tracker().get_recent_activity(hours)


def get_influencer_list() -> Dict:
    """Get list of tracked influencers."""
    return get_tracker().get_influencer_list()


def get_coin_influencer_sentiment(coin_id: str) -> Dict:
    """Get influencer sentiment for a coin."""
    return get_tracker().get_coin_influencer_sentiment(coin_id)
