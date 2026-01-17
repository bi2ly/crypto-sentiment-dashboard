#!/usr/bin/env python3
"""
Crypto Sentiment Dashboard - Application Entry Point

This is the main entry point for running the Flask application.

Usage:
    Development:
        python run.py

    Production (with gunicorn):
        gunicorn -w 4 -b 0.0.0.0:5000 "app:create_app()"

Environment Variables:
    FLASK_ENV: Set to 'development', 'production', or 'testing'
    HOST: Server host (default: 127.0.0.1)
    PORT: Server port (default: 5000)
    DEBUG: Enable debug mode (default: False in production)
"""

import os
import sys

# Add the project root to the Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import create_app
from config import Config


def main():
    """Run the Flask development server."""
    # Create the application
    app = create_app()

    # Get configuration
    host = Config.HOST
    port = Config.PORT
    debug = Config.DEBUG

    # Print startup message
    print(f"""
    ╔══════════════════════════════════════════════════════════════╗
    ║         Crypto Sentiment Dashboard v0.1.0                    ║
    ║                                                              ║
    ║  Server running at: http://{host}:{port}                    ║
    ║  Debug mode: {'ON' if debug else 'OFF'}                                           ║
    ║                                                              ║
    ║  Press CTRL+C to quit                                        ║
    ╚══════════════════════════════════════════════════════════════╝
    """)

    # Run the development server
    app.run(
        host=host,
        port=port,
        debug=debug
    )


if __name__ == '__main__':
    main()
