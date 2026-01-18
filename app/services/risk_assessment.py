"""
Crypto Sentiment Dashboard - Risk Assessment Service

Evaluates and monitors risk indicators including volatility,
liquidity, concentration risk, and market manipulation signals.
"""

import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional
from dataclasses import dataclass
from enum import Enum

from app.utils.cache import cached

logger = logging.getLogger(__name__)


class RiskLevel(Enum):
    """Risk severity levels."""
    MINIMAL = 'minimal'
    LOW = 'low'
    MODERATE = 'moderate'
    HIGH = 'high'
    EXTREME = 'extreme'


@dataclass
class RiskIndicator:
    """Individual risk indicator."""
    name: str
    category: str
    level: RiskLevel
    score: float  # 0-100, higher = more risk
    description: str
    recommendation: str


class RiskAssessment:
    """
    Comprehensive risk assessment for crypto assets.

    Risk Categories:
    1. Volatility Risk - Price movement unpredictability
    2. Liquidity Risk - Ability to enter/exit positions
    3. Market Risk - Overall market conditions
    4. Concentration Risk - Whale holdings, exchange concentration
    5. Technical Risk - Bearish technical patterns
    6. Sentiment Risk - Extreme market sentiment
    """

    # Risk thresholds
    VOLATILITY_THRESHOLDS = {
        'minimal': 0.02,
        'low': 0.05,
        'moderate': 0.10,
        'high': 0.20,
        'extreme': 0.30
    }

    def __init__(self):
        self._risk_weights = {
            'volatility': 0.25,
            'liquidity': 0.15,
            'market': 0.20,
            'concentration': 0.15,
            'technical': 0.15,
            'sentiment': 0.10
        }

    def assess_risk(
        self,
        price_data: Optional[Dict] = None,
        volume_data: Optional[Dict] = None,
        market_data: Optional[Dict] = None,
        whale_data: Optional[Dict] = None,
        technical_data: Optional[Dict] = None,
        sentiment_data: Optional[Dict] = None
    ) -> Dict:
        """
        Perform comprehensive risk assessment.

        Returns:
            Complete risk assessment with indicators and recommendations
        """
        indicators = []

        # 1. Volatility Risk
        volatility_risk = self._assess_volatility(price_data)
        indicators.append(volatility_risk)

        # 2. Liquidity Risk
        liquidity_risk = self._assess_liquidity(volume_data, market_data)
        indicators.append(liquidity_risk)

        # 3. Market Risk
        market_risk = self._assess_market_risk(market_data, sentiment_data)
        indicators.append(market_risk)

        # 4. Concentration Risk
        concentration_risk = self._assess_concentration(whale_data)
        indicators.append(concentration_risk)

        # 5. Technical Risk
        technical_risk = self._assess_technical_risk(technical_data)
        indicators.append(technical_risk)

        # 6. Sentiment Risk
        sentiment_risk = self._assess_sentiment_risk(sentiment_data)
        indicators.append(sentiment_risk)

        # Calculate composite risk score
        composite_score = self._calculate_composite_score(indicators)
        overall_level = self._determine_risk_level(composite_score)

        # Generate warnings
        warnings = self._generate_warnings(indicators)

        # Generate recommendations
        recommendations = self._generate_recommendations(indicators, overall_level)

        return {
            'timestamp': datetime.utcnow().isoformat(),
            'overall_risk': {
                'level': overall_level.value,
                'score': round(composite_score, 1),
                'description': self._get_risk_description(overall_level)
            },
            'indicators': [
                {
                    'name': ind.name,
                    'category': ind.category,
                    'level': ind.level.value,
                    'score': round(ind.score, 1),
                    'description': ind.description,
                    'recommendation': ind.recommendation
                }
                for ind in indicators
            ],
            'warnings': warnings,
            'recommendations': recommendations,
            'risk_breakdown': self._get_risk_breakdown(indicators)
        }

    def _assess_volatility(self, price_data: Optional[Dict]) -> RiskIndicator:
        """Assess volatility risk."""
        if not price_data:
            return RiskIndicator(
                name='Volatility',
                category='volatility',
                level=RiskLevel.MODERATE,
                score=50,
                description='Unable to assess volatility - no price data',
                recommendation='Monitor price movements closely'
            )

        volatility = price_data.get('volatility', 0)
        price_change_24h = abs(price_data.get('price_change_24h', 0))
        price_change_7d = abs(price_data.get('price_change_7d', 0))

        # Calculate volatility score (0-100)
        score = min(100, (
            (volatility * 200) +  # Daily volatility contribution
            (price_change_24h * 2) +  # 24h change contribution
            (price_change_7d * 0.5)  # 7d change contribution
        ))

        level = self._score_to_level(score)

        descriptions = {
            RiskLevel.MINIMAL: 'Very stable price action',
            RiskLevel.LOW: 'Normal market volatility',
            RiskLevel.MODERATE: 'Elevated volatility - expect price swings',
            RiskLevel.HIGH: 'High volatility - significant price movements likely',
            RiskLevel.EXTREME: 'Extreme volatility - exercise caution'
        }

        recommendations = {
            RiskLevel.MINIMAL: 'Good conditions for position building',
            RiskLevel.LOW: 'Standard risk management sufficient',
            RiskLevel.MODERATE: 'Consider tighter stop-losses',
            RiskLevel.HIGH: 'Reduce position size, use wider stops',
            RiskLevel.EXTREME: 'Avoid large positions, wait for stability'
        }

        return RiskIndicator(
            name='Volatility Risk',
            category='volatility',
            level=level,
            score=score,
            description=descriptions[level],
            recommendation=recommendations[level]
        )

    def _assess_liquidity(self, volume_data: Optional[Dict], market_data: Optional[Dict]) -> RiskIndicator:
        """Assess liquidity risk."""
        if not volume_data and not market_data:
            return RiskIndicator(
                name='Liquidity',
                category='liquidity',
                level=RiskLevel.MODERATE,
                score=50,
                description='Unable to assess liquidity',
                recommendation='Be cautious with large orders'
            )

        volume_24h = (volume_data or {}).get('total_volume', 0)
        market_cap = (market_data or {}).get('market_cap', 0)

        # Volume to market cap ratio (higher is better)
        if market_cap > 0:
            vol_ratio = volume_24h / market_cap
        else:
            vol_ratio = 0

        # Lower ratio = higher risk
        if vol_ratio >= 0.1:
            score = 20
            level = RiskLevel.LOW
        elif vol_ratio >= 0.05:
            score = 40
            level = RiskLevel.MODERATE
        elif vol_ratio >= 0.02:
            score = 60
            level = RiskLevel.MODERATE
        elif vol_ratio >= 0.01:
            score = 75
            level = RiskLevel.HIGH
        else:
            score = 90
            level = RiskLevel.EXTREME

        descriptions = {
            RiskLevel.MINIMAL: 'Excellent liquidity',
            RiskLevel.LOW: 'Good liquidity for most position sizes',
            RiskLevel.MODERATE: 'Adequate liquidity - large orders may cause slippage',
            RiskLevel.HIGH: 'Low liquidity - expect significant slippage',
            RiskLevel.EXTREME: 'Very low liquidity - difficult to exit positions'
        }

        return RiskIndicator(
            name='Liquidity Risk',
            category='liquidity',
            level=level,
            score=score,
            description=descriptions.get(level, 'Unknown'),
            recommendation='Use limit orders for large positions' if score > 50 else 'Market orders acceptable'
        )

    def _assess_market_risk(self, market_data: Optional[Dict], sentiment_data: Optional[Dict]) -> RiskIndicator:
        """Assess overall market risk."""
        score = 50
        factors = []

        if market_data:
            # Market trend
            btc_dominance = market_data.get('btc_dominance', 50)
            if btc_dominance > 60:
                score += 10
                factors.append('High BTC dominance (risk-off)')
            elif btc_dominance < 40:
                score -= 5
                factors.append('Low BTC dominance (risk-on)')

            # Total market cap trend
            market_change = market_data.get('market_cap_change_24h', 0)
            if market_change < -5:
                score += 15
                factors.append('Market declining')
            elif market_change > 5:
                score -= 10
                factors.append('Market expanding')

        if sentiment_data:
            fear_greed = sentiment_data.get('fear_greed', {})
            fg_value = fear_greed.get('value', 50) if isinstance(fear_greed, dict) else 50

            if fg_value < 25:
                score += 20
                factors.append('Extreme fear environment')
            elif fg_value > 75:
                score += 15
                factors.append('Extreme greed (potential correction)')

        score = max(0, min(100, score))
        level = self._score_to_level(score)

        return RiskIndicator(
            name='Market Risk',
            category='market',
            level=level,
            score=score,
            description=', '.join(factors) if factors else 'Normal market conditions',
            recommendation='Hedge exposure' if score > 60 else 'Standard positioning acceptable'
        )

    def _assess_concentration(self, whale_data: Optional[Dict]) -> RiskIndicator:
        """Assess concentration risk from whale holdings."""
        if not whale_data or whale_data.get('configured') == False:
            return RiskIndicator(
                name='Concentration Risk',
                category='concentration',
                level=RiskLevel.MODERATE,
                score=50,
                description='Whale data not available',
                recommendation='Monitor large transactions manually'
            )

        score = 30  # Base score

        # Exchange concentration
        exchange_ratio = whale_data.get('exchange_concentration', 0)
        if exchange_ratio > 0.3:
            score += 30
        elif exchange_ratio > 0.2:
            score += 15

        # Large holder activity
        large_tx_count = whale_data.get('large_transaction_count', 0)
        if large_tx_count > 20:
            score += 20
        elif large_tx_count > 10:
            score += 10

        # Net flow direction
        inflow = whale_data.get('exchange_inflow', 0)
        outflow = whale_data.get('exchange_outflow', 0)
        if inflow > outflow * 2:
            score += 20  # Heavy selling pressure

        score = max(0, min(100, score))
        level = self._score_to_level(score)

        return RiskIndicator(
            name='Concentration Risk',
            category='concentration',
            level=level,
            score=score,
            description='Whale accumulation detected' if outflow > inflow else 'Normal whale activity',
            recommendation='Watch for large sell orders' if score > 60 else 'No immediate concerns'
        )

    def _assess_technical_risk(self, technical_data: Optional[Dict]) -> RiskIndicator:
        """Assess risk from technical indicators."""
        if not technical_data:
            return RiskIndicator(
                name='Technical Risk',
                category='technical',
                level=RiskLevel.MODERATE,
                score=50,
                description='Technical data not available',
                recommendation='Use basic support/resistance levels'
            )

        indicators = technical_data.get('indicators', {})
        score = 50
        signals = []

        # RSI risk
        rsi = indicators.get('rsi', {})
        rsi_value = rsi.get('value') if isinstance(rsi, dict) else rsi
        if rsi_value:
            if rsi_value > 80:
                score += 25
                signals.append('RSI overbought')
            elif rsi_value > 70:
                score += 10
                signals.append('RSI elevated')
            elif rsi_value < 20:
                signals.append('RSI extremely oversold')
            elif rsi_value < 30:
                signals.append('RSI oversold')

        # MACD risk
        macd = indicators.get('macd', {})
        if macd:
            trend = macd.get('trend', '')
            if trend == 'BEARISH':
                score += 15
                signals.append('MACD bearish')

        # Bollinger risk
        bb = indicators.get('bollinger_bands', {})
        if bb:
            bb_signal = bb.get('signal', '')
            if 'UPPER' in bb_signal:
                score += 15
                signals.append('At upper Bollinger band')

        score = max(0, min(100, score))
        level = self._score_to_level(score)

        return RiskIndicator(
            name='Technical Risk',
            category='technical',
            level=level,
            score=score,
            description=', '.join(signals) if signals else 'Neutral technical setup',
            recommendation='Wait for better entry' if score > 60 else 'Technical setup acceptable'
        )

    def _assess_sentiment_risk(self, sentiment_data: Optional[Dict]) -> RiskIndicator:
        """Assess risk from extreme sentiment."""
        if not sentiment_data:
            return RiskIndicator(
                name='Sentiment Risk',
                category='sentiment',
                level=RiskLevel.MODERATE,
                score=50,
                description='Sentiment data not available',
                recommendation='Monitor social media sentiment'
            )

        fear_greed = sentiment_data.get('fear_greed', {})
        fg_value = fear_greed.get('value', 50) if isinstance(fear_greed, dict) else 50

        # Extreme sentiment is risky (either direction)
        distance_from_neutral = abs(fg_value - 50)

        if distance_from_neutral <= 10:
            score = 20
            level = RiskLevel.LOW
            description = 'Neutral sentiment - balanced market'
        elif distance_from_neutral <= 20:
            score = 40
            level = RiskLevel.MODERATE
            description = 'Moderate sentiment bias'
        elif distance_from_neutral <= 30:
            score = 60
            level = RiskLevel.MODERATE
            description = 'Strong sentiment bias - potential reversal zone'
        else:
            score = 80
            level = RiskLevel.HIGH
            description = 'Extreme sentiment - high reversal probability'

        recommendation = 'Consider contrarian positioning' if score > 50 else 'Sentiment supports current trend'

        return RiskIndicator(
            name='Sentiment Risk',
            category='sentiment',
            level=level,
            score=score,
            description=description,
            recommendation=recommendation
        )

    def _calculate_composite_score(self, indicators: List[RiskIndicator]) -> float:
        """Calculate weighted composite risk score."""
        total_score = 0
        total_weight = 0

        for indicator in indicators:
            weight = self._risk_weights.get(indicator.category, 0.1)
            total_score += indicator.score * weight
            total_weight += weight

        return total_score / total_weight if total_weight > 0 else 50

    def _score_to_level(self, score: float) -> RiskLevel:
        """Convert numeric score to risk level."""
        if score <= 20:
            return RiskLevel.MINIMAL
        elif score <= 40:
            return RiskLevel.LOW
        elif score <= 60:
            return RiskLevel.MODERATE
        elif score <= 80:
            return RiskLevel.HIGH
        else:
            return RiskLevel.EXTREME

    def _determine_risk_level(self, score: float) -> RiskLevel:
        """Determine overall risk level from composite score."""
        return self._score_to_level(score)

    def _get_risk_description(self, level: RiskLevel) -> str:
        """Get description for risk level."""
        descriptions = {
            RiskLevel.MINIMAL: 'Very low risk environment - favorable conditions',
            RiskLevel.LOW: 'Low risk - normal market conditions',
            RiskLevel.MODERATE: 'Moderate risk - exercise standard caution',
            RiskLevel.HIGH: 'High risk - reduce exposure and use tight risk management',
            RiskLevel.EXTREME: 'Extreme risk - consider reducing positions significantly'
        }
        return descriptions.get(level, 'Unknown risk level')

    def _generate_warnings(self, indicators: List[RiskIndicator]) -> List[Dict]:
        """Generate specific warnings from indicators."""
        warnings = []

        for indicator in indicators:
            if indicator.level in [RiskLevel.HIGH, RiskLevel.EXTREME]:
                warnings.append({
                    'category': indicator.category,
                    'level': indicator.level.value,
                    'message': f"{indicator.name}: {indicator.description}",
                    'action': indicator.recommendation
                })

        return warnings

    def _generate_recommendations(self, indicators: List[RiskIndicator], overall_level: RiskLevel) -> List[str]:
        """Generate actionable recommendations."""
        recommendations = []

        if overall_level == RiskLevel.EXTREME:
            recommendations.append('Consider moving to stablecoins or reducing exposure significantly')
            recommendations.append('Avoid opening new long positions')
            recommendations.append('Set tight stop-losses on existing positions')
        elif overall_level == RiskLevel.HIGH:
            recommendations.append('Reduce position sizes by 30-50%')
            recommendations.append('Use stop-losses on all positions')
            recommendations.append('Avoid leverage')
        elif overall_level == RiskLevel.MODERATE:
            recommendations.append('Standard risk management practices')
            recommendations.append('Consider hedging strategies')
        else:
            recommendations.append('Favorable risk environment for position building')
            recommendations.append('Standard position sizing acceptable')

        # Add specific recommendations from high-risk indicators
        for indicator in indicators:
            if indicator.level in [RiskLevel.HIGH, RiskLevel.EXTREME]:
                if indicator.recommendation not in recommendations:
                    recommendations.append(indicator.recommendation)

        return recommendations[:5]  # Limit to top 5

    def _get_risk_breakdown(self, indicators: List[RiskIndicator]) -> Dict:
        """Get risk breakdown by category."""
        breakdown = {}
        for indicator in indicators:
            breakdown[indicator.category] = {
                'level': indicator.level.value,
                'score': round(indicator.score, 1)
            }
        return breakdown


# Global instance
_assessment: Optional[RiskAssessment] = None


def get_risk_assessment() -> RiskAssessment:
    """Get or create the global risk assessment instance."""
    global _assessment
    if _assessment is None:
        _assessment = RiskAssessment()
    return _assessment


# Convenience functions
def assess_risk(
    price_data: Optional[Dict] = None,
    volume_data: Optional[Dict] = None,
    market_data: Optional[Dict] = None,
    whale_data: Optional[Dict] = None,
    technical_data: Optional[Dict] = None,
    sentiment_data: Optional[Dict] = None
) -> Dict:
    """Perform comprehensive risk assessment."""
    return get_risk_assessment().assess_risk(
        price_data=price_data,
        volume_data=volume_data,
        market_data=market_data,
        whale_data=whale_data,
        technical_data=technical_data,
        sentiment_data=sentiment_data
    )
