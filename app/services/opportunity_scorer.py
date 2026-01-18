"""
Crypto Sentiment Dashboard - Opportunity Scoring Algorithm

Calculates composite opportunity scores (0-100) for cryptocurrencies
based on multiple factors including sentiment, technical indicators,
whale activity, and development metrics.
"""

import logging
from datetime import datetime
from typing import Dict, List, Optional
from dataclasses import dataclass

from app.utils.cache import cached

logger = logging.getLogger(__name__)


@dataclass
class ScoreFactor:
    """Individual scoring factor with weight and value."""
    name: str
    value: float  # 0-100
    weight: float  # 0-1
    signal: str  # BULLISH, BEARISH, NEUTRAL
    details: str


class OpportunityScorer:
    """
    Calculates composite opportunity scores for crypto assets.

    Factors considered:
    1. Market Sentiment (Fear & Greed, social sentiment)
    2. Technical Indicators (RSI, MACD, trends)
    3. Whale Activity (accumulation vs distribution)
    4. Development Activity (GitHub commits, contributors)
    5. Volume Analysis (unusual volume, trend)
    6. Price Action (momentum, support/resistance)
    """

    # Factor weights (must sum to 1.0)
    WEIGHTS = {
        'sentiment': 0.20,
        'technical': 0.25,
        'whale_activity': 0.15,
        'development': 0.10,
        'volume': 0.15,
        'price_action': 0.15
    }

    # Thresholds for opportunity classification
    THRESHOLDS = {
        'strong_buy': 80,
        'buy': 65,
        'neutral_high': 55,
        'neutral_low': 45,
        'sell': 35,
        'strong_sell': 20
    }

    def __init__(self):
        self._cached_scores = {}

    def calculate_score(
        self,
        sentiment_data: Optional[Dict] = None,
        technical_data: Optional[Dict] = None,
        whale_data: Optional[Dict] = None,
        development_data: Optional[Dict] = None,
        volume_data: Optional[Dict] = None,
        price_data: Optional[Dict] = None
    ) -> Dict:
        """
        Calculate composite opportunity score.

        Returns:
            Composite score with breakdown by factor
        """
        factors = []

        # 1. Sentiment Score
        sentiment_factor = self._score_sentiment(sentiment_data)
        factors.append(sentiment_factor)

        # 2. Technical Score
        technical_factor = self._score_technical(technical_data)
        factors.append(technical_factor)

        # 3. Whale Activity Score
        whale_factor = self._score_whale_activity(whale_data)
        factors.append(whale_factor)

        # 4. Development Score
        dev_factor = self._score_development(development_data)
        factors.append(dev_factor)

        # 5. Volume Score
        volume_factor = self._score_volume(volume_data)
        factors.append(volume_factor)

        # 6. Price Action Score
        price_factor = self._score_price_action(price_data)
        factors.append(price_factor)

        # Calculate weighted composite score
        composite_score = sum(f.value * f.weight for f in factors)

        # Determine overall signal
        signal = self._determine_signal(composite_score)

        # Calculate confidence based on factor agreement
        confidence = self._calculate_confidence(factors)

        return {
            'timestamp': datetime.utcnow().isoformat(),
            'composite_score': round(composite_score, 1),
            'signal': signal['signal'],
            'signal_strength': signal['strength'],
            'recommendation': signal['recommendation'],
            'confidence': confidence,
            'factors': [
                {
                    'name': f.name,
                    'score': round(f.value, 1),
                    'weight': f.weight,
                    'weighted_score': round(f.value * f.weight, 1),
                    'signal': f.signal,
                    'details': f.details
                }
                for f in factors
            ],
            'risk_level': self._assess_risk_level(factors, composite_score),
            'summary': self._generate_summary(composite_score, factors, signal)
        }

    def _score_sentiment(self, data: Optional[Dict]) -> ScoreFactor:
        """Score based on market sentiment indicators."""
        if not data:
            return ScoreFactor(
                name='Market Sentiment',
                value=50,
                weight=self.WEIGHTS['sentiment'],
                signal='NEUTRAL',
                details='No sentiment data available'
            )

        fear_greed = data.get('fear_greed', {})
        fg_value = fear_greed.get('value', 50)

        # Contrarian approach: extreme fear = opportunity, extreme greed = caution
        if fg_value <= 20:
            score = 85  # Extreme fear = strong buy opportunity
            signal = 'BULLISH'
            details = f'Extreme Fear ({fg_value}) - Contrarian buy signal'
        elif fg_value <= 35:
            score = 70
            signal = 'BULLISH'
            details = f'Fear ({fg_value}) - Potential accumulation zone'
        elif fg_value <= 55:
            score = 50
            signal = 'NEUTRAL'
            details = f'Neutral sentiment ({fg_value})'
        elif fg_value <= 75:
            score = 35
            signal = 'BEARISH'
            details = f'Greed ({fg_value}) - Exercise caution'
        else:
            score = 20
            signal = 'BEARISH'
            details = f'Extreme Greed ({fg_value}) - High risk zone'

        # Adjust for social sentiment if available
        social_sentiment = data.get('social_sentiment', 0)
        if social_sentiment > 0.5:
            score = min(100, score + 5)
        elif social_sentiment < -0.5:
            score = max(0, score - 5)

        return ScoreFactor(
            name='Market Sentiment',
            value=score,
            weight=self.WEIGHTS['sentiment'],
            signal=signal,
            details=details
        )

    def _score_technical(self, data: Optional[Dict]) -> ScoreFactor:
        """Score based on technical indicators."""
        if not data:
            return ScoreFactor(
                name='Technical Analysis',
                value=50,
                weight=self.WEIGHTS['technical'],
                signal='NEUTRAL',
                details='No technical data available'
            )

        indicators = data.get('indicators', {})
        signals = []
        score = 50

        # RSI Analysis
        rsi_data = indicators.get('rsi', {})
        rsi = rsi_data.get('value') if isinstance(rsi_data, dict) else rsi_data
        if rsi is not None:
            if rsi <= 30:
                signals.append(('RSI', 'BULLISH', 'Oversold'))
                score += 15
            elif rsi >= 70:
                signals.append(('RSI', 'BEARISH', 'Overbought'))
                score -= 15
            else:
                signals.append(('RSI', 'NEUTRAL', 'Normal range'))

        # MACD Analysis
        macd = indicators.get('macd', {})
        if macd:
            histogram = macd.get('histogram', 0)
            trend = macd.get('trend', '')
            if histogram > 0 or trend == 'BULLISH':
                signals.append(('MACD', 'BULLISH', 'Positive momentum'))
                score += 10
            elif histogram < 0 or trend == 'BEARISH':
                signals.append(('MACD', 'BEARISH', 'Negative momentum'))
                score -= 10

        # Bollinger Bands
        bb = indicators.get('bollinger_bands', {})
        if bb:
            bb_signal = bb.get('signal', '')
            if 'LOWER' in bb_signal:
                signals.append(('Bollinger', 'BULLISH', 'Near lower band'))
                score += 10
            elif 'UPPER' in bb_signal:
                signals.append(('Bollinger', 'BEARISH', 'Near upper band'))
                score -= 10

        # Clamp score
        score = max(0, min(100, score))

        # Determine overall signal
        bullish_count = sum(1 for s in signals if s[1] == 'BULLISH')
        bearish_count = sum(1 for s in signals if s[1] == 'BEARISH')

        if bullish_count > bearish_count:
            signal = 'BULLISH'
        elif bearish_count > bullish_count:
            signal = 'BEARISH'
        else:
            signal = 'NEUTRAL'

        details = ', '.join([f"{s[0]}: {s[2]}" for s in signals]) or 'Limited data'

        return ScoreFactor(
            name='Technical Analysis',
            value=score,
            weight=self.WEIGHTS['technical'],
            signal=signal,
            details=details
        )

    def _score_whale_activity(self, data: Optional[Dict]) -> ScoreFactor:
        """Score based on whale transaction patterns."""
        if not data or data.get('configured') == False:
            return ScoreFactor(
                name='Whale Activity',
                value=50,
                weight=self.WEIGHTS['whale_activity'],
                signal='NEUTRAL',
                details='Whale tracking not available'
            )

        score = 50
        details_parts = []

        # Analyze exchange flows
        exchange_inflow = data.get('exchange_inflow', 0)
        exchange_outflow = data.get('exchange_outflow', 0)

        if exchange_outflow > exchange_inflow * 1.5:
            score += 20
            details_parts.append('Strong outflows (accumulation)')
            signal = 'BULLISH'
        elif exchange_inflow > exchange_outflow * 1.5:
            score -= 20
            details_parts.append('Strong inflows (distribution)')
            signal = 'BEARISH'
        else:
            details_parts.append('Balanced flows')
            signal = 'NEUTRAL'

        # Analyze transaction size trend
        large_tx_count = data.get('large_transaction_count', 0)
        if large_tx_count > 10:
            score += 10
            details_parts.append(f'{large_tx_count} large transactions')

        score = max(0, min(100, score))

        return ScoreFactor(
            name='Whale Activity',
            value=score,
            weight=self.WEIGHTS['whale_activity'],
            signal=signal,
            details=', '.join(details_parts) or 'Normal activity'
        )

    def _score_development(self, data: Optional[Dict]) -> ScoreFactor:
        """Score based on development activity."""
        if not data:
            return ScoreFactor(
                name='Development Activity',
                value=50,
                weight=self.WEIGHTS['development'],
                signal='NEUTRAL',
                details='No development data available'
            )

        activity_score = data.get('activity_score', 50)
        commits_week = data.get('commits_last_week', 0)
        contributors = data.get('contributor_count', 0)

        # Normalize to 0-100
        score = min(100, activity_score)

        if score >= 70:
            signal = 'BULLISH'
            details = f'High activity: {commits_week} commits/week, {contributors} contributors'
        elif score >= 40:
            signal = 'NEUTRAL'
            details = f'Moderate activity: {commits_week} commits/week'
        else:
            signal = 'BEARISH'
            details = f'Low activity: {commits_week} commits/week'

        return ScoreFactor(
            name='Development Activity',
            value=score,
            weight=self.WEIGHTS['development'],
            signal=signal,
            details=details
        )

    def _score_volume(self, data: Optional[Dict]) -> ScoreFactor:
        """Score based on volume analysis."""
        if not data:
            return ScoreFactor(
                name='Volume Analysis',
                value=50,
                weight=self.WEIGHTS['volume'],
                signal='NEUTRAL',
                details='No volume data available'
            )

        volume_change = data.get('volume_change_24h', 0)
        avg_volume_ratio = data.get('volume_to_avg_ratio', 1)

        score = 50
        details_parts = []

        # High volume with price increase = bullish
        # High volume with price decrease = bearish
        price_change = data.get('price_change_24h', 0)

        if avg_volume_ratio > 2:
            if price_change > 0:
                score = 75
                signal = 'BULLISH'
                details_parts.append('Unusually high volume on uptrend')
            else:
                score = 30
                signal = 'BEARISH'
                details_parts.append('Unusually high volume on downtrend')
        elif avg_volume_ratio > 1.5:
            score = 60 if price_change > 0 else 40
            signal = 'NEUTRAL'
            details_parts.append('Above average volume')
        else:
            signal = 'NEUTRAL'
            details_parts.append('Normal volume')

        return ScoreFactor(
            name='Volume Analysis',
            value=score,
            weight=self.WEIGHTS['volume'],
            signal=signal,
            details=', '.join(details_parts)
        )

    def _score_price_action(self, data: Optional[Dict]) -> ScoreFactor:
        """Score based on price action and momentum."""
        if not data:
            return ScoreFactor(
                name='Price Action',
                value=50,
                weight=self.WEIGHTS['price_action'],
                signal='NEUTRAL',
                details='No price data available'
            )

        price_change_24h = data.get('price_change_24h', 0)
        price_change_7d = data.get('price_change_7d', 0)

        score = 50

        # Short-term momentum
        if price_change_24h > 10:
            score += 15
        elif price_change_24h > 5:
            score += 10
        elif price_change_24h < -10:
            score -= 15
        elif price_change_24h < -5:
            score -= 10

        # Weekly trend
        if price_change_7d > 20:
            score += 10
        elif price_change_7d < -20:
            score -= 10

        score = max(0, min(100, score))

        if score >= 60:
            signal = 'BULLISH'
            details = f'Positive momentum: 24h {price_change_24h:+.1f}%, 7d {price_change_7d:+.1f}%'
        elif score <= 40:
            signal = 'BEARISH'
            details = f'Negative momentum: 24h {price_change_24h:+.1f}%, 7d {price_change_7d:+.1f}%'
        else:
            signal = 'NEUTRAL'
            details = f'Mixed signals: 24h {price_change_24h:+.1f}%, 7d {price_change_7d:+.1f}%'

        return ScoreFactor(
            name='Price Action',
            value=score,
            weight=self.WEIGHTS['price_action'],
            signal=signal,
            details=details
        )

    def _determine_signal(self, score: float) -> Dict:
        """Determine trading signal from composite score."""
        if score >= self.THRESHOLDS['strong_buy']:
            return {
                'signal': 'STRONG_BUY',
                'strength': 'HIGH',
                'recommendation': 'Strong buying opportunity identified'
            }
        elif score >= self.THRESHOLDS['buy']:
            return {
                'signal': 'BUY',
                'strength': 'MODERATE',
                'recommendation': 'Favorable conditions for accumulation'
            }
        elif score >= self.THRESHOLDS['neutral_high']:
            return {
                'signal': 'HOLD',
                'strength': 'LOW',
                'recommendation': 'Slightly bullish, monitor for better entry'
            }
        elif score >= self.THRESHOLDS['neutral_low']:
            return {
                'signal': 'HOLD',
                'strength': 'NEUTRAL',
                'recommendation': 'No clear direction, wait for confirmation'
            }
        elif score >= self.THRESHOLDS['sell']:
            return {
                'signal': 'HOLD',
                'strength': 'LOW',
                'recommendation': 'Slightly bearish, consider reducing exposure'
            }
        elif score >= self.THRESHOLDS['strong_sell']:
            return {
                'signal': 'SELL',
                'strength': 'MODERATE',
                'recommendation': 'Unfavorable conditions, consider taking profits'
            }
        else:
            return {
                'signal': 'STRONG_SELL',
                'strength': 'HIGH',
                'recommendation': 'High risk detected, strongly consider exiting'
            }

    def _calculate_confidence(self, factors: List[ScoreFactor]) -> Dict:
        """Calculate confidence based on factor agreement."""
        signals = [f.signal for f in factors]
        bullish = signals.count('BULLISH')
        bearish = signals.count('BEARISH')
        total = len(signals)

        if bullish >= 4 or bearish >= 4:
            level = 'HIGH'
            percentage = 85
        elif bullish >= 3 or bearish >= 3:
            level = 'MODERATE'
            percentage = 65
        else:
            level = 'LOW'
            percentage = 45

        return {
            'level': level,
            'percentage': percentage,
            'agreement': {
                'bullish': bullish,
                'bearish': bearish,
                'neutral': total - bullish - bearish
            }
        }

    def _assess_risk_level(self, factors: List[ScoreFactor], score: float) -> Dict:
        """Assess overall risk level."""
        # High risk if score is extreme or factors disagree
        signals = [f.signal for f in factors]
        bullish = signals.count('BULLISH')
        bearish = signals.count('BEARISH')

        disagreement = min(bullish, bearish)

        if score > 85 or score < 15:
            level = 'HIGH'
            reason = 'Extreme score indicates potential volatility'
        elif disagreement >= 2:
            level = 'MODERATE'
            reason = 'Mixed signals from indicators'
        elif score > 75 or score < 25:
            level = 'MODERATE'
            reason = 'Strong directional bias'
        else:
            level = 'LOW'
            reason = 'Balanced market conditions'

        return {
            'level': level,
            'reason': reason
        }

    def _generate_summary(self, score: float, factors: List[ScoreFactor], signal: Dict) -> str:
        """Generate human-readable summary."""
        bullish_factors = [f.name for f in factors if f.signal == 'BULLISH']
        bearish_factors = [f.name for f in factors if f.signal == 'BEARISH']

        parts = [f"Opportunity Score: {score:.0f}/100 ({signal['signal']})"]

        if bullish_factors:
            parts.append(f"Bullish: {', '.join(bullish_factors)}")
        if bearish_factors:
            parts.append(f"Bearish: {', '.join(bearish_factors)}")

        parts.append(signal['recommendation'])

        return '. '.join(parts)


# Global scorer instance
_scorer: Optional[OpportunityScorer] = None


def get_scorer() -> OpportunityScorer:
    """Get or create the global opportunity scorer."""
    global _scorer
    if _scorer is None:
        _scorer = OpportunityScorer()
    return _scorer


def calculate_opportunity_score(
    sentiment_data: Optional[Dict] = None,
    technical_data: Optional[Dict] = None,
    whale_data: Optional[Dict] = None,
    development_data: Optional[Dict] = None,
    volume_data: Optional[Dict] = None,
    price_data: Optional[Dict] = None
) -> Dict:
    """Calculate composite opportunity score."""
    return get_scorer().calculate_score(
        sentiment_data=sentiment_data,
        technical_data=technical_data,
        whale_data=whale_data,
        development_data=development_data,
        volume_data=volume_data,
        price_data=price_data
    )
