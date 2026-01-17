"""
Crypto Sentiment Dashboard - Routes

This module defines all the routes (endpoints) for both the web interface
and the REST API.
"""

from datetime import datetime

from flask import Blueprint, jsonify, render_template, request

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
    return jsonify({
        'status': 'healthy',
        'timestamp': datetime.utcnow().isoformat(),
        'version': '0.1.0'
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
    # TODO: Implement CoinGecko integration in Phase 1
    return jsonify({
        'status': 'success',
        'message': 'Trending coins endpoint - Coming in Phase 1',
        'data': []
    })


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
    coins = request.args.get('coins', 'bitcoin,ethereum')
    vs_currency = request.args.get('vs_currency', 'usd')

    # TODO: Implement CoinGecko integration in Phase 1
    return jsonify({
        'status': 'success',
        'message': 'Prices endpoint - Coming in Phase 1',
        'params': {'coins': coins, 'vs_currency': vs_currency},
        'data': {}
    })


@api_bp.route('/market/coin/<coin_id>')
def get_coin_details(coin_id: str):
    """
    Get detailed information for a specific coin.

    Args:
        coin_id: CoinGecko coin ID (e.g., bitcoin, ethereum)

    Returns:
        JSON with detailed coin data.
    """
    # TODO: Implement CoinGecko integration in Phase 1
    return jsonify({
        'status': 'success',
        'message': f'Coin details for {coin_id} - Coming in Phase 1',
        'data': {}
    })


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

    # TODO: Implement Fear & Greed API integration in Phase 1
    return jsonify({
        'status': 'success',
        'message': 'Fear & Greed endpoint - Coming in Phase 1',
        'params': {'limit': limit},
        'data': {}
    })


@api_bp.route('/sentiment/reddit/<coin_id>')
def get_reddit_sentiment(coin_id: str):
    """
    Get Reddit sentiment for a specific coin.

    Args:
        coin_id: Coin identifier

    Returns:
        JSON with Reddit sentiment data.
    """
    # TODO: Implement Reddit integration in Phase 1
    return jsonify({
        'status': 'success',
        'message': f'Reddit sentiment for {coin_id} - Coming in Phase 1',
        'data': {}
    })


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

    # TODO: Implement Whale Alert integration in Phase 1
    return jsonify({
        'status': 'success',
        'message': 'Whale transactions endpoint - Coming in Phase 1',
        'params': {'min_value': min_value, 'limit': limit},
        'data': []
    })


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

    # TODO: Implement NewsAPI integration in Phase 1
    return jsonify({
        'status': 'success',
        'message': 'News endpoint - Coming in Phase 1',
        'params': {'query': query, 'limit': limit},
        'data': []
    })


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
