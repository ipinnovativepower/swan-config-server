from flask import Flask
from .config import Config
from .views.main import main_bp
from .views.auth import auth_bp
from .views.api import api_bp

def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)
        
    # Register blueprints
    app.register_blueprint(main_bp)
    app.register_blueprint(auth_bp)
    app.register_blueprint(api_bp, url_prefix='/api')

    return app