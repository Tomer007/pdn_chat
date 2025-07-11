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

# Setup logger
logger = setup_logger()

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


@pdn_chat_ai_bp.route('/upload', methods=['POST'])
def upload_file():
    """Handle file uploads"""
    logger.debug("POST /pdn-chat-ai/upload called")
    logger.info("Request: %s %s", request.method, request.url)
    
    try:
        # Check if file is present
        if 'file' not in request.files:
            return jsonify({"error": "No file provided"}), 400
        
        file = request.files['file']
        if file.filename == '':
            return jsonify({"error": "No file selected"}), 400
        
        # Validate file type
        allowed_extensions = {'png', 'jpg', 'jpeg', 'gif', 'pdf', 'doc', 'docx', 'mp3', 'wav', 'm4a'}
        filename = secure_filename(file.filename)
        file_ext = filename.rsplit('.', 1)[1].lower() if '.' in filename else ''
        
        if file_ext not in allowed_extensions:
            return jsonify({"error": f"File type .{file_ext} not allowed"}), 400
        
        # Check file size (5MB limit)
        file.seek(0, os.SEEK_END)
        file_size = file.tell()
        file.seek(0)
        
        if file_size > 5 * 1024 * 1024:  # 5MB
            return jsonify({"error": "File too large. Maximum size: 5MB"}), 400
        
        # Create upload directory if it doesn't exist
        upload_dir = os.path.join(current_app.root_path, '..', 'static', 'uploads')
        os.makedirs(upload_dir, exist_ok=True)
        
        # Generate unique filename
        unique_filename = f"{uuid.uuid4().hex}_{filename}"
        file_path = os.path.join(upload_dir, unique_filename)
        
        # Save file
        file.save(file_path)
        
        # Return file info
        file_info = {
            "filename": filename,
            "unique_filename": unique_filename,
            "size": file_size,
            "url": f"/static/uploads/{unique_filename}",
            "type": file_ext
        }
        
        logger.info("File uploaded successfully: %s", filename)
        return jsonify(file_info)
        
    except Exception as e:
        logger.error(f"Error uploading file: {e}")
        return jsonify({"error": "File upload failed"}), 500


@pdn_chat_ai_bp.route('/files/<filename>')
def serve_file(filename):
    """Serve uploaded files"""
    try:
        upload_dir = os.path.join(current_app.root_path, '..', 'static', 'uploads')
        return send_from_directory(upload_dir, filename)
    except Exception as e:
        logger.error(f"Error serving file {filename}: {e}")
        return jsonify({"error": "File not found"}), 404


@pdn_chat_ai_bp.route('/upload_audio', methods=['POST'])
def upload_audio():
    """Handle audio file uploads with transcription"""
    logger.debug("POST /pdn-chat-ai/upload_audio called")
    logger.info("Request: %s %s", request.method, request.url)
    
    try:
        # Check if file is present
        if 'file' not in request.files:
            return jsonify({"error": "No audio file provided"}), 400
        
        file = request.files['file']
        if file.filename == '':
            return jsonify({"error": "No audio file selected"}), 400
        
        # Get transcription and user info
        transcription = request.form.get('transcription', '')
        user_name = request.form.get('user_name', 'Anonymous')
        user_id = request.form.get('user_id', '')
        
        # Validate file type (audio files)
        allowed_extensions = {'webm', 'mp3', 'wav', 'm4a', 'ogg'}
        filename = secure_filename(file.filename)
        file_ext = filename.rsplit('.', 1)[1].lower() if '.' in filename else ''
        
        if file_ext not in allowed_extensions:
            return jsonify({"error": f"Audio file type .{file_ext} not allowed"}), 400
        
        # Check file size (10MB limit for audio)
        file.seek(0, os.SEEK_END)
        file_size = file.tell()
        file.seek(0)
        
        if file_size > 10 * 1024 * 1024:  # 10MB
            return jsonify({"error": "Audio file too large. Maximum size: 10MB"}), 400
        
        # Create audio upload directory if it doesn't exist
        audio_upload_dir = os.path.join(current_app.root_path, '..', 'static', 'uploads', 'audio')
        os.makedirs(audio_upload_dir, exist_ok=True)
        
        # Generate unique filename
        unique_filename = f"{uuid.uuid4().hex}_{filename}"
        file_path = os.path.join(audio_upload_dir, unique_filename)
        
        # Save file
        file.save(file_path)
        
        # Store transcription and metadata
        metadata = {
            "filename": filename,
            "unique_filename": unique_filename,
            "size": file_size,
            "url": f"/static/uploads/audio/{unique_filename}",
            "type": file_ext,
            "transcription": transcription,
            "user_name": user_name,
            "user_id": user_id,
            "upload_time": datetime.now().isoformat()
        }
        
        # Save metadata to a JSON file (simple storage, could be replaced with database)
        metadata_file = os.path.join(audio_upload_dir, f"{unique_filename}.json")
        with open(metadata_file, 'w', encoding='utf-8') as f:
            json.dump(metadata, f, ensure_ascii=False, indent=2)
        
        logger.info("Audio file uploaded successfully: %s", filename)
        return jsonify(metadata)
        
    except Exception as e:
        logger.error(f"Error uploading audio file: {e}")
        return jsonify({"error": "Audio upload failed"}), 500


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
        
        # Get user context for personalized responses
        email = session.get('email', 'anonymous')
        user_context = {}
        
        try:
            user_answers = load_answers(email)
            if user_answers:
                pdn_code = calculate_pdn_code(user_answers)
                if pdn_code:
                    report_data = load_pdn_report(pdn_code)
                    if report_data:
                        user_context = {
                            'pdn_code': pdn_code,
                            'report_data': report_data,
                            'user_answers': user_answers
                        }
        except Exception as context_error:
            logger.warning(f"Could not load user context: {context_error}")
        
        # Generate AI response based on context
        response = generate_ai_response(message, user_name, user_context)
        
        logger.info("Response: %s", 200)
        return jsonify(response)

    except Exception as e:
        logger.error(f"Error in chat: {e}")
        return jsonify({"error": "Chat error occurred"}), 500


def generate_ai_response(message, user_name, user_context):
    """Generate AI response based on message and user context"""
    
    # Simple keyword-based responses for now
    # In production, this would integrate with a real AI service
    
    message_lower = message.lower()
    
    # Greeting responses
    if any(word in message_lower for word in ['שלום', 'היי', 'בוקר טוב', 'ערב טוב', 'ברוך הבא']):
        return {
            "message": f"שלום {user_name} 🌿\nברוך הבא לבינת קוד המקור. איך אני יכול/ה לעזור לך היום?",
            "user_context": user_context
        }
    
    # PDN code related responses
    if any(word in message_lower for word in ['קוד', 'pdn', 'קוד המקור', 'הקוד שלי']):
        if user_context.get('pdn_code'):
            pdn_code = user_context['pdn_code']
            return {
                "message": f"הקוד שלך הוא: {pdn_code}\n\nזהו הקוד הייחודי שלך שמתאר את המבנה הפנימי שלך. האם תרצה/י שאסביר יותר על המשמעות שלו?",
                "user_context": user_context
            }
        else:
            return {
                "message": "אני רואה שאתה/ה מתעניין/ת בקוד המקור שלך. כדי שאוכל לעזור לך, אנא השלם/י את השאלון הקצר שלנו.",
                "user_context": user_context
            }
    
    # Spiritual/meditation responses
    if any(word in message_lower for word in ['מדיטציה', 'רוחני', 'פנימי', 'מסע', 'התפתחות']):
        return {
            "message": "המסע הפנימי הוא אחד המסעות החשובים ביותר בחיינו. כל צעד שאתה/ה עושה/ה לכיוון המודעות העצמית הוא משמעותי. מה מעניין אותך/ך במיוחד?",
            "user_context": user_context
        }
    
    # Help responses
    if any(word in message_lower for word in ['עזרה', 'איך', 'מה', 'למה', 'מתי']):
        return {
            "message": "אני כאן כדי לעזור לך להבין את הקוד הפנימי שלך. אתה/ה יכול/ה לשאול אותי על:\n• הקוד שלך ומשמעותו\n• דפוסים פנימיים\n• התפתחות רוחנית\n• כל שאלה אחרת שמעניינת אותך/ך",
            "user_context": user_context
        }
    
    # Default response
    return {
        "message": f"תודה על ההודעה שלך, {user_name} 🙏\n\nאני רואה שאתה/ה מעוניין/ת לדעת יותר. בינת קוד המקור עוזרת לאנשים להבין את המבנה הפנימי שלהם. האם תרצה/י שאסביר יותר על הקוד שלך או על איך זה יכול לעזור לך?",
        "user_context": user_context
    }
