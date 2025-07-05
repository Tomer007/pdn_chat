import json
import logging
import os
from pathlib import Path
from flask import Flask, request
from flask_session import Session
import yaml

# Import blueprints
from app.pdn_diagnose import pdn_diagnose_bp
from app.pdn_admin import pdn_admin_bp, audio_bp
from app.pdn_chat_ai import pdn_chat_ai_bp

def create_app():
    """Application factory pattern for Flask app creation"""
    app = Flask(__name__)
    
    # Configure app
    app.config['SECRET_KEY'] = 'your-very-secret-key'
    app.config['SESSION_TYPE'] = 'filesystem'
    
    # Initialize Flask-Session
    Session(app)
    
    # Ensure logs directory exists
    os.makedirs('logs', exist_ok=True)
    
    # Configure logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(),  # Console handler
            logging.FileHandler('logs/app.log')  # File handler
        ]
    )
    
    # Create logger
    logger = logging.getLogger(__name__)
    
    # Load configuration
    config_path = Path(__file__).resolve().parent / "app" / "data" / "config.yaml"
    questions_path = Path(__file__).resolve().parent / "app" / "data" / "questions.json"
    
    try:
        # Load config
        with open(config_path, "r", encoding="utf-8") as f:
            app.config['PDN_CONFIG'] = yaml.safe_load(f)
        
        # Load questions
        with open(questions_path, "r", encoding="utf-8") as f:
            app.config['PDN_QUESTIONS'] = json.load(f)
            
        logger.info("Configuration loaded successfully")
    except Exception as e:
        logger.error(f"Error loading configuration: {e}")
        app.config['PDN_CONFIG'] = {}
        app.config['PDN_QUESTIONS'] = {}
    
    # Register blueprints
    app.register_blueprint(pdn_diagnose_bp, url_prefix='/pdn-diagnose')
    app.register_blueprint(pdn_admin_bp, url_prefix='/pdn-admin')
    app.register_blueprint(audio_bp, url_prefix='/pdn-admin')  # Audio endpoints
    app.register_blueprint(pdn_chat_ai_bp, url_prefix='/pdn-chat-ai')
    
    # Mount static files
    app.static_folder = 'app/static'
    app.static_url_path = '/static'
    
    # Root route
    @app.route('/')
    def root():
        return {"message": "Welcome to PDN Flask Application!", "modules": [
            "/pdn-diagnose - Personal development interaction",
            "/pdn-admin - Admin dashboard and monitoring", 
            "/pdn-chat-ai - AI chat assistance"
        ]}
    
    # Request logging middleware
    @app.before_request
    def log_request_info():
        logger.info(f"Request: {request.method} {request.url}")
    
    @app.after_request
    def log_response_info(response):
        logger.info(f"Response: {response.status_code}")
        return response
    
    return app

if __name__ == '__main__':
    app = create_app()
    app.run(debug=True, host='0.0.0.0', port=8001) 