"""
PDN Chat AI Routes - Flask routes for AI-powered chat interface.
Handles user authentication, chat messaging, and 21-day plan generation.
"""

import uuid
from datetime import datetime
from flask import Blueprint, request, render_template, jsonify, session, current_app

from .binat_agents.pdn_agent import PDNAgent
from .logger import setup_logger

# Setup logger
logger = setup_logger()

# Global agent instance to maintain conversation history
_pdn_agent = None

# Single source of truth for valid PDN codes
VALID_PDN_CODES = ["A7", "E5", "P6", "P10"]

def get_agent_instance():
    """Get or create the single PDN agent instance"""
    global _pdn_agent
    
    if _pdn_agent is None:
        _pdn_agent = PDNAgent()
        logger.info("Created new PDNAgent instance")
    
    return _pdn_agent


def validate_pdn_authorization(pdn_code: str, user_name: str, endpoint_name: str) -> tuple[bool, dict]:
    """
    Validate PDN code authorization.
    
    Args:
        pdn_code: The user's PDN code to validate
        user_name: The user's name for logging
        endpoint_name: The endpoint being accessed for logging
        
    Returns:
        tuple: (is_authorized, error_response_dict)
    """
    if not pdn_code or pdn_code not in VALID_PDN_CODES:
        logger.warning("Unauthorized access attempt to %s - User: %s, PDN Code: %s", 
                      endpoint_name, user_name, pdn_code)
        
        error_response = {
            "error": "Unauthorized access",
            "response": f"משתמש {user_name} לא מורשה לגשת למערכת. קוד PDN: {pdn_code} אינו תקין.",
            "timestamp": datetime.now().isoformat()
        }
        return False, error_response
    
    return True, {}




# Static user data for authentication
USERS_DATA = {
    'tomergur@gmail.com': {
        'password': 'pdn',
        'pdn_code': 'E5',
        'name': 'תומר'
    },
    'pdncode@gmail.com': {
        'password': 'pdn',
        'pdn_code': 'A7',
        'name': 'פנינה'
    },
    'orna@84zebras.co.il': {
        'password': 'pdn',
        'pdn_code': 'P10',
        'name': 'אורנה'
    },
    'info.dede.studio@gmail.com': {
        'password': 'pdn',
        'pdn_code': 'A7',
        'name': 'דניאל'
    },
    'sigal4170@gmail.com': {    
        'password': 'pdn',
        'pdn_code': 'P6',
        'name': 'סיגל'
    }
}

# Create blueprint
pdn_chat_ai_bp = Blueprint('pdn_chat_ai', __name__,
                           template_folder='templates',
                           static_folder='../static')


@pdn_chat_ai_bp.route('/')
def chat():
    """Binat Chat AI login endpoint"""
    logger.info("Login page accessed")
    return render_template("binat_login.html")


@pdn_chat_ai_bp.route('/login', methods=['POST'])
def login():
    """Handle user login with email and password verification"""
    logger.info("Login attempt")

    try:
        data = request.get_json()
        if not data:
            return jsonify({"error": "No data provided"}), 400

        email = data.get('email', '').strip()
        password = data.get('password', '').strip()

        if not email or not password:
            return jsonify({"error": "Email and password are required"}), 400

        # Check if user exists and password is correct
        if email in USERS_DATA and USERS_DATA[email]['password'] == password:
            user_data = USERS_DATA[email]

            # Generate a unique user ID for this session
            user_id = str(uuid.uuid4())

            # Store user data in session
            session['user_id'] = user_id
            session['user_email'] = email
            session['user_name'] = user_data['name']
            session['pdn_code'] = user_data['pdn_code']

            logger.info("User %s logged in successfully", email)

            return jsonify({
                "success": True,
                "message": "Login successful",
                "user_id": user_id,
                "user_name": user_data['name'],
                "pdn_code": user_data['pdn_code']
            })
        else:
            logger.warning("Failed login attempt for email: %s", email)
            return jsonify({
                "success": False,
                "error": "Invalid email or password"
            }), 401

    except (KeyError, ValueError, TypeError) as e:
        logger.error("Error in login: %s", e)
        return jsonify({"error": "Login error occurred"}), 500


@pdn_chat_ai_bp.route('/logout', methods=['POST'])
def logout():
    """Handle user logout"""
    logger.info("User logout")

    try:
        # Clear conversation history from the agent instance
        user_name = session.get('user_name')
        if user_name:
            agent = get_agent_instance()
            agent.clear_user_history(user_name)
            logger.info("Cleared conversation history for user: %s", user_name)
        
        # Clear session data
        session.clear()
        logger.info("User logged out successfully")

        return jsonify({
            "success": True,
            "message": "Logout successful"
        })

    except (KeyError, ValueError) as e:
        logger.error("Error in logout: %s", e)
        return jsonify({"error": "Logout error occurred"}), 500


@pdn_chat_ai_bp.route('/chat-ai')
def chat_interface():
    """Chat interface endpoint - accessed after login"""
    logger.info("Chat interface accessed")

    # Get user data from session or query parameters
    user_name = session.get('user_name') or request.args.get('user_name', 'Anonymous')
    user_id = session.get('user_id') or request.args.get('user_id', '')
    pdn_code = session.get('pdn_code') or request.args.get('pdn_code', '')

    # Check if user is authorized (has valid PDN code)
    is_authorized, error_response = validate_pdn_authorization(pdn_code, user_name, "chat-interface")
    if not is_authorized:
        return render_template(
            "chat.html",
            welcome_message=error_response["response"],
            user_name=user_name,
            user_id=user_id,
            pdn_code=pdn_code,
            include_menu=True,
            error_message=error_response["response"]
        )

    config = current_app.config.get('PDN_CONFIG', {})
    welcome_message = config.get("chatbots", {}).get("chatbot_PDN", {}).get("welcome_message",
                                                                            "ברוך הבא לבינת קוד המקור ")

    return render_template(
        "chat.html",
        welcome_message=welcome_message,
        user_name=user_name,
        user_id=user_id,
        pdn_code=pdn_code,
        include_menu=True
    )


@pdn_chat_ai_bp.route('/chat', methods=['POST'])
def chat_message():
    """Handle chat messages with improved AI responses"""
    logger.info("Chat message received")

    try:
        data = request.get_json()
        if not data:
            return jsonify({"error": "No data provided"}), 400

        message = data.get('message', '').strip()
        user_name = data.get('user_name', 'Anonymous')
        pdn_code = data.get('pdn_code', '')

        # Check if user is authorized (has valid PDN code)
        is_authorized, error_response = validate_pdn_authorization(pdn_code, user_name, "chat")
        if not is_authorized:
            return jsonify(error_response), 403

        # Get the single agent instance
        agent = get_agent_instance()
        
        return jsonify({
            "response": agent.chat_with_user(message, user_name, pdn_code),
            "timestamp": datetime.now().isoformat()
        })

    except (ValueError, AttributeError, TypeError) as e:
        logger.error("Error in chat: %s", e)
        return jsonify({"error": "Chat error occurred"}), 500


@pdn_chat_ai_bp.route('/21-day-plan', methods=['POST'])
def create_21_day_plan():
    """Handle 21-day transformation plan requests"""
    logger.info("21-day plan request received")

    try:
        data = request.get_json()
        
        if not data:
            logger.warning("No data provided in request")
            return jsonify({"error": "No data provided"}), 400

        goals = data.get('goals', '').strip()
        success = data.get('success', '').strip()
        user_name = data.get('user_name', 'Anonymous')
        pdn_code = data.get('pdn_code', '')

        logger.info("Processing 21-day plan for %s (PDN: %s)", user_name, pdn_code)

        # Check if user is authorized (has valid PDN code)
        is_authorized, error_response = validate_pdn_authorization(pdn_code, user_name, "21-day-plan")
        if not is_authorized:
            return jsonify(error_response), 403

        if not goals or not success:
            logger.warning("Missing goals or success definition")
            return jsonify({"error": "Goals and success definition are required"}), 400

        # Create user context for the 21-day plan
        user_context = f"""
        User Goals: {goals}
        User Success Definition: {success}
        """

        # Generate response using the single PDN agent
        try:
            agent = get_agent_instance()
            response = agent.build_21_transformation_plan(user_context, user_name, pdn_code)
            
        except (AttributeError, ValueError, ImportError) as agent_error:
            logger.error("Error with PDNAgent: %s", agent_error)
            response = "I apologize, but I encountered an error while processing your request. Please try again."
        except Exception as timeout_error:
            logger.error("Unexpected error with PDNAgent: %s", timeout_error)
            if "timeout" in str(timeout_error).lower() or "timed out" in str(timeout_error).lower():
                response = (
                    "I apologize, but the request is taking longer than expected. "
                    "This might be due to high server load. Please try again in a few moments."
                )
            else:
                response = "I apologize, but I encountered an unexpected error. Please try again."

        return jsonify({
            "response": response,
            "timestamp": datetime.now().isoformat()
        })

    except (ValueError, KeyError, TypeError) as e:
        logger.error("Error creating 21-day plan: %s", e)
        return jsonify({"error": "Failed to create 21-day plan"}), 500
