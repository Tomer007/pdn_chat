"""
PDN Chat AI Routes - Flask routes for AI-powered chat interface.
Handles user authentication, chat messaging, and 45-day plan generation.
"""

import uuid
from datetime import datetime
from string import Template
from flask import Blueprint, request, render_template, jsonify, session, current_app

from .binat_agents.a7_agent import A7Agent
from .logger import setup_logger

# Setup logger
logger = setup_logger()

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
    }

}

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
        except (ImportError, AttributeError, ValueError) as e:
            logger.error("Failed to initialize RAG system: %s", e)
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


@pdn_chat_ai_bp.route('/login', methods=['POST'])
def login():
    """Handle user login with email and password verification"""
    logger.debug("POST /pdn-chat-ai/login called")
    logger.info("Request: %s %s", request.method, request.url)

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
    logger.debug("POST /pdn-chat-ai/logout called")
    logger.info("Request: %s %s", request.method, request.url)

    try:

        A7Agent().clear_user_history(session.get('user_name'))
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
    logger.debug("GET /pdn-chat-ai/chat-ai called")
    logger.info("Request: %s %s", request.method, request.url)
    logger.info("Response: %s", 200)

    # Get user data from session or query parameters
    user_name = session.get('user_name') or request.args.get('user_name', 'Anonymous')
    user_id = session.get('user_id') or request.args.get('user_id', '')
    pdn_code = session.get('pdn_code') or request.args.get('pdn_code', '')

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
    logger.debug("POST /pdn-chat-ai/chat called")
    logger.info("Request: %s %s", request.method, request.url)

    try:
        data = request.get_json()
        if not data:
            return jsonify({"error": "No data provided"}), 400

        message = data.get('message', '').strip()
        user_name = data.get('user_name', 'Anonymous')
        # user_id = data.get('user_id', '')
        pdn_code = data.get('pdn_code', '')

        if pdn_code == "A7":
            return jsonify({
                "response": A7Agent().get_response(message, user_name, pdn_code),
                "timestamp": datetime.now().isoformat()
            })
        else:
            raise ValueError(f"Unknown PDN code: {pdn_code}")

        # # Check if RAG system is available
        # rag = get_rag_system()
        # if rag is None:
        #     logger.error("RAG system not initialized")
        #     return jsonify({
        #         "error": "AI system not available. Please try again later.",
        #         "response": "מערכת הבינה המלאכותית אינה זמינה כרגע. אנא נסה שוב מאוחר יותר."
        #     }), 503

        # # Generate AI response using RAG
        # try:
        #     response = rag.retrieve(message, user_name, user_id, pdn_code)
        #     logger.info("AI response generated successfully")

        #     return jsonify({
        #         "response": response,
        #         "timestamp": datetime.now().isoformat()
        #     })
        # except Exception as e:
        #     logger.error(f"Error generating AI response: {e}")
        #     return jsonify({
        #         "error": "Failed to generate response",
        #         "response": "מצטער, לא הצלחתי לעבד את השאלה שלך. אנא נסה שוב."
        #     }), 500

    except (ValueError, AttributeError, TypeError) as e:
        logger.error("Error in chat: %s", e)
        return jsonify({"error": "Chat error occurred"}), 500


@pdn_chat_ai_bp.route('/45-day-plan', methods=['POST'])
def create_45_day_plan():
    """Handle 45-day transformation plan requests"""
    logger.debug("POST /pdn-chat-ai/45-day-plan called")
    logger.info("Request: %s %s", request.method, request.url)

    try:
        data = request.get_json()
        logger.info("Received data: %s", data)
        
        if not data:
            logger.warning("No data provided in request")
            return jsonify({"error": "No data provided"}), 400

        goals = data.get('goals', '').strip()
        success = data.get('success', '').strip()
        user_name = data.get('user_name', 'Anonymous')
        pdn_code = data.get('pdn_code', '')

        logger.info("Processing 45-day plan for user: %s, PDN code: %s", user_name, pdn_code)

        if not goals or not success:
            logger.warning("Missing goals or success definition")
            return jsonify({"error": "Goals and success definition are required"}), 400

        # Create user context for the 45-day plan
        user_context = f"""
        User Goals: {goals}
        User Success Definition: {success}
        """

        # Generate response using A7Agent
        logger.info("Generating response for PDN code: %s", pdn_code)
        
        if pdn_code == "A7":
            try:
                logger.info("Initializing A7Agent...")
                agentA7 = A7Agent()
                logger.info("A7Agent initialized successfully")
                
                logger.info("Generating response...")
                response = agentA7.get_response_for_45_day_plan(user_context, user_name, pdn_code)
                logger.info("Response generated successfully")
                
            except (AttributeError, ValueError, ImportError) as agent_error:
                logger.error("Error with A7Agent: %s", agent_error)
                response = "I apologize, but I encountered an error while processing your request. Please try again."
            except Exception as timeout_error:
                logger.error("Unexpected error with A7Agent: %s", timeout_error)
                if "timeout" in str(timeout_error).lower() or "timed out" in str(timeout_error).lower():
                    response = (
                        "I apologize, but the request is taking longer than expected. "
                        "This might be due to high server load. Please try again in a few moments."
                    )
                else:
                    response = "I apologize, but I encountered an unexpected error. Please try again."
        else:
            logger.warning("Unknown PDN code: %s, using fallback response", pdn_code)
            response = "I apologize, but I encountered an error while processing your request. Please try again."

        return jsonify({
            "response": response,
            "timestamp": datetime.now().isoformat()
        })

    except (ValueError, KeyError, TypeError) as e:
        logger.error("Error creating 45-day plan: %s", e)
        return jsonify({"error": "Failed to create 45-day plan"}), 500
