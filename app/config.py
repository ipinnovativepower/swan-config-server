import os

class Config:
    """Base configuration class for Flask application."""

    # Secret key for session management and CSRF protection
    SECRET_KEY = os.environ.get('SECRET_KEY', 'you-will-never-guess')

    # Custom configuration options can be added here
    CUSTOM_SETTING = os.environ.get('CUSTOM_SETTING', 'default_value')

    # Example for debug mode (not for production)
    DEBUG = os.environ.get('FLASK_DEBUG', 'true') == 'true'
