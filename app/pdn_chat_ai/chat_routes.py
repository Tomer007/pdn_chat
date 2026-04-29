"""
PDN Chat AI Routes - Flask routes for AI-powered chat interface.
Handles user authentication, chat messaging, and 21-day plan generation.
"""

import uuid
from datetime import datetime
from functools import wraps

from flask import Blueprint, request, render_template, jsonify, session

from .binat_agents.pdn_agent import PDNAgent
from .logger import setup_logger
from ..utils.conversation_stats import conversation_stats

logger = setup_logger()
_pdn_agent = None

# Track active chat sessions
chat_sessions = {}  # session_id -> {email, user_id, login_time}

USERS_DATA = {
    'tomergur@gmail.com': {'password': 'pdn', 'pdn_code': 'e5', 'name': 'תומר', 'daily_conversation_limit': 100},
    'pdncode@gmail.com': {'password': 'pdn', 'pdn_code': 'a7', 'name': 'פנינה', 'daily_conversation_limit': 10},
    'anna123benyehuda@gmail.com': {'password': 'pdn', 'pdn_code': 'a3', 'name': 'אנה', 'daily_conversation_limit': 100},
    'yaelrapoport2@gmail.com': {'password': 'pdn', 'pdn_code': 'a3', 'name': 'יעל', 'daily_conversation_limit': 100},
    'einavmakover@gmail.com': {'password': 'pdn', 'pdn_code': 'e9', 'name': 'עינב', 'daily_conversation_limit': 100}
}

def get_agent_instance():
    """Get or create the single PDN agent instance"""
    global _pdn_agent
    if _pdn_agent is None:
        _pdn_agent = PDNAgent()
        logger.info("Created new PDNAgent instance")
    return _pdn_agent

def handle_errors(f):
    """Decorator for consistent error handling"""
    @wraps(f)
    def wrapper(*args, **kwargs):
        try:
            return f(*args, **kwargs)
        except Exception as e:
            logger.error("Error in %s: %s", f.__name__, e)
            return jsonify({"error": f"{f.__name__.replace('_', ' ').title()} error occurred"}), 500
    return wrapper

pdn_chat_ai_bp = Blueprint('pdn_chat_ai', __name__, template_folder='templates', static_folder='../static')

@pdn_chat_ai_bp.route('/')
def chat():
    """Binat Chat AI login endpoint"""
    return render_template("binat_login.html")

@pdn_chat_ai_bp.route('/login', methods=['POST'])
@handle_errors
def login():
    """Handle user login with email and password verification"""
    data = request.get_json()
    if not data:
        return jsonify({"error": "No data provided"}), 400

    email = data.get('email', '').strip()
    password = data.get('password', '').strip()

    if not email or not password:
        return jsonify({"error": "Email and password are required"}), 400

    user_data = USERS_DATA.get(email)
    if user_data and user_data['password'] == password:
        user_id = str(uuid.uuid4())
        # Get daily_conversation_limit with default value of 15
        daily_conversation_limit = user_data.get('daily_conversation_limit', 15)
        session.update({
            'user_id': user_id,
            'user_email': email,
            'user_name': user_data['name'],
            'pdn_code': user_data['pdn_code'],
            'daily_conversation_limit': daily_conversation_limit
        })
        # Track active session
        chat_sessions[session.sid] = {
            "email": email,
            "user_id": user_id,
            "login_time": datetime.now()
        }
        logger.info("User %s logged in successfully", email)
        return jsonify({
            "success": True,
            "message": "Login successful",
            "user_id": user_id,
            "user_name": user_data['name'],
            "pdn_code": user_data['pdn_code'],
            "daily_conversation_limit": daily_conversation_limit
        })

    logger.warning("Failed login attempt for email: %s", email)
    return jsonify({"success": False, "error": "Invalid email or password"}), 401

@pdn_chat_ai_bp.route('/logout', methods=['POST'])
@handle_errors
def logout():
    """Handle user logout"""
    user_email = session.get('user_email')
    
    # Remove from active sessions
    chat_sessions.pop(session.sid, None)
    
    session.clear()
    logger.info("User %s logged out successfully (history preserved)", user_email)
    return jsonify({"success": True, "message": "Logout successful"})

@pdn_chat_ai_bp.route('/binat')
def chat_interface():
    """Chat interface endpoint - accessed after login"""
    return render_template(
        "chat.html",
        welcome_message="ברוך הבא לבינת קוד המקור ",
        user_name=session.get('user_name') or request.args.get('user_name', 'Anonymous'),
        user_id=session.get('user_id') or request.args.get('user_id', ''),
        pdn_code=session.get('pdn_code') or request.args.get('pdn_code', ''),
        daily_conversation_limit=session.get('daily_conversation_limit', 15),
        include_menu=True
    )

@pdn_chat_ai_bp.route('/chat', methods=['POST'])
@handle_errors
def chat_with_binat():
    """Handle chat messages with improved AI responses"""
    data = request.get_json()
    if not data:
        return jsonify({"error": "No data provided"}), 400

    # Track conversation
    user_email = session.get('user_email')
    if user_email:
        conversation_stats.increment_conversation(user_email)

    # Get daily_conversation_limit from session or use default
    daily_conversation_limit = session.get('daily_conversation_limit', 15)

    agent = get_agent_instance()
    return jsonify({
        "response": agent.chat_with_binat(
            data.get('message', '').strip(),
            data.get('user_name', 'Anonymous'),
            data.get('pdn_code', ''),
            daily_conversation_limit=daily_conversation_limit
        ),
        "timestamp": datetime.now().isoformat()
    })

@pdn_chat_ai_bp.route('/21-day-plan', methods=['POST'])
@handle_errors
def build_21_transformation_plan():
    """Handle 21-day transformation plan requests"""
    data = request.get_json()
    goal = data.get('goal', '').strip()
    user_name = data.get('user_name', '')
    pdn_code = data.get('pdn_code', '')

    if not goal:
        return jsonify({"error": "Goal is required"}), 400

    # Get daily_conversation_limit from session or use default
    daily_conversation_limit = session.get('daily_conversation_limit', 15)

    agent = get_agent_instance()

    return jsonify({
        "response": agent.build_21_transformation_plan(goal, user_name, pdn_code, daily_conversation_limit),
        "timestamp": datetime.now().isoformat()
    })

@pdn_chat_ai_bp.route('/daily-training', methods=['POST'])
@handle_errors
def daily_training():
    """Handle daily training requests"""
    data = request.get_json()
    task = data.get('task', '').strip()
    user_name = data.get('user_name', 'Anonymous')
    pdn_code = data.get('pdn_code', '')

    if not task:
        return jsonify({"error": "Task is required"}), 400

    # Get daily_conversation_limit from session or use default
    daily_conversation_limit = session.get('daily_conversation_limit', 15)

    agent = get_agent_instance()

    return jsonify({
        "response": agent.daily_training(
            user_name,
            pdn_code,
            task,
            daily_conversation_limit
        ),
        "timestamp": datetime.now().isoformat()
    })
