"""
Crypto Sentiment Dashboard - Database Models

This module defines all SQLAlchemy database models for storing
cryptocurrency data, sentiment analysis, user subscriptions, and alerts.
"""

from datetime import datetime

from app import db


class Coin(db.Model):
    """
    Cryptocurrency information and current market data.
    """
    __tablename__ = 'coins'

    id = db.Column(db.String(100), primary_key=True)  # CoinGecko ID
    symbol = db.Column(db.String(20), nullable=False, index=True)
    name = db.Column(db.String(100), nullable=False)
    current_price = db.Column(db.Float)
    market_cap = db.Column(db.BigInteger)
    market_cap_rank = db.Column(db.Integer)
    total_volume = db.Column(db.BigInteger)
    price_change_24h = db.Column(db.Float)
    price_change_percentage_24h = db.Column(db.Float)
    circulating_supply = db.Column(db.Float)
    total_supply = db.Column(db.Float)
    ath = db.Column(db.Float)  # All-time high
    ath_date = db.Column(db.DateTime)
    atl = db.Column(db.Float)  # All-time low
    atl_date = db.Column(db.DateTime)
    image_url = db.Column(db.String(500))
    last_updated = db.Column(db.DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f'<Coin {self.symbol.upper()} - ${self.current_price}>'

    def to_dict(self):
        return {
            'id': self.id,
            'symbol': self.symbol,
            'name': self.name,
            'current_price': self.current_price,
            'market_cap': self.market_cap,
            'market_cap_rank': self.market_cap_rank,
            'total_volume': self.total_volume,
            'price_change_24h': self.price_change_24h,
            'price_change_percentage_24h': self.price_change_percentage_24h,
            'image_url': self.image_url,
            'last_updated': self.last_updated.isoformat() if self.last_updated else None
        }


class FearGreedHistory(db.Model):
    """
    Historical Fear & Greed Index data.
    """
    __tablename__ = 'fear_greed_history'

    id = db.Column(db.Integer, primary_key=True)
    timestamp = db.Column(db.DateTime, nullable=False, index=True)
    value = db.Column(db.Integer, nullable=False)  # 0-100
    classification = db.Column(db.String(20))  # Extreme Fear, Fear, Neutral, Greed, Extreme Greed
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f'<FearGreed {self.value} ({self.classification}) @ {self.timestamp}>'

    def to_dict(self):
        return {
            'timestamp': self.timestamp.isoformat(),
            'value': self.value,
            'classification': self.classification
        }


class WhaleTransaction(db.Model):
    """
    Large cryptocurrency transactions tracked by Whale Alert.
    """
    __tablename__ = 'whale_transactions'

    id = db.Column(db.Integer, primary_key=True)
    transaction_hash = db.Column(db.String(100), unique=True, nullable=False)
    blockchain = db.Column(db.String(50), nullable=False, index=True)
    symbol = db.Column(db.String(20), nullable=False, index=True)
    amount = db.Column(db.Float, nullable=False)
    amount_usd = db.Column(db.Float, nullable=False, index=True)
    from_address = db.Column(db.String(200))
    from_owner = db.Column(db.String(100))  # Exchange name if known
    from_owner_type = db.Column(db.String(50))  # exchange, wallet, etc.
    to_address = db.Column(db.String(200))
    to_owner = db.Column(db.String(100))
    to_owner_type = db.Column(db.String(50))
    timestamp = db.Column(db.DateTime, nullable=False, index=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f'<WhaleTransaction {self.symbol} ${self.amount_usd:,.0f}>'

    def to_dict(self):
        return {
            'transaction_hash': self.transaction_hash,
            'blockchain': self.blockchain,
            'symbol': self.symbol,
            'amount': self.amount,
            'amount_usd': self.amount_usd,
            'from': {
                'address': self.from_address,
                'owner': self.from_owner,
                'type': self.from_owner_type
            },
            'to': {
                'address': self.to_address,
                'owner': self.to_owner,
                'type': self.to_owner_type
            },
            'timestamp': self.timestamp.isoformat()
        }


class RedditSentiment(db.Model):
    """
    Reddit sentiment data for cryptocurrencies.
    """
    __tablename__ = 'reddit_sentiment'

    id = db.Column(db.Integer, primary_key=True)
    coin_id = db.Column(db.String(100), db.ForeignKey('coins.id'), nullable=False, index=True)
    subreddit = db.Column(db.String(100), nullable=False, index=True)
    date = db.Column(db.Date, nullable=False, index=True)
    mention_count = db.Column(db.Integer, default=0)
    positive_count = db.Column(db.Integer, default=0)
    negative_count = db.Column(db.Integer, default=0)
    neutral_count = db.Column(db.Integer, default=0)
    avg_sentiment_score = db.Column(db.Float)  # -1 to 1
    upvote_ratio = db.Column(db.Float)
    total_comments = db.Column(db.Integer)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # Relationships
    coin = db.relationship('Coin', backref=db.backref('reddit_sentiments', lazy='dynamic'))

    def __repr__(self):
        return f'<RedditSentiment {self.coin_id} r/{self.subreddit} {self.avg_sentiment_score}>'

    def to_dict(self):
        return {
            'coin_id': self.coin_id,
            'subreddit': self.subreddit,
            'date': self.date.isoformat(),
            'mention_count': self.mention_count,
            'sentiment': {
                'positive': self.positive_count,
                'negative': self.negative_count,
                'neutral': self.neutral_count,
                'avg_score': self.avg_sentiment_score
            },
            'upvote_ratio': self.upvote_ratio,
            'total_comments': self.total_comments
        }


class NewsArticle(db.Model):
    """
    Crypto news articles with sentiment analysis.
    """
    __tablename__ = 'news_articles'

    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(500), nullable=False)
    description = db.Column(db.Text)
    url = db.Column(db.String(1000), unique=True, nullable=False)
    source = db.Column(db.String(100))
    author = db.Column(db.String(200))
    published_at = db.Column(db.DateTime, index=True)
    sentiment_score = db.Column(db.Float)  # -1 to 1
    sentiment_label = db.Column(db.String(20))  # positive, negative, neutral
    mentioned_coins = db.Column(db.Text)  # JSON array of coin IDs
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f'<NewsArticle {self.title[:50]}...>'

    def to_dict(self):
        return {
            'title': self.title,
            'description': self.description,
            'url': self.url,
            'source': self.source,
            'author': self.author,
            'published_at': self.published_at.isoformat() if self.published_at else None,
            'sentiment': {
                'score': self.sentiment_score,
                'label': self.sentiment_label
            }
        }


class User(db.Model):
    """
    User subscriptions for alerts and reports.
    """
    __tablename__ = 'users'

    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(200), unique=True, index=True)
    telegram_id = db.Column(db.String(100), unique=True, index=True)
    is_email_verified = db.Column(db.Boolean, default=False)
    is_telegram_verified = db.Column(db.Boolean, default=False)
    is_active = db.Column(db.Boolean, default=True)
    daily_report_enabled = db.Column(db.Boolean, default=True)
    report_time_utc = db.Column(db.Time)  # Preferred report time
    watchlist = db.Column(db.Text)  # JSON array of coin IDs
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    alerts = db.relationship('Alert', backref='user', lazy='dynamic', cascade='all, delete-orphan')

    def __repr__(self):
        identifier = self.email or f'TG:{self.telegram_id}'
        return f'<User {identifier}>'

    def to_dict(self):
        return {
            'id': self.id,
            'email': self.email,
            'telegram_id': self.telegram_id,
            'is_active': self.is_active,
            'daily_report_enabled': self.daily_report_enabled,
            'created_at': self.created_at.isoformat()
        }


class Alert(db.Model):
    """
    Custom user alerts for price, volume, sentiment, etc.
    """
    __tablename__ = 'alerts'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False, index=True)
    coin_id = db.Column(db.String(100), db.ForeignKey('coins.id'), index=True)
    alert_type = db.Column(db.String(50), nullable=False)  # price_above, price_below, volume_spike, etc.
    threshold = db.Column(db.Float)
    condition = db.Column(db.Text)  # JSON for complex conditions
    is_active = db.Column(db.Boolean, default=True)
    is_triggered = db.Column(db.Boolean, default=False)
    triggered_at = db.Column(db.DateTime)
    notification_method = db.Column(db.String(50), default='both')  # email, telegram, both
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # Relationships
    coin = db.relationship('Coin', backref=db.backref('alerts', lazy='dynamic'))

    def __repr__(self):
        return f'<Alert {self.alert_type} for {self.coin_id}>'

    def to_dict(self):
        return {
            'id': self.id,
            'coin_id': self.coin_id,
            'alert_type': self.alert_type,
            'threshold': self.threshold,
            'is_active': self.is_active,
            'is_triggered': self.is_triggered,
            'triggered_at': self.triggered_at.isoformat() if self.triggered_at else None,
            'created_at': self.created_at.isoformat()
        }


class OpportunityScore(db.Model):
    """
    Composite opportunity scores for coins.
    """
    __tablename__ = 'opportunity_scores'

    id = db.Column(db.Integer, primary_key=True)
    coin_id = db.Column(db.String(100), db.ForeignKey('coins.id'), nullable=False, index=True)
    date = db.Column(db.Date, nullable=False, index=True)

    # Component scores (0-100)
    sentiment_score = db.Column(db.Float, default=50)
    volume_score = db.Column(db.Float, default=50)
    social_score = db.Column(db.Float, default=50)
    technical_score = db.Column(db.Float, default=50)
    whale_score = db.Column(db.Float, default=50)
    fear_greed_score = db.Column(db.Float, default=50)

    # Composite score (0-100)
    total_score = db.Column(db.Float, nullable=False)
    classification = db.Column(db.String(20))  # Strong, Moderate, Neutral, Weak, Avoid

    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # Relationships
    coin = db.relationship('Coin', backref=db.backref('opportunity_scores', lazy='dynamic'))

    # Unique constraint on coin_id + date
    __table_args__ = (
        db.UniqueConstraint('coin_id', 'date', name='unique_coin_date'),
    )

    def __repr__(self):
        return f'<OpportunityScore {self.coin_id} {self.total_score}>'

    def to_dict(self):
        return {
            'coin_id': self.coin_id,
            'date': self.date.isoformat(),
            'scores': {
                'sentiment': self.sentiment_score,
                'volume': self.volume_score,
                'social': self.social_score,
                'technical': self.technical_score,
                'whale': self.whale_score,
                'fear_greed': self.fear_greed_score,
                'total': self.total_score
            },
            'classification': self.classification
        }
