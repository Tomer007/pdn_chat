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
    config_path = Path(__file__).resolve().parent / "data" / "config.yaml"
    questions_path = Path(__file__).resolve().parent / "data" / "questions.json"
    
    try:
        # Load config
        with open(config_path, "r", encoding="utf-8") as f:
            app.config['PDN_CONFIG'] = yaml.safe_load(f)
        
        # Load questions
        with open(questions_path, "r", encoding="utf-8") as f:
            app.config['QUESTIONS_FILE'] = json.load(f)
            
        logger.info("Configuration loaded successfully")
        
        # Log all configuration data
        logger.info("=== CONFIGURATION DATA START ===")
        logger.info(f"Config file path: {config_path}")
        logger.info(f"Questions file path: {questions_path}")
        logger.info(f"Config file exists: {config_path.exists()}")
        logger.info(f"Questions file exists: {questions_path.exists()}")
        
        # Log PDN_CONFIG
        logger.info("PDN_CONFIG content:")
        logger.info(json.dumps(app.config['PDN_CONFIG'], indent=2, default=str))
        
        # Log QUESTIONS_FILE structure (be careful with large files)
        questions_data = app.config['QUESTIONS_FILE']
        logger.info("QUESTIONS_FILE structure:")
        logger.info(f"Total phases: {len(questions_data.get('phases', {}))}")
        logger.info(f"Phase names: {list(questions_data.get('phases', {}).keys())}")
        
        # Log each phase structure
        for phase_name, phase_data in questions_data.get('phases', {}).items():
            logger.info(f"Phase '{phase_name}':")
            logger.info(f"  - Instructions: {phase_data.get('instructions', 'N/A')}")
            logger.info(f"  - Questions count: {len(phase_data.get('questions', []))}")
            
            # Log first few questions as sample
            questions = phase_data.get('questions', [])
            for i, question in enumerate(questions[:3]):  # Log first 3 questions
                logger.info(f"  - Question {i+1}: {question.get('question', 'N/A')[:100]}...")
            if len(questions) > 3:
                logger.info(f"  - ... and {len(questions) - 3} more questions")
        
        # Log environment variables
        logger.info("Environment variables:")
        env_vars = ['FLASK_ENV', 'FLASK_DEBUG', 'ADMIN_PASSWORD', 'QUESTIONS_FILE']
        for var in env_vars:
            logger.info(f"  {var}: {os.environ.get(var, 'NOT_SET')}")
        
        # Log app config keys
        logger.info("App config keys:")
        for key in sorted(app.config.keys()):
            if key not in ['SECRET_KEY']:  # Skip sensitive data
                value = app.config[key]
                if isinstance(value, (dict, list)):
                    logger.info(f"  {key}: {type(value).__name__} with {len(value)} items")
                else:
                    logger.info(f"  {key}: {value}")
        
        logger.info("=== CONFIGURATION DATA END ===")
        
    except Exception as e:
        logger.error(f"Error loading configuration: {e}")
        logger.error(f"Current working directory: {os.getcwd()}")
        logger.error(f"Files in current directory: {os.listdir('.')}")
        app.config['PDN_CONFIG'] = {}
        app.config['QUESTIONS_FILE'] = {}
    
    # Register blueprints
    app.register_blueprint(pdn_diagnose_bp, url_prefix='/pdn-diagnose')
    app.register_blueprint(pdn_admin_bp, url_prefix='/pdn-admin')
    app.register_blueprint(audio_bp, url_prefix='/pdn-admin')  # Audio endpoints
    app.register_blueprint(pdn_chat_ai_bp, url_prefix='/pdn-chat-ai')
    
    # Mount static files
    app.static_folder = 'static'
    app.static_url_path = '/static'
    
    # Root route
    @app.route('/')
    def root():
        return {"message": "Welcome to PDN Flask Application 1.0 ", "modules": [
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

# Create the app instance for gunicorn
app = create_app()

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=8001)
