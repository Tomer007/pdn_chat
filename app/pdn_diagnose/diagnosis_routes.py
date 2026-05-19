"""
PDN Diagnose Routes - Flask routes for psychological assessment questionnaire.
Handles user registration, questionnaire management, PDN code calculation, and report generation.
"""

import hmac
import threading
from flask import Blueprint, request, render_template, jsonify, session, current_app
from datetime import datetime

from .logger import setup_logger
from ..utils.answer_storage import load_answers, save_user_metadata, save_answer, delete_answer
from ..utils.auth import require_auth
from ..utils.pdn_calculator import calculate_pdn_code
from ..utils.questionnaire import get_question
from ..utils.email_sender import send_email_via_smtp
from ..pdn_admin.coupon_manager import get_coupon_manager

# Setup logger
logger = setup_logger()

# Admin notification email
ADMIN_EMAIL = 'tomergur@gmail.com'

# Create blueprint
pdn_diagnose_bp = Blueprint('pdn_diagnose', __name__,
                            template_folder='templates',
                            static_folder='static')


def _send_admin_notification(subject: str, body: str):
    """Send a notification email to admin in a background thread (non-blocking)."""
    def _send():
        try:
            from email.mime.multipart import MIMEMultipart
            from email.mime.text import MIMEText
            from ..utils.email_sender import EmailConfig

            msg = MIMEMultipart()
            msg['From'] = EmailConfig.FROM_EMAIL
            msg['To'] = ADMIN_EMAIL
            msg['Subject'] = subject
            msg.attach(MIMEText(body, 'plain', 'utf-8'))
            send_email_via_smtp(msg)
            logger.info("Admin notification sent: %s", subject)
        except Exception as e:
            logger.warning("Failed to send admin notification: %s", e)

    thread = threading.Thread(target=_send, daemon=True)
    thread.start()


# Track active sessions
active_sessions = {}  # session_id -> {email, login_time}


@pdn_diagnose_bp.route('/')
def home():
    """Home page endpoint - login page"""
    logger.debug("GET /pdn-diagnose/ called")
    logger.info("Request: %s %s", request.method, request.url)
    logger.info("Response: %s", 200)
    return render_template("diagnose_login.html")


@pdn_diagnose_bp.route('/user_info')
def user_info_page():
    """User information page endpoint"""
    logger.debug("GET /pdn-diagnose/user_info called")
    logger.info("Request: %s %s", request.method, request.url)
    logger.info("Response: %s", 200)

    email = session.get("email", "anonymous")

    # Load questions.json to get the instructions
    questions = current_app.config.get('QUESTIONS_FILE', {})

    personal_instructions = questions.get("phases", {}).get("PersonalDetails", {}).get("instructions", "")
    logger.info(" /user_info  personal_instructions: %s", personal_instructions)
    coupon_code = session.get('coupon_code', '')
    return render_template("user_form.html",
                           include_menu=True,
                           email=email,
                           personal_instructions=personal_instructions,
                           coupon_code=coupon_code)


@pdn_diagnose_bp.route('/user_info', methods=['POST'])
def save_user_info_api():
    """Save user information endpoint"""
    logger.debug("POST /pdn-diagnose/user_info called")
    logger.info("Request: %s %s", request.method, request.url)
    logger.info("Response: %s", 200)

    try:
        user_data = request.get_json()
        email = user_data.get('email', 'anonymous').lower()
        user_data['email'] = email  # UPDATE the email in user_data
        # Store coupon_code in user record if user logged in with a coupon
        coupon_code = session.get('coupon_code', '')
        if coupon_code:
            user_data['coupon_code'] = coupon_code
        save_user_metadata(user_data, email)
        session["user_data"] = user_data

        # Notify admin about new user registration
        name = f"{user_data.get('first_name', '')} {user_data.get('last_name', '')}".strip()
        _send_admin_notification(
            subject=f"🆕 משתמש חדש נרשם לשאלון: {name}",
            body=(
                f"משתמש חדש נרשם לשאלון PDN\n\n"
                f"שם: {name}\n"
                f"אימייל: {email}\n"
                f"טלפון: {user_data.get('phone', 'לא צוין')}\n"
                f"תאריך: {datetime.now().strftime('%d/%m/%Y %H:%M')}\n"
            ),
        )

        return jsonify({"message": "User information saved successfully."})
    except (ValueError, KeyError, TypeError) as e:
        logger.error("Error saving user info: %s", e)
        return jsonify({"error": str(e)}), 400


@pdn_diagnose_bp.route('/login', methods=['POST'])
def login_user():
    """User login endpoint - supports email/password or coupon code authentication"""
    logger.debug("POST /pdn-diagnose/login called")
    logger.info("Request: %s %s", request.method, request.url)
    logger.info("Response: %s", 200)

    try:
        login_data = request.get_json()
        coupon_code = login_data.get('coupon_code')

        # Coupon-based login path
        if coupon_code:
            email = login_data.get('email', '').lower()
            if not email:
                return jsonify({"error": "Email is required"}), 400

            coupon_manager = get_coupon_manager()
            is_valid, message = coupon_manager.validate_coupon(coupon_code)

            if not is_valid:
                if "usage limit" in message:
                    return jsonify({"error": message}), 403
                return jsonify({"error": message}), 401

            # Redeem the coupon
            coupon_manager.redeem_coupon(coupon_code, email)

            session.permanent = True
            session["email"] = email
            session["coupon_code"] = coupon_code
            # Track active session
            active_sessions[session.sid] = {
                "email": email,
                "login_time": datetime.now()
            }
            return jsonify({"message": "Login successful"})

        # Standard email/password login path
        email = login_data.get('email', '').lower()
        expected_password = email.split('@')[0] if '@' in email else email
        if hmac.compare_digest(login_data.get('password', ''), expected_password):
            session.permanent = True
            session["email"] = email
            session.pop("coupon_code", None)  # Clear any previous coupon login
            # Track active session
            active_sessions[session.sid] = {
                "email": email,
                "login_time": datetime.now()
            }
            return jsonify({"message": "Login successful"})
        else:
            return jsonify({"error": "Invalid credentials"}), 401
    except (ValueError, KeyError, TypeError) as e:
        logger.error("Login error: %s", e)
        return jsonify({"error": "Login failed"}), 400


@pdn_diagnose_bp.route('/questionnaire/<int:question_number>')
def get_question_route(question_number):
    """Get specific question by number"""
    logger.debug("GET /pdn-diagnose/questionnaire/%s called", question_number)
    logger.info("Request: %s %s", request.method, request.url)
    logger.info("Response: %s", 200)

    questions = current_app.config.get('QUESTIONS_FILE', {})

    return get_question(question_number, questions)


@pdn_diagnose_bp.route('/answer', methods=['POST'])
@require_auth
def submit_answer_route():
    """Submit answer for a question"""
    logger.debug("POST /pdn-diagnose/answer called")
    logger.info("Request: %s %s", request.method, request.url)
    logger.info("Response: %s", 200)

    try:
        data = request.get_json()

        question_number = data.get('question_number')
        selected_option_code = data.get('selected_option_code')
        ranking = data.get('ranking')
        email = session.get('email', 'anonymous')

        logger.debug(
            f"Processed data - question_number: {question_number}, selected_option_code: {selected_option_code}, ranking: {ranking}, email: {email}")

        # Validate required fields
        if question_number is None:
            logger.error("Missing question_number in request")
            return jsonify({"error": "Missing question_number"}), 400

        # For ranking questions, ranking should be present
        # For regular questions, selected_option_code should be present
        if ranking is not None:
            # This is a ranking question, selected_option_code can be null
            pass
        elif selected_option_code is None:
            logger.error("Missing selected_option_code for regular question")
            return jsonify({"error": "Missing selected_option_code"}), 400

        # Get question text from questions data
        question_text = None
        question_options = None
        try:
            questions = current_app.config.get('QUESTIONS_FILE', {})
            question_data = get_question(question_number, questions)
            if 'question' in question_data:
                question_text = question_data['question']
                question_options = question_data['options']
        except Exception as e:
            logger.error("Could not get question text for question %s: %s", question_number, e)

        # Create answer data dictionary
        answer_data = {
            'selected_option_code': selected_option_code,
            'ranking': ranking,
            'question_options': question_options
        }

        # Save answer with question text
        try:
            logger.info("Saving answer for user %s, question %s", email, question_number)
            save_answer(email, question_number, answer_data, question_text)
            logger.info("Answer saved successfully for user %s, question %s", email, question_number)
        except Exception as save_error:
            logger.error("Error saving answer for user %s, question %s: %s", email, question_number, save_error, exc_info=True)
            return jsonify({"error": f"Failed to save answer: {str(save_error)}"}), 500

        return jsonify({"message": "Answer saved successfully", "question_number": question_number})
    except (ValueError, KeyError, FileNotFoundError) as e:
        logger.error("Error submitting answer: %s", e, exc_info=True)
        return jsonify({"error": str(e)}), 400
    except Exception as e:
        logger.error("Unexpected error submitting answer: %s", e, exc_info=True)
        return jsonify({"error": "An unexpected error occurred"}), 500


@pdn_diagnose_bp.route('/delete_answer', methods=['POST'])
@require_auth
def delete_answer_route():
    """Delete a previously saved answer (used when user goes back)"""
    try:
        data = request.get_json()
        question_number = data.get('question_number')
        email = session.get('email', 'anonymous')

        if question_number is None:
            return jsonify({"error": "Missing question_number"}), 400

        deleted = delete_answer(email, int(question_number))
        return jsonify({"success": deleted, "question_number": question_number})
    except Exception as e:
        logger.error("Error deleting answer: %s", e)
        return jsonify({"error": str(e)}), 400


@pdn_diagnose_bp.route('/get_progress', methods=['GET'])
@require_auth
def get_progress():
    """Return saved progress for resume functionality"""
    email = session.get('email', 'anonymous')
    answers = load_answers(email)
    if not answers:
        return jsonify({"current_question": 0})
    digit_keys = [int(k) for k in answers.keys() if k.isdigit()]
    if not digit_keys:
        return jsonify({"current_question": 0})
    max_question = max(digit_keys)
    return jsonify({"current_question": max_question})


@pdn_diagnose_bp.route('/complete_questionnaire', methods=['POST'])
@require_auth
def complete_questionnaire():
    """Complete questionnaire and calculate PDN code"""
    logger.debug("POST /pdn-diagnose/complete_questionnaire called")
    logger.info("Request: %s %s", request.method, request.url)
    logger.info("Response: %s", 200)

    try:
        email = session.get('email', 'anonymous')
        logger.info("Completing questionnaire for email: %s", email)

        user_answers_data = load_answers(email)
        # logger.info(f"Loaded answers data: {user_answers_data}")

        if not user_answers_data:
            logger.error("No answers found for email: %s", email)
            return jsonify({"error": "No answers found"}), 400

        # Calculate PDN code
        pdn_code = calculate_pdn_code(user_answers_data)

        logger.info("PDN code for %s: %s", email, pdn_code)

        if not pdn_code:
            logger.error("Could not calculate PDN code for user %s", email)
            return jsonify({"error": "Could not calculate PDN code - insufficient answers"}), 400

        # Update CSV with the calculated PDN code
        try:
            from ..utils.csv_metadata_handler import UserMetadataHandler
            csv_handler = UserMetadataHandler()
            csv_handler.update_pdn_code(email, pdn_code)
            logger.info("Successfully updated CSV with PDN code %s for %s", pdn_code, email)
        except Exception as csv_error:
            logger.warning("Failed to update CSV with PDN code: %s", csv_error)
            # Don't fail the entire request if CSV update fails

        # Notify admin about completed questionnaire
        _send_admin_notification(
            subject=f"✅ שאלון הושלם: {email} → קוד {pdn_code}",
            body=(
                f"משתמש סיים את השאלון PDN\n\n"
                f"אימייל: {email}\n"
                f"קוד PDN: {pdn_code}\n"
                f"תאריך: {datetime.now().strftime('%d/%m/%Y %H:%M')}\n"
            ),
        )

        return jsonify({"pdn_code": pdn_code, "message": "Questionnaire completed successfully"})
    except (ValueError, KeyError, FileNotFoundError) as e:
        logger.error("Error completing questionnaire: %s", e)
        return jsonify({"error": str(e)}), 400


@pdn_diagnose_bp.route('/pdn_report')
def pdn_report():
    """PDN report page"""
    logger.debug("GET /pdn-diagnose/pdn_report called")
    logger.info("Request: %s %s", request.method, request.url)
    logger.info("Response: %s", 200)

    email = session.get('email', 'anonymous')
    return render_template("pdn_report.html",
                           include_menu=True,
                           email=email)


@pdn_diagnose_bp.route('/get_report_data', methods=['GET'])
@require_auth
def get_report_data():
    """Get report data for the frontend"""
    try:
        # Get the current user's email from session
        email = session.get('email', 'anonymous')
        logger.info("Getting report data for email: %s", email)

        # Load user answers
        user_answers_data = load_answers(email)

        if not user_answers_data:
            logger.error("No answers found for email: %s", email)
            return jsonify({'error': 'No answers found'}), 400
        
        # Calculate PDN code
        pdn_code = calculate_pdn_code(user_answers_data)

        # Get user metadata
        user_data = session.get('user_data', {})

        # Prepare response data
        response_data = {
            'metadata': {
                'first_name': user_data.get('first_name', 'User'),
                'last_name': user_data.get('last_name', ''),
                'email': email
            },
            'pdn_code': pdn_code or 'N/A'
        }

        return jsonify(response_data)

    except (ValueError, KeyError, FileNotFoundError) as e:
        logger.error("Error getting report data: %s", str(e))
        return jsonify({'error': 'Internal server error'}), 500


@pdn_diagnose_bp.route('/chat')
def chat():
    """Chat page for diagnose questionnaire"""
    logger.debug("GET /pdn-diagnose/chat called")
    logger.info("Request: %s %s", request.method, request.url)
    logger.info("Response: %s", 200)

    email = session.get('email', 'anonymous')
    user_data = session.get('user_data', {})
    user_name = user_data.get('first_name', 'User')
    user_id = email  # Using email as user ID

    return render_template("questionnaire.html",
                           include_menu=True,
                           user_name=user_name,
                           user_id=user_id,
                           email=email)
