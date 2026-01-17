"""
Crypto Sentiment Dashboard - Sentiment Analysis Utilities

VADER sentiment analysis with TextBlob fallback.
"""

import re
from typing import Dict, List, Optional, Tuple

try:
    from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer
    VADER_AVAILABLE = True
except ImportError:
    VADER_AVAILABLE = False

try:
    from textblob import TextBlob
    TEXTBLOB_AVAILABLE = True
except ImportError:
    TEXTBLOB_AVAILABLE = False


class SentimentAnalyzer:
    """
    Sentiment analyzer supporting multiple backends.

    Uses VADER as primary analyzer (optimized for social media),
    with TextBlob as fallback.

    Usage:
        analyzer = SentimentAnalyzer()
        result = analyzer.analyze("Bitcoin is going to the moon!")
        print(result['compound'])  # 0.5 to 0.9 (positive)
    """

    # Crypto-specific lexicon additions for VADER
    CRYPTO_LEXICON = {
        # Bullish terms
        'moon': 2.5,
        'mooning': 3.0,
        'bullish': 2.5,
        'hodl': 1.5,
        'hodling': 1.5,
        'ath': 2.0,  # all-time high
        'pump': 1.5,
        'lambo': 2.0,
        'rocket': 2.0,
        'breakout': 1.5,
        'accumulate': 1.0,
        'undervalued': 1.5,
        'gem': 2.0,

        # Bearish terms
        'dump': -2.0,
        'dumping': -2.5,
        'bearish': -2.5,
        'rekt': -3.0,
        'crash': -2.5,
        'scam': -3.0,
        'rugpull': -3.5,
        'rug': -2.5,
        'fud': -1.5,
        'shitcoin': -2.0,
        'overvalued': -1.5,
        'bubble': -1.5,

        # Neutral/context terms
        'whale': 0.5,
        'dip': -0.5,
        'correction': -0.5,
        'volatility': -0.3,
    }

    def __init__(self, use_crypto_lexicon: bool = True):
        """
        Initialize sentiment analyzer.

        Args:
            use_crypto_lexicon: Add crypto-specific terms to VADER
        """
        self._vader = None
        self._use_crypto_lexicon = use_crypto_lexicon

        if VADER_AVAILABLE:
            self._vader = SentimentIntensityAnalyzer()
            if use_crypto_lexicon:
                self._vader.lexicon.update(self.CRYPTO_LEXICON)

    def analyze(self, text: str) -> Dict[str, float]:
        """
        Analyze sentiment of text.

        Args:
            text: Text to analyze

        Returns:
            Dictionary with sentiment scores:
            - compound: Overall sentiment (-1 to 1)
            - positive: Positive sentiment ratio (0 to 1)
            - negative: Negative sentiment ratio (0 to 1)
            - neutral: Neutral sentiment ratio (0 to 1)
        """
        if not text or not text.strip():
            return {
                'compound': 0.0,
                'positive': 0.0,
                'negative': 0.0,
                'neutral': 1.0
            }

        # Clean text
        text = self._preprocess(text)

        # Try VADER first
        if self._vader is not None:
            scores = self._vader.polarity_scores(text)
            return {
                'compound': scores['compound'],
                'positive': scores['pos'],
                'negative': scores['neg'],
                'neutral': scores['neu']
            }

        # Fallback to TextBlob
        if TEXTBLOB_AVAILABLE:
            blob = TextBlob(text)
            polarity = blob.sentiment.polarity  # -1 to 1

            # Convert to VADER-like format
            if polarity > 0:
                return {
                    'compound': polarity,
                    'positive': polarity,
                    'negative': 0.0,
                    'neutral': 1 - polarity
                }
            elif polarity < 0:
                return {
                    'compound': polarity,
                    'positive': 0.0,
                    'negative': abs(polarity),
                    'neutral': 1 - abs(polarity)
                }
            else:
                return {
                    'compound': 0.0,
                    'positive': 0.0,
                    'negative': 0.0,
                    'neutral': 1.0
                }

        # No analyzer available
        raise RuntimeError("No sentiment analyzer available. Install vaderSentiment or textblob.")

    def analyze_batch(self, texts: List[str]) -> List[Dict[str, float]]:
        """Analyze sentiment of multiple texts."""
        return [self.analyze(text) for text in texts]

    def classify(self, text: str) -> Tuple[str, float]:
        """
        Classify text as positive, negative, or neutral.

        Args:
            text: Text to classify

        Returns:
            Tuple of (label, confidence)
        """
        scores = self.analyze(text)
        compound = scores['compound']

        if compound >= 0.05:
            return ('positive', compound)
        elif compound <= -0.05:
            return ('negative', abs(compound))
        else:
            return ('neutral', scores['neutral'])

    def aggregate_sentiment(self, texts: List[str]) -> Dict[str, any]:
        """
        Analyze and aggregate sentiment across multiple texts.

        Args:
            texts: List of texts to analyze

        Returns:
            Aggregated sentiment statistics
        """
        if not texts:
            return {
                'count': 0,
                'avg_compound': 0.0,
                'positive_count': 0,
                'negative_count': 0,
                'neutral_count': 0,
                'positive_ratio': 0.0,
                'negative_ratio': 0.0,
                'neutral_ratio': 0.0
            }

        results = self.analyze_batch(texts)
        compounds = [r['compound'] for r in results]

        positive = sum(1 for c in compounds if c >= 0.05)
        negative = sum(1 for c in compounds if c <= -0.05)
        neutral = len(compounds) - positive - negative

        return {
            'count': len(texts),
            'avg_compound': sum(compounds) / len(compounds),
            'positive_count': positive,
            'negative_count': negative,
            'neutral_count': neutral,
            'positive_ratio': positive / len(texts),
            'negative_ratio': negative / len(texts),
            'neutral_ratio': neutral / len(texts)
        }

    def _preprocess(self, text: str) -> str:
        """Preprocess text for analysis."""
        # Convert to lowercase
        text = text.lower()

        # Remove URLs
        text = re.sub(r'https?://\S+', '', text)

        # Remove mentions (@username)
        text = re.sub(r'@\w+', '', text)

        # Keep hashtags but remove the # symbol
        text = re.sub(r'#(\w+)', r'\1', text)

        # Remove extra whitespace
        text = ' '.join(text.split())

        return text


# Global analyzer instance
_analyzer: Optional[SentimentAnalyzer] = None


def get_analyzer() -> SentimentAnalyzer:
    """Get the global sentiment analyzer instance."""
    global _analyzer
    if _analyzer is None:
        _analyzer = SentimentAnalyzer()
    return _analyzer


def analyze_sentiment(text: str) -> Dict[str, float]:
    """Convenience function for single text analysis."""
    return get_analyzer().analyze(text)


def classify_sentiment(text: str) -> Tuple[str, float]:
    """Convenience function for text classification."""
    return get_analyzer().classify(text)
