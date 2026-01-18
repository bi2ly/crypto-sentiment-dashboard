"""
Crypto Sentiment Dashboard - Routes

This module defines all the routes (endpoints) for both the web interface
and the REST API.
"""

import logging
from datetime import datetime

from flask import Blueprint, jsonify, render_template, request

from app.api import coingecko, fear_greed, whale_alert, reddit_client, news_api
from app.services import technical, whale_tracker, sector_analysis, calendar, influencer, github_tracker

logger = logging.getLogger(__name__)

# Create blueprints
main_bp = Blueprint('main', __name__)
api_bp = Blueprint('api', __name__)


# =============================================================================
# Web Interface Routes
# =============================================================================

@main_bp.route('/')
def index():
    """
    Home page - redirects to dashboard.
    """
    return render_template('index.html')


@main_bp.route('/dashboard')
def dashboard():
    """
    Main dashboard view with all crypto sentiment data.
    """
    return render_template('dashboard.html')


@main_bp.route('/health')
def health_check():
    """
    Health check endpoint for monitoring.
    """
    # Check API connections
    api_status = {
        'coingecko': coingecko.get_client().ping(),
        'fear_greed': fear_greed.get_client().get_current_index() is not None,
        'whale_alert': whale_alert.get_client().get_status()['configured'],
        'reddit': reddit_client.get_client().get_status()['configured'],
        'news_api': news_api.get_client().get_status()['configured']
    }

    return jsonify({
        'status': 'healthy',
        'timestamp': datetime.utcnow().isoformat(),
        'version': '0.2.0',
        'api_status': api_status
    })


# =============================================================================
# API Routes - Market Data
# =============================================================================

@api_bp.route('/market/trending')
def get_trending_coins():
    """
    Get trending cryptocurrencies.

    Returns:
        JSON list of trending coins with price and volume data.
    """
    try:
        data = coingecko.get_trending_coins()
        if data:
            return jsonify({
                'status': 'success',
                'data': data
            })
        return jsonify({
            'status': 'error',
            'message': 'Failed to fetch trending coins',
            'data': None
        }), 503
    except Exception as e:
        logger.error(f"Error fetching trending coins: {e}")
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500


@api_bp.route('/market/prices')
def get_prices():
    """
    Get current prices for specified coins.

    Query Parameters:
        coins: Comma-separated list of coin IDs (e.g., bitcoin,ethereum)
        vs_currency: Target currency (default: usd)

    Returns:
        JSON with current prices.
    """
    coins_param = request.args.get('coins', 'bitcoin,ethereum')
    vs_currency = request.args.get('vs_currency', 'usd')

    coin_ids = [c.strip() for c in coins_param.split(',') if c.strip()]

    try:
        data = coingecko.get_simple_prices(coin_ids, [vs_currency])
        if data:
            return jsonify({
                'status': 'success',
                'params': {'coins': coin_ids, 'vs_currency': vs_currency},
                'data': data
            })
        return jsonify({
            'status': 'error',
            'message': 'Failed to fetch prices',
            'data': None
        }), 503
    except Exception as e:
        logger.error(f"Error fetching prices: {e}")
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500


@api_bp.route('/market/coin/<coin_id>')
def get_coin_details(coin_id: str):
    """
    Get detailed information for a specific coin.

    Args:
        coin_id: CoinGecko coin ID (e.g., bitcoin, ethereum)

    Returns:
        JSON with detailed coin data.
    """
    try:
        data = coingecko.get_coin_details(coin_id)
        if data:
            return jsonify({
                'status': 'success',
                'data': data
            })
        return jsonify({
            'status': 'error',
            'message': f'Coin {coin_id} not found',
            'data': None
        }), 404
    except Exception as e:
        logger.error(f"Error fetching coin details: {e}")
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500


@api_bp.route('/market/history/<coin_id>')
def get_coin_history(coin_id: str):
    """
    Get historical price data for a coin.

    Args:
        coin_id: CoinGecko coin ID

    Query Parameters:
        days: Number of days (default: 7)

    Returns:
        JSON with historical price data.
    """
    days = request.args.get('days', 7, type=int)

    try:
        data = coingecko.get_price_history(coin_id, days)
        if data:
            return jsonify({
                'status': 'success',
                'params': {'coin_id': coin_id, 'days': days},
                'data': data
            })
        return jsonify({
            'status': 'error',
            'message': f'History not available for {coin_id}',
            'data': None
        }), 404
    except Exception as e:
        logger.error(f"Error fetching price history: {e}")
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500


# =============================================================================
# API Routes - Sentiment
# =============================================================================

@api_bp.route('/sentiment/fear-greed')
def get_fear_greed():
    """
    Get current Fear & Greed Index.

    Query Parameters:
        limit: Number of historical days to include (default: 1)

    Returns:
        JSON with Fear & Greed index data.
    """
    limit = request.args.get('limit', 1, type=int)

    try:
        if limit == 1:
            data = fear_greed.get_current_index()
        else:
            data = fear_greed.get_historical_index(limit)

        if data:
            return jsonify({
                'status': 'success',
                'params': {'limit': limit},
                'data': data
            })
        return jsonify({
            'status': 'error',
            'message': 'Failed to fetch Fear & Greed index',
            'data': None
        }), 503
    except Exception as e:
        logger.error(f"Error fetching Fear & Greed: {e}")
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500


@api_bp.route('/sentiment/fear-greed/signal')
def get_fear_greed_signal():
    """
    Get trading signal based on Fear & Greed Index.

    Returns:
        JSON with signal recommendation.
    """
    try:
        data = fear_greed.get_sentiment_signal()
        if data:
            return jsonify({
                'status': 'success',
                'data': data
            })
        return jsonify({
            'status': 'error',
            'message': 'Failed to generate signal',
            'data': None
        }), 503
    except Exception as e:
        logger.error(f"Error generating signal: {e}")
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500


@api_bp.route('/sentiment/reddit/<coin_id>')
def get_reddit_sentiment(coin_id: str):
    """
    Get Reddit sentiment for a specific coin.

    Args:
        coin_id: Coin identifier

    Query Parameters:
        subreddit: Specific subreddit (default: CryptoCurrency)

    Returns:
        JSON with Reddit sentiment data.
    """
    subreddit = request.args.get('subreddit', 'CryptoCurrency')

    try:
        data = reddit_client.get_subreddit_sentiment(subreddit, coin_id)
        if data:
            return jsonify({
                'status': 'success',
                'data': data
            })
        return jsonify({
            'status': 'error',
            'message': f'No sentiment data for {coin_id}',
            'data': None
        }), 404
    except Exception as e:
        logger.error(f"Error fetching Reddit sentiment: {e}")
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500


@api_bp.route('/sentiment/reddit/trending')
def get_reddit_trending():
    """
    Get trending crypto discussions from Reddit.

    Returns:
        JSON with trending posts.
    """
    try:
        data = reddit_client.get_trending_discussions()
        if data:
            return jsonify({
                'status': 'success',
                'data': data
            })
        return jsonify({
            'status': 'error',
            'message': 'Failed to fetch trending discussions',
            'data': None
        }), 503
    except Exception as e:
        logger.error(f"Error fetching Reddit trending: {e}")
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500


# =============================================================================
# API Routes - Whale Activity
# =============================================================================

@api_bp.route('/whales/transactions')
def get_whale_transactions():
    """
    Get recent whale transactions.

    Query Parameters:
        min_value: Minimum transaction value in USD (default: 1000000)
        limit: Number of transactions to return (default: 10)

    Returns:
        JSON with whale transaction data.
    """
    min_value = request.args.get('min_value', 1000000, type=int)
    limit = request.args.get('limit', 10, type=int)

    try:
        data = whale_alert.get_recent_transactions(min_value, limit)
        if data:
            return jsonify({
                'status': 'success',
                'params': {'min_value': min_value, 'limit': limit},
                'data': data
            })

        # Check if API is configured
        status = whale_alert.get_client().get_status()
        if not status['configured']:
            return jsonify({
                'status': 'error',
                'message': 'Whale Alert API not configured. Set WHALE_ALERT_API_KEY.',
                'data': None
            }), 503

        return jsonify({
            'status': 'error',
            'message': 'Failed to fetch whale transactions',
            'data': None
        }), 503
    except Exception as e:
        logger.error(f"Error fetching whale transactions: {e}")
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500


@api_bp.route('/whales/flows')
def get_exchange_flows():
    """
    Get exchange inflow/outflow analysis.

    Returns:
        JSON with exchange flow data.
    """
    try:
        data = whale_alert.get_exchange_flows()
        if data:
            return jsonify({
                'status': 'success',
                'data': data
            })

        # Check if API is configured
        status = whale_alert.get_client().get_status()
        if not status['configured']:
            return jsonify({
                'status': 'error',
                'message': 'Whale Alert API not configured. Set WHALE_ALERT_API_KEY.',
                'data': None
            }), 503

        return jsonify({
            'status': 'error',
            'message': 'Failed to analyze exchange flows',
            'data': None
        }), 503
    except Exception as e:
        logger.error(f"Error analyzing exchange flows: {e}")
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500


# =============================================================================
# API Routes - News
# =============================================================================

@api_bp.route('/news')
def get_news():
    """
    Get latest crypto news with sentiment analysis.

    Query Parameters:
        query: Search query (default: cryptocurrency)
        limit: Number of articles (default: 10)

    Returns:
        JSON with news articles and sentiment scores.
    """
    query = request.args.get('query', 'cryptocurrency')
    limit = request.args.get('limit', 10, type=int)

    try:
        data = news_api.get_crypto_news(query, limit)
        if data:
            sentiment_summary = news_api.analyze_sentiment(data)
            return jsonify({
                'status': 'success',
                'params': {'query': query, 'limit': limit},
                'sentiment_summary': sentiment_summary,
                'data': data
            })

        # Check if API is configured
        status = news_api.get_client().get_status()
        if not status['configured']:
            return jsonify({
                'status': 'error',
                'message': 'NewsAPI not configured. Set NEWS_API_KEY.',
                'data': None
            }), 503

        return jsonify({
            'status': 'error',
            'message': 'Failed to fetch news',
            'data': None
        }), 503
    except Exception as e:
        logger.error(f"Error fetching news: {e}")
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500


@api_bp.route('/news/coin/<coin_name>')
def get_coin_news(coin_name: str):
    """
    Get news for a specific cryptocurrency.

    Args:
        coin_name: Coin name (e.g., Bitcoin, Ethereum)

    Query Parameters:
        limit: Number of articles (default: 10)

    Returns:
        JSON with news articles for the coin.
    """
    limit = request.args.get('limit', 10, type=int)

    try:
        data = news_api.get_coin_news(coin_name, limit)
        if data:
            sentiment_summary = news_api.analyze_sentiment(data)
            return jsonify({
                'status': 'success',
                'params': {'coin': coin_name, 'limit': limit},
                'sentiment_summary': sentiment_summary,
                'data': data
            })
        return jsonify({
            'status': 'error',
            'message': f'No news found for {coin_name}',
            'data': None
        }), 404
    except Exception as e:
        logger.error(f"Error fetching coin news: {e}")
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500


@api_bp.route('/news/summary')
def get_news_summary():
    """
    Get overall crypto news sentiment summary.

    Returns:
        JSON with news sentiment summary.
    """
    try:
        data = news_api.get_client().get_news_summary()
        return jsonify({
            'status': 'success',
            'data': data
        })
    except Exception as e:
        logger.error(f"Error generating news summary: {e}")
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500


# =============================================================================
# API Routes - Alerts & Subscriptions
# =============================================================================

@api_bp.route('/subscribe', methods=['POST'])
def subscribe():
    """
    Subscribe to alerts and daily reports.

    Request Body:
        email: Email address (optional)
        telegram_id: Telegram chat ID (optional)
        preferences: Alert preferences

    Returns:
        JSON with subscription confirmation.
    """
    data = request.get_json() or {}

    # TODO: Implement subscription system in Phase 5
    return jsonify({
        'status': 'success',
        'message': 'Subscription endpoint - Coming in Phase 5',
        'data': data
    })


@api_bp.route('/alerts', methods=['GET', 'POST'])
def manage_alerts():
    """
    Get or create custom alerts.

    GET: Retrieve user's active alerts
    POST: Create a new alert

    Returns:
        JSON with alert data.
    """
    if request.method == 'POST':
        data = request.get_json() or {}
        # TODO: Implement alert creation in Phase 4
        return jsonify({
            'status': 'success',
            'message': 'Alert creation - Coming in Phase 4',
            'data': data
        })

    # TODO: Implement alert retrieval in Phase 4
    return jsonify({
        'status': 'success',
        'message': 'Alert retrieval - Coming in Phase 4',
        'data': []
    })


# =============================================================================
# API Routes - Opportunity Scoring
# =============================================================================

@api_bp.route('/opportunities')
def get_opportunities():
    """
    Get coins ranked by opportunity score.

    Query Parameters:
        limit: Number of coins to return (default: 10)
        min_score: Minimum opportunity score (default: 0)

    Returns:
        JSON with ranked opportunities.
    """
    limit = request.args.get('limit', 10, type=int)
    min_score = request.args.get('min_score', 0, type=int)

    # TODO: Implement opportunity scoring in Phase 4
    return jsonify({
        'status': 'success',
        'message': 'Opportunities endpoint - Coming in Phase 4',
        'params': {'limit': limit, 'min_score': min_score},
        'data': []
    })


# =============================================================================
# API Routes - Dashboard Summary
# =============================================================================

@api_bp.route('/dashboard/summary')
def get_dashboard_summary():
    """
    Get aggregated dashboard data in a single call.

    Returns:
        JSON with market overview, sentiment, and key metrics.
    """
    try:
        # Fetch data from multiple sources
        trending = coingecko.get_trending_coins()
        fear_greed_data = fear_greed.get_current_index()
        fear_greed_signal_data = fear_greed.get_sentiment_signal()

        return jsonify({
            'status': 'success',
            'data': {
                'trending_coins': trending,
                'fear_greed': fear_greed_data,
                'market_signal': fear_greed_signal_data,
                'timestamp': datetime.utcnow().isoformat()
            }
        })
    except Exception as e:
        logger.error(f"Error generating dashboard summary: {e}")
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500


# =============================================================================
# API Routes - Technical Analysis (Phase 3)
# =============================================================================

@api_bp.route('/analysis/technical/<coin_id>')
def get_technical_analysis(coin_id: str):
    """
    Get technical analysis for a coin.

    Args:
        coin_id: CoinGecko coin ID

    Query Parameters:
        days: Number of days of data (default: 30)

    Returns:
        JSON with RSI, MACD, Bollinger Bands, and recommendations.
    """
    days = request.args.get('days', 30, type=int)

    try:
        data = technical.analyze_coin(coin_id, days)
        if data:
            return jsonify({
                'status': 'success',
                'data': data
            })
        return jsonify({
            'status': 'error',
            'message': f'Unable to analyze {coin_id}. Insufficient data.',
            'data': None
        }), 404
    except Exception as e:
        logger.error(f"Error in technical analysis: {e}")
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500


# =============================================================================
# API Routes - Whale Analysis (Phase 3)
# =============================================================================

@api_bp.route('/whales/analysis')
def get_whale_analysis():
    """
    Get comprehensive whale activity analysis.

    Query Parameters:
        min_value: Minimum transaction value in USD (default: 1000000)

    Returns:
        JSON with whale activity, exchange flows, and alerts.
    """
    min_value = request.args.get('min_value', 1000000, type=int)

    try:
        data = whale_tracker.get_whale_analysis(min_value)
        return jsonify({
            'status': 'success',
            'data': data
        })
    except Exception as e:
        logger.error(f"Error in whale analysis: {e}")
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500


@api_bp.route('/whales/coin/<symbol>')
def get_coin_whale_flow(symbol: str):
    """
    Get whale flow analysis for a specific coin.

    Args:
        symbol: Coin symbol (e.g., BTC, ETH)

    Returns:
        JSON with coin-specific whale activity.
    """
    try:
        data = whale_tracker.get_coin_flow(symbol)
        if data:
            return jsonify({
                'status': 'success',
                'data': data
            })
        return jsonify({
            'status': 'error',
            'message': f'No whale data for {symbol}',
            'data': None
        }), 404
    except Exception as e:
        logger.error(f"Error in coin whale flow: {e}")
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500


@api_bp.route('/whales/alerts')
def get_whale_alerts():
    """
    Get current whale alerts.

    Returns:
        JSON with high-impact whale alerts.
    """
    try:
        alerts = whale_tracker.get_whale_alerts()
        return jsonify({
            'status': 'success',
            'data': {
                'alert_count': len(alerts),
                'alerts': alerts
            }
        })
    except Exception as e:
        logger.error(f"Error fetching whale alerts: {e}")
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500


# =============================================================================
# API Routes - Sector Analysis (Phase 3)
# =============================================================================

@api_bp.route('/sectors')
def get_sector_overview():
    """
    Get overview of all crypto sectors.

    Returns:
        JSON with sector performance comparison.
    """
    try:
        data = sector_analysis.get_sector_overview()
        return jsonify({
            'status': 'success',
            'data': data
        })
    except Exception as e:
        logger.error(f"Error in sector overview: {e}")
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500


@api_bp.route('/sectors/<sector_id>')
def get_sector_detail(sector_id: str):
    """
    Get detailed analysis for a specific sector.

    Args:
        sector_id: Sector identifier

    Returns:
        JSON with sector details and top coins.
    """
    try:
        data = sector_analysis.get_sector_detail(sector_id)
        if data:
            return jsonify({
                'status': 'success',
                'data': data
            })
        return jsonify({
            'status': 'error',
            'message': f'Sector {sector_id} not found',
            'data': None
        }), 404
    except Exception as e:
        logger.error(f"Error in sector detail: {e}")
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500


@api_bp.route('/sectors/leaders')
def get_sector_leaders():
    """
    Get top performers from each sector.

    Query Parameters:
        limit: Number of coins per sector (default: 5)

    Returns:
        JSON with sector leaders.
    """
    limit = request.args.get('limit', 5, type=int)

    try:
        data = sector_analysis.get_sector_leaders(limit)
        return jsonify({
            'status': 'success',
            'data': data
        })
    except Exception as e:
        logger.error(f"Error fetching sector leaders: {e}")
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500


# =============================================================================
# API Routes - Calendar Events (Phase 3)
# =============================================================================

@api_bp.route('/calendar/events')
def get_calendar_events():
    """
    Get all upcoming crypto events.

    Query Parameters:
        days: Number of days to look ahead (default: 30)

    Returns:
        JSON with upcoming events.
    """
    days = request.args.get('days', 30, type=int)

    try:
        data = calendar.get_upcoming_events(days)
        return jsonify({
            'status': 'success',
            'data': data
        })
    except Exception as e:
        logger.error(f"Error fetching calendar events: {e}")
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500


@api_bp.route('/calendar/listings')
def get_exchange_listings():
    """
    Get upcoming exchange listings.

    Query Parameters:
        days: Number of days to look ahead (default: 30)

    Returns:
        JSON with upcoming listings.
    """
    days = request.args.get('days', 30, type=int)

    try:
        data = calendar.get_exchange_listings(days)
        return jsonify({
            'status': 'success',
            'data': data
        })
    except Exception as e:
        logger.error(f"Error fetching exchange listings: {e}")
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500


@api_bp.route('/calendar/unlocks')
def get_token_unlocks():
    """
    Get upcoming token unlocks.

    Query Parameters:
        days: Number of days to look ahead (default: 30)

    Returns:
        JSON with upcoming token unlocks.
    """
    days = request.args.get('days', 30, type=int)

    try:
        data = calendar.get_token_unlocks(days)
        return jsonify({
            'status': 'success',
            'data': data
        })
    except Exception as e:
        logger.error(f"Error fetching token unlocks: {e}")
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500


@api_bp.route('/calendar/upgrades')
def get_network_upgrades():
    """
    Get upcoming network upgrades.

    Query Parameters:
        days: Number of days to look ahead (default: 90)

    Returns:
        JSON with upcoming network upgrades.
    """
    days = request.args.get('days', 90, type=int)

    try:
        data = calendar.get_network_upgrades(days)
        return jsonify({
            'status': 'success',
            'data': data
        })
    except Exception as e:
        logger.error(f"Error fetching network upgrades: {e}")
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500


# =============================================================================
# API Routes - Influencer Tracking (Phase 3)
# =============================================================================

@api_bp.route('/influencers')
def get_influencers():
    """
    Get list of tracked influencers.

    Returns:
        JSON with influencer list by category.
    """
    try:
        data = influencer.get_influencer_list()
        return jsonify({
            'status': 'success',
            'data': data
        })
    except Exception as e:
        logger.error(f"Error fetching influencers: {e}")
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500


@api_bp.route('/influencers/activity')
def get_influencer_activity():
    """
    Get recent influencer activity.

    Query Parameters:
        hours: Look back period in hours (default: 24)

    Returns:
        JSON with recent influencer mentions.
    """
    hours = request.args.get('hours', 24, type=int)

    try:
        data = influencer.get_recent_activity(hours)
        return jsonify({
            'status': 'success',
            'data': data
        })
    except Exception as e:
        logger.error(f"Error fetching influencer activity: {e}")
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500


@api_bp.route('/influencers/coin/<coin_id>')
def get_coin_influencer_sentiment(coin_id: str):
    """
    Get influencer sentiment for a specific coin.

    Args:
        coin_id: Coin identifier

    Returns:
        JSON with influencer sentiment analysis.
    """
    try:
        data = influencer.get_coin_influencer_sentiment(coin_id)
        return jsonify({
            'status': 'success',
            'data': data
        })
    except Exception as e:
        logger.error(f"Error fetching coin influencer sentiment: {e}")
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500


# =============================================================================
# API Routes - Development Activity (Phase 3)
# =============================================================================

@api_bp.route('/development')
def get_development_overview():
    """
    Get development activity overview for tracked projects.

    Returns:
        JSON with GitHub activity comparison.
    """
    try:
        data = github_tracker.get_development_overview()
        return jsonify({
            'status': 'success',
            'data': data
        })
    except Exception as e:
        logger.error(f"Error fetching development overview: {e}")
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500


@api_bp.route('/development/<project_id>')
def get_project_development(project_id: str):
    """
    Get development activity for a specific project.

    Args:
        project_id: Project identifier

    Returns:
        JSON with project GitHub stats.
    """
    try:
        data = github_tracker.get_project_activity(project_id)
        if data:
            return jsonify({
                'status': 'success',
                'data': data
            })
        return jsonify({
            'status': 'error',
            'message': f'Project {project_id} not found',
            'data': None
        }), 404
    except Exception as e:
        logger.error(f"Error fetching project development: {e}")
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500


# =============================================================================
# API Routes - Advanced Dashboard (Phase 3)
# =============================================================================

@api_bp.route('/dashboard/advanced')
def get_advanced_dashboard():
    """
    Get advanced dashboard data including all Phase 3 features.

    Returns:
        JSON with comprehensive market analysis.
    """
    try:
        # Fetch data from multiple sources
        trending = coingecko.get_trending_coins()
        fear_greed_data = fear_greed.get_current_index()
        fear_greed_signal_data = fear_greed.get_sentiment_signal()
        whale_data = whale_tracker.get_whale_analysis()
        sector_data = sector_analysis.get_sector_overview()
        influencer_data = influencer.get_recent_activity(24)
        calendar_data = calendar.get_upcoming_events(14)

        return jsonify({
            'status': 'success',
            'data': {
                'trending_coins': trending,
                'fear_greed': fear_greed_data,
                'market_signal': fear_greed_signal_data,
                'whale_activity': whale_data,
                'sectors': sector_data,
                'influencer_activity': influencer_data,
                'upcoming_events': calendar_data,
                'timestamp': datetime.utcnow().isoformat()
            }
        })
    except Exception as e:
        logger.error(f"Error generating advanced dashboard: {e}")
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500
