import os
import uuid
import json
from datetime import datetime
from werkzeug.utils import secure_filename
from flask import Blueprint, request, render_template, jsonify, session, current_app, send_from_directory

from .logger import setup_logger
from ..utils.answer_storage import load_answers
from ..utils.pdn_calculator import calculate_pdn_code
from ..utils.report_generator import load_pdn_report
from ..utils.conversation_history import conversation_history

# Setup logger
logger = setup_logger()

# Replace with this lazy initialization approach:
_rag_system = None

def get_rag_system():
    """Get or initialize the RAG system lazily"""
    global _rag_system
    if _rag_system is None:
        try:
            from .pdn_chat_rag import PDNRAG
            _rag_system = PDNRAG("./rag", persist_dir="./chroma_db", persist=True)
            logger.info("RAG system initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize RAG system: {e}")
            _rag_system = None
    return _rag_system

# Create blueprint
pdn_chat_ai_bp = Blueprint('pdn_chat_ai', __name__,
                           template_folder='templates',
                           static_folder='../static')


@pdn_chat_ai_bp.route('/')
def chat():
    """Binat Chat AI login endpoint"""

    logger.debug("GET /pdn-chat-ai/ called")
    logger.info("Request: %s %s", request.method, request.url)
    logger.info("Response: %s", 200)

    return render_template("binat_login.html")


@pdn_chat_ai_bp.route('/chat-ai')
def chat_interface():
    """Chat interface endpoint - accessed after login"""
    logger.debug("GET /pdn-chat-ai/chat-ai called")
    logger.info("Request: %s %s", request.method, request.url)
    logger.info("Response: %s", 200)

    # Get user name from query parameters
    user_name = request.args.get('user_name', 'Anonymous')
    user_id = request.args.get('user_id', '')

    config = current_app.config.get('PDN_CONFIG', {})
    welcome_message = config.get("chatbots", {}).get("chatbot_PDN", {}).get("welcome_message", "ברוך הבא לבינת קוד המקור ")

    return render_template(
        "chat.html",
        welcome_message=welcome_message,
        user_name=user_name,
        user_id=user_id,
        include_menu=True
    )


@pdn_chat_ai_bp.route('/history')
def get_chat_history():
    """Get chat history for user"""
    logger.debug("GET /pdn-chat-ai/history called")
    logger.info("Request: %s %s", request.method, request.url)
    logger.info("Response: %s", 200)

    try:
        # Get user_id from query parameters or session
        user_id = request.args.get('user_id') or session.get('user_id', 'anonymous')
        
        # Get conversation history
        history = conversation_history.get_history(user_id)
        
        return jsonify({"history": history})

    except Exception as e:
        logger.error(f"Error getting chat history: {e}")
        return jsonify({"error": "Could not load chat history"}), 500


@pdn_chat_ai_bp.route('/clear_history', methods=['POST'])
def clear_chat_history():
    """Clear chat history for user"""
    logger.debug("POST /pdn-chat-ai/clear_history called")
    logger.info("Request: %s %s", request.method, request.url)
    logger.info("Response: %s", 200)

    try:
        data = request.get_json() or {}
        user_id = data.get('user_id') or session.get('user_id', 'anonymous')

        # Clear conversation history
        success = conversation_history.clear_history(user_id)
        
        if success:
            return jsonify({"message": "Chat history cleared successfully"})
        else:
            return jsonify({"error": "Could not clear chat history"}), 500

    except Exception as e:
        logger.error(f"Error clearing chat history: {e}")
        return jsonify({"error": "Could not clear chat history"}), 500


@pdn_chat_ai_bp.route('/chat', methods=['POST'])
def chat_message():
    """Handle chat messages with improved AI responses"""
    logger.debug("POST /pdn-chat-ai/chat called")
    logger.info("Request: %s %s", request.method, request.url)
    
    try:
        data = request.get_json()
        if not data:
            return jsonify({"error": "No data provided"}), 400
            
        message = data.get('message', '').strip()
        user_name = data.get('user_name', 'Anonymous')
        user_id = data.get('user_id', '')
        
        if not message:
            return jsonify({"error": "Message cannot be empty"}), 400
        
        # Check if RAG system is available
        rag = get_rag_system()
        if rag is None:
            logger.error("RAG system not initialized")
            return jsonify({
                "error": "AI system not available. Please try again later.",
                "response": "מערכת הבינה המלאכותית אינה זמינה כרגע. אנא נסה שוב מאוחר יותר."
            }), 503
        
        # Generate AI response using RAG
        try:
            response = rag.retrieve(message, user_name, user_id)
            logger.info("AI response generated successfully")
            
            return jsonify({
                "response": response,
                "timestamp": datetime.now().isoformat()
            })
        except Exception as e:
            logger.error(f"Error generating AI response: {e}")
            return jsonify({
                "error": "Failed to generate response",
                "response": "מצטער, לא הצלחתי לעבד את השאלה שלך. אנא נסה שוב."
            }), 500

    except Exception as e:
        logger.error(f"Error in chat: {e}")
        return jsonify({"error": "Chat error occurred"}), 500

