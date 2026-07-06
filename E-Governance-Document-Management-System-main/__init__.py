from flask import Flask
from .database import mongo, init_db

def create_app():
    app = Flask(__name__)
    
    # Load configuration
    app.config.from_pyfile('config.py')
    
    # Initialize database
    init_db(app)
    
    # Register blueprints
    from .documents import documents_bp
    app.register_blueprint(documents_bp)
    
    return app