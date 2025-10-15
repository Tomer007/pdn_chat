import json
import logging
import os
from flask import Flask, request
from pathlib import Path

from app.pdn_admin import pdn_admin_bp, audio_bp
from app.pdn_chat_ai import pdn_chat_ai_bp
from app.pdn_diagnose import pdn_diagnose_bp
from app.neo import neo_bp
from flask_session import Session
from app.utils.memory_monitor import start_memory_monitoring

def create_app():
    """Application factory pattern for Flask app creation"""
    app = Flask(__name__)

    # Configuration
    app.config.update(
        SECRET_KEY=os.getenv('SECRET_KEY', 'your-very-secret-key'),
        SESSION_TYPE='filesystem'
    )

    Session(app)

    # Setup logging
    os.makedirs('logs', exist_ok=True)
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[logging.StreamHandler(), logging.FileHandler('logs/app.log')]
    )

    logger = logging.getLogger(__name__)

    # Load questions
    questions_path = Path(__file__).parent / "data" / "questions.json"
    try:
        app.config['QUESTIONS_FILE'] = json.loads(questions_path.read_text(encoding="utf-8"))
        logger.info(f"Loaded {len(app.config['QUESTIONS_FILE'].get('phases', {}))} question phases")
    except Exception as e:
        logger.error(f"Failed to load questions: {e}")
        app.config['QUESTIONS_FILE'] = {}

    # Register blueprints
    for bp, prefix in [
        (pdn_diagnose_bp, '/pdn-diagnose'),
        (pdn_admin_bp, '/pdn-admin'),
        (audio_bp, '/pdn-admin'),
        (pdn_chat_ai_bp, '/pdn-chat-ai'),
        (neo_bp, '/neo')
    ]:
        app.register_blueprint(bp, url_prefix=prefix)

    # Production monitoring
    if os.getenv('FLASK_ENV') == 'production':
        start_memory_monitoring()

    # Root route
    @app.route('/')
    def root():
        return {
            "message": "Welcome to PDN Flask Application 1.0",
            "modules": [
                "/pdn-diagnose - Personal development interaction",
                "/pdn-admin - Admin dashboard and monitoring",
                "/pdn-chat-ai - AI chat assistance",
                "/neo - Neo P.D.N Center"
            ]
        }

    # Request/response logging
    @app.before_request
    def log_request():
        logger.info(f"{request.method} {request.url}")

    @app.after_request
    def log_response(response):
        logger.info(f"Status: {response.status_code}")
        return response

    return app


app = create_app()

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=8001)
