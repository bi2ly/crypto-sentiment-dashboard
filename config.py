"""
Crypto Sentiment Dashboard - Configuration Module

This module loads configuration from environment variables.
It's safe to commit this file as it contains no actual secrets,
only references to environment variables.

Usage:
    from config import Config
    app.config.from_object(Config)
"""

import os
from datetime import timedelta

from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()


def get_env(key: str, default: str = None, required: bool = False) -> str:
    """
    Get environment variable with optional default value.

    Args:
        key: Environment variable name
        default: Default value if not set
        required: If True, raise error when not set

    Returns:
        Environment variable value or default

    Raises:
        ValueError: If required=True and variable is not set
    """
    value = os.getenv(key, default)
    if required and value is None:
        raise ValueError(f"Required environment variable '{key}' is not set")
    return value


def get_env_bool(key: str, default: bool = False) -> bool:
    """Get environment variable as boolean."""
    value = os.getenv(key, str(default)).lower()
    return value in ('true', '1', 'yes', 'on')


def get_env_int(key: str, default: int = 0) -> int:
    """Get environment variable as integer."""
    try:
        return int(os.getenv(key, str(default)))
    except ValueError:
        return default


class Config:
    """Base configuration class."""

    # ==========================================================================
    # Application Settings
    # ==========================================================================
    SECRET_KEY = get_env('SECRET_KEY', 'dev-secret-key-change-in-production')
    DEBUG = get_env_bool('DEBUG', False)
    TESTING = False

    # Server
    HOST = get_env('HOST', '127.0.0.1')
    PORT = get_env_int('PORT', 5000)

    # ==========================================================================
    # Database
    # ==========================================================================
    SQLALCHEMY_DATABASE_URI = get_env('DATABASE_URL', 'sqlite:///crypto_sentiment.db')
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_ECHO = get_env_bool('SQLALCHEMY_ECHO', False)

    # ==========================================================================
    # API URLs (Primary - Free, No Key Required)
    # ==========================================================================
    COINGECKO_API_URL = get_env('COINGECKO_API_URL', 'https://api.coingecko.com/api/v3')
    COINGECKO_RATE_LIMIT = get_env_int('COINGECKO_RATE_LIMIT', 30)

    FEAR_GREED_API_URL = get_env('FEAR_GREED_API_URL', 'https://api.alternative.me/fng/')

    # ==========================================================================
    # API Keys (Secondary - Free with Registration)
    # ==========================================================================
    WHALE_ALERT_API_KEY = get_env('WHALE_ALERT_API_KEY')
    WHALE_ALERT_API_URL = get_env('WHALE_ALERT_API_URL', 'https://api.whale-alert.io/v1')

    COINMARKETCAP_API_KEY = get_env('COINMARKETCAP_API_KEY')
    COINMARKETCAP_API_URL = get_env('COINMARKETCAP_API_URL', 'https://pro-api.coinmarketcap.com/v1')

    # ==========================================================================
    # Social Media APIs
    # ==========================================================================
    REDDIT_CLIENT_ID = get_env('REDDIT_CLIENT_ID')
    REDDIT_CLIENT_SECRET = get_env('REDDIT_CLIENT_SECRET')
    REDDIT_USER_AGENT = get_env('REDDIT_USER_AGENT', 'crypto-sentiment-dashboard:v1.0')

    NEWS_API_KEY = get_env('NEWS_API_KEY')
    NEWS_API_URL = get_env('NEWS_API_URL', 'https://newsapi.org/v2')

    # ==========================================================================
    # Optional APIs (Advanced Features)
    # ==========================================================================
    ALPHA_VANTAGE_API_KEY = get_env('ALPHA_VANTAGE_API_KEY')
    ALPHA_VANTAGE_API_URL = get_env('ALPHA_VANTAGE_API_URL', 'https://www.alphavantage.co/query')

    LUNARCRUSH_API_KEY = get_env('LUNARCRUSH_API_KEY')
    CRYPTOCOMPARE_API_KEY = get_env('CRYPTOCOMPARE_API_KEY')
    MESSARI_API_KEY = get_env('MESSARI_API_KEY')

    # ==========================================================================
    # Email Configuration (SendGrid)
    # ==========================================================================
    SENDGRID_API_KEY = get_env('SENDGRID_API_KEY')
    FROM_EMAIL = get_env('FROM_EMAIL', 'noreply@example.com')
    FROM_NAME = get_env('FROM_NAME', 'Crypto Sentiment Dashboard')

    # SMTP Alternative
    SMTP_HOST = get_env('SMTP_HOST')
    SMTP_PORT = get_env_int('SMTP_PORT', 587)
    SMTP_USERNAME = get_env('SMTP_USERNAME')
    SMTP_PASSWORD = get_env('SMTP_PASSWORD')

    # ==========================================================================
    # Telegram Configuration
    # ==========================================================================
    TELEGRAM_BOT_TOKEN = get_env('TELEGRAM_BOT_TOKEN')
    TELEGRAM_ADMIN_CHAT_ID = get_env('TELEGRAM_ADMIN_CHAT_ID')

    # ==========================================================================
    # Caching
    # ==========================================================================
    CACHE_TYPE = get_env('CACHE_TYPE', 'simple')
    REDIS_URL = get_env('REDIS_URL')

    # Cache timeouts (in seconds)
    CACHE_PRICE_TIMEOUT = get_env_int('CACHE_PRICE_TIMEOUT', 300)  # 5 minutes
    CACHE_FEAR_GREED_TIMEOUT = get_env_int('CACHE_FEAR_GREED_TIMEOUT', 14400)  # 4 hours
    CACHE_WHALE_TIMEOUT = get_env_int('CACHE_WHALE_TIMEOUT', 900)  # 15 minutes
    CACHE_REDDIT_TIMEOUT = get_env_int('CACHE_REDDIT_TIMEOUT', 1800)  # 30 minutes
    CACHE_NEWS_TIMEOUT = get_env_int('CACHE_NEWS_TIMEOUT', 3600)  # 1 hour

    # ==========================================================================
    # Scheduler
    # ==========================================================================
    SCHEDULER_ENABLED = get_env_bool('SCHEDULER_ENABLED', True)
    DAILY_REPORT_HOUR = get_env_int('DAILY_REPORT_HOUR', 8)
    DAILY_REPORT_MINUTE = get_env_int('DAILY_REPORT_MINUTE', 0)

    # ==========================================================================
    # Logging
    # ==========================================================================
    LOG_LEVEL = get_env('LOG_LEVEL', 'INFO')
    LOG_FILE = get_env('LOG_FILE', 'logs/app.log')

    # ==========================================================================
    # Rate Limiting
    # ==========================================================================
    RATE_LIMIT_ENABLED = get_env_bool('RATE_LIMIT_ENABLED', True)
    RATE_LIMIT_DEFAULT = get_env('RATE_LIMIT_DEFAULT', '100/hour')

    # ==========================================================================
    # Security
    # ==========================================================================
    CORS_ORIGINS = get_env('CORS_ORIGINS', 'http://localhost:5000,http://127.0.0.1:5000').split(',')
    SESSION_COOKIE_SECURE = get_env_bool('SESSION_COOKIE_SECURE', False)
    SESSION_COOKIE_HTTPONLY = get_env_bool('SESSION_COOKIE_HTTPONLY', True)
    SESSION_COOKIE_SAMESITE = get_env('SESSION_COOKIE_SAMESITE', 'Lax')

    # ==========================================================================
    # Crypto Settings
    # ==========================================================================
    # Default coins to track
    DEFAULT_COINS = [
        'bitcoin', 'ethereum', 'binancecoin', 'solana', 'cardano',
        'ripple', 'polkadot', 'dogecoin', 'avalanche-2', 'chainlink'
    ]

    # Subreddits to monitor
    REDDIT_SUBREDDITS = [
        'CryptoCurrency',
        'Bitcoin',
        'ethereum',
        'CryptoMoonShots',
        'altcoin',
        'defi'
    ]

    # Whale transaction thresholds (in USD)
    WHALE_THRESHOLD_SMALL = 1_000_000  # $1M
    WHALE_THRESHOLD_MEDIUM = 5_000_000  # $5M
    WHALE_THRESHOLD_LARGE = 10_000_000  # $10M

    # Fear & Greed thresholds
    FEAR_THRESHOLD = 25  # Extreme fear
    GREED_THRESHOLD = 75  # Extreme greed


class DevelopmentConfig(Config):
    """Development configuration."""
    DEBUG = True
    SQLALCHEMY_ECHO = True


class ProductionConfig(Config):
    """Production configuration."""
    DEBUG = False
    TESTING = False

    # Enforce HTTPS in production
    SESSION_COOKIE_SECURE = True

    # More restrictive rate limiting
    RATE_LIMIT_DEFAULT = '50/hour'


class TestingConfig(Config):
    """Testing configuration."""
    TESTING = True
    DEBUG = True
    SQLALCHEMY_DATABASE_URI = 'sqlite:///:memory:'
    WTF_CSRF_ENABLED = False


# Configuration dictionary for easy access
config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'testing': TestingConfig,
    'default': DevelopmentConfig
}


def get_config(env: str = None) -> Config:
    """
    Get configuration class based on environment.

    Args:
        env: Environment name (development, production, testing)

    Returns:
        Configuration class
    """
    if env is None:
        env = get_env('FLASK_ENV', 'development')
    return config.get(env, config['default'])
