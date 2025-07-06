from flask import Blueprint, request, render_template, jsonify, session, current_app

from .logger import setup_logger
from ..utils.answer_storage import load_answers
from ..utils.pdn_calculator import calculate_pdn_code
from ..utils.report_generator import load_pdn_report

# Setup logger
logger = setup_logger()

# Create blueprint
pdn_chat_ai_bp = Blueprint('pdn_chat_ai', __name__,
                           template_folder='../pdn_diagnose/templates',
                           static_folder='../pdn_diagnose/static')


@pdn_chat_ai_bp.route('/')
def chat():
    """Chat interface endpoint"""
    logger.debug("GET /pdn-chat-ai/ called")
    logger.info("Request: %s %s", request.method, request.url)
    logger.info("Response: %s", 200)

    config = current_app.config.get('PDN_CONFIG', {})
    email = session.get("email", None)

    welcome_message = config.get("chatbots", {}).get("chatbot_PDN", {}).get("welcome_message", "Welcome to PDN Chat!")

    return render_template(
        "chat.html",
        welcome_message=welcome_message,
        email=email,
        include_menu=True
    )


@pdn_chat_ai_bp.route('/chat', methods=['POST'])
def chat_message():
    """Handle chat messages"""
    logger.debug("POST /pdn-chat-ai/chat called")
    logger.info("Request: %s %s", request.method, request.url)
    logger.info("Response: %s", 200)

    try:
        data = request.get_json()
        message = data.get('message', '')
        email = session.get('email', 'anonymous')

        # Load user context if available
        user_context = {}
        try:
            user_answers = load_answers(email)
            if user_answers:
                # Calculate PDN code for context
                pdn_code = calculate_pdn_code(user_answers)
                if pdn_code:
                    report_data = load_pdn_report(pdn_code)
                    if report_data:
                        user_context = {
                            'pdn_code': pdn_code,
                            'report_data': report_data,
                            'user_answers': user_answers
                        }
        except Exception as e:
            logger.warning(f"Could not load user context: {e}")

        # TODO: Implement actual AI chat logic here
        # For now, return a simple response
        response = {
            "message": f"Thank you for your message: '{message}'. This is a placeholder response. User context: {bool(user_context)}",
            "user_context": user_context
        }

        return jsonify(response)

    except Exception as e:
        logger.error(f"Error in chat: {e}")
        return jsonify({"error": "Chat error occurred"}), 500


@pdn_chat_ai_bp.route('/context')
def get_user_context():
    """Get user context for chat"""
    logger.debug("GET /pdn-chat-ai/context called")
    logger.info("Request: %s %s", request.method, request.url)
    logger.info("Response: %s", 200)

    try:
        email = session.get('email', 'anonymous')
        user_context = {}

        # Load user answers
        user_answers = load_answers(email)
        if user_answers:
            # Calculate PDN code
            pdn_code = calculate_pdn_code(user_answers)
            if pdn_code:
                # Load report data
                report_data = load_pdn_report(pdn_code)
                if report_data:
                    user_context = {
                        'pdn_code': pdn_code,
                        'report_data': report_data,
                        'user_answers': user_answers
                    }

        return jsonify(user_context)

    except Exception as e:
        logger.error(f"Error getting user context: {e}")
        return jsonify({"error": "Could not load user context"}), 500


@pdn_chat_ai_bp.route('/history')
def get_chat_history():
    """Get chat history for user"""
    logger.debug("GET /pdn-chat-ai/history called")
    logger.info("Request: %s %s", request.method, request.url)
    logger.info("Response: %s", 200)

    try:
        email = session.get('email', 'anonymous')

        # TODO: Implement chat history storage and retrieval
        # For now, return empty history
        history = []

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
        email = session.get('email', 'anonymous')

        # TODO: Implement chat history clearing
        # For now, just return success

        return jsonify({"message": "Chat history cleared successfully"})

    except Exception as e:
        logger.error(f"Error clearing chat history: {e}")
        return jsonify({"error": "Could not clear chat history"}), 500


@pdn_chat_ai_bp.route('/settings')
def get_chat_settings():
    """Get chat settings"""
    logger.debug("GET /pdn-chat-ai/settings called")
    logger.info("Request: %s %s", request.method, request.url)
    logger.info("Response: %s", 200)

    try:
        config = current_app.config.get('PDN_CONFIG', {})
        chat_settings = config.get("chatbots", {}).get("chatbot_PDN", {})

        return jsonify(chat_settings)

    except Exception as e:
        logger.error(f"Error getting chat settings: {e}")
        return jsonify({"error": "Could not load chat settings"}), 500


@pdn_chat_ai_bp.route('/settings', methods=['PUT'])
def update_chat_settings():
    """Update chat settings"""
    logger.debug("PUT /pdn-chat-ai/settings called")
    logger.info("Request: %s %s", request.method, request.url)
    logger.info("Response: %s", 200)

    try:
        settings = request.get_json()

        # TODO: Implement settings update logic
        # For now, just return success

        return jsonify({"message": "Settings updated successfully"})

    except Exception as e:
        logger.error(f"Error updating chat settings: {e}")
        return jsonify({"error": "Could not update settings"}), 500
