# Crypto Market Sentiment Analysis Dashboard

A professional web-based dashboard that displays cryptocurrency market sentiment, technical indicators, whale activity, exchange listings, and influencer mentions. Users can subscribe to daily reports via email or Telegram.

## Features

### Core Features
- **Real-time Market Data**: Live cryptocurrency prices, market cap, and volume from CoinGecko
- **Fear & Greed Index**: Track market sentiment with historical data visualization
- **Trending Coins**: Discover which cryptocurrencies are gaining attention
- **Volume Spike Detection**: Identify unusual trading activity

### Advanced Features
- **Whale Activity Tracker**: Monitor large transactions ($1M+) across blockchains
- **Social Sentiment Analysis**: Reddit sentiment tracking across crypto subreddits
- **News Aggregation**: Crypto news with sentiment analysis
- **Technical Indicators**: RSI, MACD, moving averages (via Alpha Vantage)
- **Sector Analysis**: Compare performance across DeFi, NFTs, Layer 1s, etc.
- **Exchange Listing Alerts**: Track new Coinbase/Binance listings

### Notifications
- **Email Reports**: Daily summaries via SendGrid (100 emails/day free)
- **Telegram Bot**: Real-time alerts and daily digests (free, unlimited)
- **Custom Alerts**: Set personalized thresholds for price, volume, and sentiment

### Opportunity Scoring
- Composite score (0-100) based on multiple factors:
  - Sentiment trend
  - Volume spikes
  - Social buzz
  - Technical indicators
  - Whale accumulation
  - Fear & Greed alignment

## Tech Stack

- **Backend**: Python 3.11+ with Flask
- **Frontend**: HTML/CSS/JavaScript with Chart.js
- **Database**: SQLite (easily upgradable to PostgreSQL)
- **APIs**: CoinGecko, Whale Alert, Reddit, NewsAPI, and more
- **Email**: SendGrid
- **Notifications**: Telegram Bot API
- **Scheduling**: APScheduler

## Quick Start

### Prerequisites

- Python 3.11 or higher
- Git
- A code editor (VS Code recommended)

### Installation

1. **Clone the repository**
   ```bash
   git clone https://github.com/YOUR_USERNAME/crypto-sentiment-dashboard.git
   cd crypto-sentiment-dashboard
   ```

2. **Create a virtual environment**
   ```bash
   python -m venv venv

   # On macOS/Linux:
   source venv/bin/activate

   # On Windows:
   venv\Scripts\activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Set up environment variables**
   ```bash
   cp .env.example .env
   # Edit .env with your API keys
   ```

5. **Initialize the database**
   ```bash
   python -c "from app import create_app, db; app = create_app(); app.app_context().push(); db.create_all()"
   ```

6. **Run the application**
   ```bash
   python run.py
   ```

7. **Open your browser**
   Navigate to `http://localhost:5000`

## API Keys Setup

Most features work without API keys, but for full functionality:

| API | Required? | Free Tier | Get Key |
|-----|-----------|-----------|---------|
| CoinGecko | No | 50 calls/min | N/A |
| Fear & Greed | No | Unlimited | N/A |
| Whale Alert | Yes* | 1000/month | [whale-alert.io](https://whale-alert.io/) |
| Reddit | Yes* | 60/min | [reddit.com/prefs/apps](https://reddit.com/prefs/apps) |
| NewsAPI | Yes* | 100/day | [newsapi.org](https://newsapi.org/) |
| SendGrid | Yes* | 100/day | [sendgrid.com](https://sendgrid.com/) |
| Alpha Vantage | Optional | 500/day | [alphavantage.co](https://www.alphavantage.co/) |

*Required for specific features only

## Project Structure

```
crypto-sentiment-dashboard/
├── app/
│   ├── __init__.py          # Flask app factory
│   ├── routes.py             # API routes and views
│   ├── models.py             # Database models
│   ├── api/                  # External API wrappers
│   │   ├── coingecko.py      # CoinGecko API client
│   │   ├── whale_alert.py    # Whale Alert API client
│   │   ├── reddit_client.py  # Reddit API (PRAW)
│   │   ├── news_api.py       # NewsAPI client
│   │   └── fear_greed.py     # Fear & Greed Index
│   ├── utils/                # Utility modules
│   │   ├── cache.py          # Caching utilities
│   │   ├── rate_limiter.py   # API rate limiting
│   │   └── sentiment.py      # Sentiment analysis
│   ├── templates/            # HTML templates
│   └── static/               # CSS, JS, images
├── tests/                    # Test suite
├── logs/                     # Application logs
├── config.py                 # Configuration
├── run.py                    # Application entry point
├── requirements.txt          # Python dependencies
├── .env.example              # Environment template
└── README.md                 # This file
```

## Configuration

All configuration is done through environment variables. See `.env.example` for all available options.

Key settings:
- `DEBUG`: Enable debug mode (default: False)
- `DATABASE_URL`: Database connection string
- `SECRET_KEY`: Flask secret key (generate a random one for production)

## Development

### Running Tests
```bash
pytest
```

### Code Formatting
```bash
black .
isort .
flake8
```

### Database Migrations
```bash
flask db migrate -m "Description"
flask db upgrade
```

## Deployment

See [DEPLOYMENT.md](docs/DEPLOYMENT.md) for detailed deployment guides:
- Railway.app (recommended for beginners)
- Heroku
- DigitalOcean
- Docker

## API Rate Limits

The application implements intelligent caching and rate limiting:

| Data Type | Cache Duration | Reason |
|-----------|---------------|--------|
| Prices | 5 minutes | Balance freshness with API limits |
| Fear & Greed | 4 hours | Index updates daily |
| Whale Transactions | 15 minutes | Real-time isn't critical |
| Reddit Sentiment | 30 minutes | Trends change slowly |
| News | 1 hour | Headlines don't change rapidly |

## Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'feat: Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

### Commit Message Convention

We use [Conventional Commits](https://www.conventionalcommits.org/):
- `feat:` New feature
- `fix:` Bug fix
- `docs:` Documentation changes
- `style:` Code formatting
- `refactor:` Code restructuring
- `test:` Adding tests
- `chore:` Maintenance tasks

## Roadmap

- [x] Phase 0: Project setup
- [ ] Phase 1: Core API integration
- [ ] Phase 2: Dashboard UI
- [ ] Phase 3: Advanced features (whale tracking, influencers)
- [ ] Phase 4: Alert system and opportunity scoring
- [ ] Phase 5: Email/Telegram notifications
- [ ] Phase 6: Analytics and personalization
- [ ] Phase 7: Documentation and deployment

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Disclaimer

This application is for informational purposes only. It is not financial advice. Always do your own research before making investment decisions. Cryptocurrency investments carry significant risk.

## Acknowledgments

- [CoinGecko](https://www.coingecko.com/) for comprehensive crypto data
- [Alternative.me](https://alternative.me/) for Fear & Greed Index
- [Whale Alert](https://whale-alert.io/) for large transaction tracking
- All the open-source libraries that make this possible

---

Built with Python and caffeine
