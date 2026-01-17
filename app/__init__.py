"""
Crypto Sentiment Dashboard - Flask Application Factory

This module creates and configures the Flask application using the
factory pattern, allowing for different configurations (development,
production, testing).
"""

import logging
import os
from logging.handlers import RotatingFileHandler

from flask import Flask
from flask_cors import CORS
from flask_sqlalchemy import SQLAlchemy

from config import get_config

# Initialize extensions (without app)
db = SQLAlchemy()


def create_app(config_name: str = None) -> Flask:
    """
    Application factory function.

    Creates and configures the Flask application with all extensions,
    blueprints, and error handlers.

    Args:
        config_name: Configuration environment (development, production, testing)

    Returns:
        Configured Flask application instance
    """
    # Create Flask app
    app = Flask(__name__)

    # Load configuration
    config_class = get_config(config_name)
    app.config.from_object(config_class)

    # Initialize extensions with app
    initialize_extensions(app)

    # Register blueprints
    register_blueprints(app)

    # Configure logging
    configure_logging(app)

    # Register error handlers
    register_error_handlers(app)

    # Create database tables
    with app.app_context():
        db.create_all()

    app.logger.info('Crypto Sentiment Dashboard initialized successfully')

    return app


def initialize_extensions(app: Flask) -> None:
    """Initialize Flask extensions."""
    # Database
    db.init_app(app)

    # CORS
    CORS(app, origins=app.config.get('CORS_ORIGINS', ['*']))


def register_blueprints(app: Flask) -> None:
    """Register Flask blueprints."""
    from app.routes import main_bp, api_bp

    app.register_blueprint(main_bp)
    app.register_blueprint(api_bp, url_prefix='/api/v1')


def configure_logging(app: Flask) -> None:
    """Configure application logging."""
    log_level = getattr(logging, app.config.get('LOG_LEVEL', 'INFO'))
    log_file = app.config.get('LOG_FILE', 'logs/app.log')

    # Ensure logs directory exists
    log_dir = os.path.dirname(log_file)
    if log_dir and not os.path.exists(log_dir):
        os.makedirs(log_dir)

    # Configure file handler
    if not app.debug:
        file_handler = RotatingFileHandler(
            log_file,
            maxBytes=10 * 1024 * 1024,  # 10MB
            backupCount=10
        )
        file_handler.setFormatter(logging.Formatter(
            '%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]'
        ))
        file_handler.setLevel(log_level)
        app.logger.addHandler(file_handler)

    # Set app logger level
    app.logger.setLevel(log_level)


def register_error_handlers(app: Flask) -> None:
    """Register error handlers for common HTTP errors."""

    @app.errorhandler(404)
    def not_found_error(error):
        return {'error': 'Resource not found', 'status': 404}, 404

    @app.errorhandler(500)
    def internal_error(error):
        db.session.rollback()
        return {'error': 'Internal server error', 'status': 500}, 500

    @app.errorhandler(429)
    def rate_limit_error(error):
        return {'error': 'Rate limit exceeded', 'status': 429}, 429
