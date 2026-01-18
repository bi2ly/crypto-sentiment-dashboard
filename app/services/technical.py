"""
Crypto Sentiment Dashboard - Technical Indicators

Calculates RSI, MACD, Bollinger Bands, and other technical indicators.
"""

import logging
from typing import Dict, List, Optional, Tuple
from datetime import datetime, timedelta

from app.api import coingecko
from app.utils.cache import cached

logger = logging.getLogger(__name__)


class TechnicalAnalyzer:
    """
    Technical analysis calculator for cryptocurrency price data.
    """

    def __init__(self):
        self._coingecko = coingecko.get_client()

    def calculate_rsi(self, prices: List[float], period: int = 14) -> Optional[float]:
        """
        Calculate Relative Strength Index (RSI).

        RSI = 100 - (100 / (1 + RS))
        RS = Average Gain / Average Loss

        Args:
            prices: List of closing prices (oldest first)
            period: RSI period (default: 14)

        Returns:
            RSI value (0-100) or None if insufficient data
        """
        if len(prices) < period + 1:
            return None

        # Calculate price changes
        changes = [prices[i] - prices[i-1] for i in range(1, len(prices))]

        # Separate gains and losses
        gains = [max(0, c) for c in changes]
        losses = [abs(min(0, c)) for c in changes]

        # Calculate initial averages
        avg_gain = sum(gains[:period]) / period
        avg_loss = sum(losses[:period]) / period

        # Calculate smoothed averages for remaining periods
        for i in range(period, len(changes)):
            avg_gain = (avg_gain * (period - 1) + gains[i]) / period
            avg_loss = (avg_loss * (period - 1) + losses[i]) / period

        if avg_loss == 0:
            return 100.0

        rs = avg_gain / avg_loss
        rsi = 100 - (100 / (1 + rs))

        return round(rsi, 2)

    def calculate_macd(
        self,
        prices: List[float],
        fast_period: int = 12,
        slow_period: int = 26,
        signal_period: int = 9
    ) -> Optional[Dict[str, float]]:
        """
        Calculate MACD (Moving Average Convergence Divergence).

        MACD Line = EMA(fast) - EMA(slow)
        Signal Line = EMA(MACD Line)
        Histogram = MACD Line - Signal Line

        Args:
            prices: List of closing prices
            fast_period: Fast EMA period (default: 12)
            slow_period: Slow EMA period (default: 26)
            signal_period: Signal line period (default: 9)

        Returns:
            Dict with macd, signal, and histogram values
        """
        if len(prices) < slow_period + signal_period:
            return None

        # Calculate EMAs
        ema_fast = self._calculate_ema(prices, fast_period)
        ema_slow = self._calculate_ema(prices, slow_period)

        if ema_fast is None or ema_slow is None:
            return None

        # MACD line values
        macd_line = []
        for i in range(len(ema_slow)):
            fast_idx = i + (slow_period - fast_period)
            if fast_idx >= 0 and fast_idx < len(ema_fast):
                macd_line.append(ema_fast[fast_idx] - ema_slow[i])

        if len(macd_line) < signal_period:
            return None

        # Signal line (EMA of MACD)
        signal_line = self._calculate_ema(macd_line, signal_period)

        if signal_line is None or len(signal_line) == 0:
            return None

        # Current values
        macd_value = macd_line[-1]
        signal_value = signal_line[-1]
        histogram = macd_value - signal_value

        return {
            'macd': round(macd_value, 4),
            'signal': round(signal_value, 4),
            'histogram': round(histogram, 4),
            'trend': 'BULLISH' if histogram > 0 else 'BEARISH'
        }

    def _calculate_ema(self, data: List[float], period: int) -> Optional[List[float]]:
        """Calculate Exponential Moving Average."""
        if len(data) < period:
            return None

        multiplier = 2 / (period + 1)
        ema = [sum(data[:period]) / period]  # Start with SMA

        for price in data[period:]:
            ema.append((price - ema[-1]) * multiplier + ema[-1])

        return ema

    def calculate_sma(self, prices: List[float], period: int) -> Optional[float]:
        """Calculate Simple Moving Average."""
        if len(prices) < period:
            return None
        return round(sum(prices[-period:]) / period, 2)

    def calculate_bollinger_bands(
        self,
        prices: List[float],
        period: int = 20,
        std_dev: float = 2.0
    ) -> Optional[Dict[str, float]]:
        """
        Calculate Bollinger Bands.

        Args:
            prices: List of closing prices
            period: Moving average period
            std_dev: Standard deviation multiplier

        Returns:
            Dict with upper, middle, lower bands and bandwidth
        """
        if len(prices) < period:
            return None

        recent_prices = prices[-period:]
        middle = sum(recent_prices) / period

        # Calculate standard deviation
        variance = sum((p - middle) ** 2 for p in recent_prices) / period
        std = variance ** 0.5

        upper = middle + (std_dev * std)
        lower = middle - (std_dev * std)

        # Bandwidth as percentage
        bandwidth = ((upper - lower) / middle) * 100 if middle != 0 else 0

        current_price = prices[-1]
        # Position within bands (0 = lower, 1 = upper)
        position = (current_price - lower) / (upper - lower) if upper != lower else 0.5

        return {
            'upper': round(upper, 2),
            'middle': round(middle, 2),
            'lower': round(lower, 2),
            'bandwidth': round(bandwidth, 2),
            'position': round(position, 2),
            'signal': self._get_bb_signal(position)
        }

    def _get_bb_signal(self, position: float) -> str:
        """Get trading signal from Bollinger Band position."""
        if position < 0:
            return 'OVERSOLD'
        elif position > 1:
            return 'OVERBOUGHT'
        elif position < 0.2:
            return 'NEAR_LOWER'
        elif position > 0.8:
            return 'NEAR_UPPER'
        return 'NEUTRAL'

    def calculate_volatility(self, prices: List[float], period: int = 30) -> Optional[float]:
        """
        Calculate price volatility (standard deviation of returns).

        Args:
            prices: List of closing prices
            period: Period for calculation

        Returns:
            Volatility percentage
        """
        if len(prices) < period + 1:
            return None

        # Calculate daily returns
        returns = []
        for i in range(1, min(period + 1, len(prices))):
            if prices[i-1] != 0:
                returns.append((prices[i] - prices[i-1]) / prices[i-1])

        if not returns:
            return None

        # Calculate standard deviation
        mean_return = sum(returns) / len(returns)
        variance = sum((r - mean_return) ** 2 for r in returns) / len(returns)
        volatility = (variance ** 0.5) * 100  # As percentage

        return round(volatility, 2)

    @cached(ttl=300, key_prefix='technical_analysis')
    def analyze_coin(self, coin_id: str, days: int = 30) -> Optional[Dict]:
        """
        Perform full technical analysis on a coin.

        Args:
            coin_id: CoinGecko coin ID
            days: Number of days of data to analyze

        Returns:
            Complete technical analysis results
        """
        # Fetch price history
        history = self._coingecko.get_price_history(coin_id, days)
        if not history or 'prices' not in history:
            return None

        # Extract closing prices (timestamp, price pairs)
        prices = [p[1] for p in history['prices']]

        if len(prices) < 26:  # Minimum for MACD
            return None

        # Calculate all indicators
        rsi = self.calculate_rsi(prices)
        macd = self.calculate_macd(prices)
        sma_20 = self.calculate_sma(prices, 20)
        sma_50 = self.calculate_sma(prices, min(50, len(prices)))
        bollinger = self.calculate_bollinger_bands(prices)
        volatility = self.calculate_volatility(prices)

        current_price = prices[-1]

        # Determine overall signal
        signals = []
        if rsi:
            if rsi < 30:
                signals.append(('RSI', 'BUY', 'Oversold'))
            elif rsi > 70:
                signals.append(('RSI', 'SELL', 'Overbought'))
            else:
                signals.append(('RSI', 'NEUTRAL', 'Normal range'))

        if macd:
            signals.append(('MACD', 'BUY' if macd['trend'] == 'BULLISH' else 'SELL', macd['trend']))

        if bollinger:
            if bollinger['signal'] == 'OVERSOLD':
                signals.append(('Bollinger', 'BUY', 'Below lower band'))
            elif bollinger['signal'] == 'OVERBOUGHT':
                signals.append(('Bollinger', 'SELL', 'Above upper band'))
            else:
                signals.append(('Bollinger', 'NEUTRAL', bollinger['signal']))

        # Calculate overall recommendation
        buy_signals = sum(1 for s in signals if s[1] == 'BUY')
        sell_signals = sum(1 for s in signals if s[1] == 'SELL')

        if buy_signals > sell_signals:
            overall = 'BUY'
            strength = 'STRONG' if buy_signals >= 2 else 'MODERATE'
        elif sell_signals > buy_signals:
            overall = 'SELL'
            strength = 'STRONG' if sell_signals >= 2 else 'MODERATE'
        else:
            overall = 'HOLD'
            strength = 'NEUTRAL'

        return {
            'coin_id': coin_id,
            'current_price': round(current_price, 2),
            'indicators': {
                'rsi': {
                    'value': rsi,
                    'signal': 'OVERSOLD' if rsi and rsi < 30 else 'OVERBOUGHT' if rsi and rsi > 70 else 'NEUTRAL'
                },
                'macd': macd,
                'sma_20': sma_20,
                'sma_50': sma_50,
                'bollinger_bands': bollinger,
                'volatility': volatility
            },
            'signals': [{'indicator': s[0], 'action': s[1], 'reason': s[2]} for s in signals],
            'recommendation': {
                'action': overall,
                'strength': strength
            },
            'timestamp': datetime.utcnow().isoformat()
        }


# Global analyzer instance
_analyzer: Optional[TechnicalAnalyzer] = None


def get_analyzer() -> TechnicalAnalyzer:
    """Get or create the global technical analyzer."""
    global _analyzer
    if _analyzer is None:
        _analyzer = TechnicalAnalyzer()
    return _analyzer


# Convenience functions
def analyze_coin(coin_id: str, days: int = 30) -> Optional[Dict]:
    """Perform technical analysis on a coin."""
    return get_analyzer().analyze_coin(coin_id, days)


def calculate_rsi(coin_id: str) -> Optional[float]:
    """Calculate RSI for a coin."""
    analysis = analyze_coin(coin_id, 30)
    if analysis and 'indicators' in analysis:
        return analysis['indicators']['rsi']['value']
    return None
