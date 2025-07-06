import json
import logging
import os
from collections import defaultdict

from flask import Blueprint, request, render_template, jsonify, session, current_app
from werkzeug.exceptions import HTTPException

from ..utils.answer_storage import load_answers, save_user_metadata, save_answer
from ..utils.pdn_calculator import calculate_pdn_code
from ..utils.questionnaire import get_question
from ..utils.report_generator import load_pdn_report
from .logger import setup_logger
from ..utils.email_sender import send_pdn_code_email

# Setup logger
logger = setup_logger()

# Create blueprint
pdn_diagnose_bp = Blueprint('pdn_diagnose', __name__, 
                           template_folder='templates',
                           static_folder='static')

# Temporary dictionary to store user answers in memory
user_answers = defaultdict(dict)
api_usage = defaultdict(int)

@pdn_diagnose_bp.route('/')
def home():
    """Home page endpoint - login page"""
    logger.debug("GET /pdn-diagnose/ called")
    api_usage["home"] += 1
    logger.debug(f"API Usage: {dict(api_usage)}")
    logger.info("Request: %s %s", request.method, request.url)
    logger.info("Response: %s", 200)
    logger.info("User answers: %s", user_answers)
    return render_template("diagnose_login.html")

@pdn_diagnose_bp.route('/user_info')
def user_info_page():
    """User information page endpoint"""
    logger.debug("GET /pdn-diagnose/user_info called")
    api_usage["user_info"] += 1
    logger.debug(f"API Usage: {dict(api_usage)}")
    logger.info("Request: %s %s", request.method, request.url)
    logger.info("Response: %s", 200)
    logger.info("User answers: %s", user_answers)
    
    email = session.get("email", "anonymous")
    
    # Load questions.json to get the instructions
    questions = current_app.config.get('PDN_QUESTIONS', {})
    personal_instructions = questions.get("phases", {}).get("PersonalDetails", {}).get("instructions", "")
    
    return render_template("user_form.html", 
                         include_menu=True,
                         email=email,
                         personal_instructions=personal_instructions)

@pdn_diagnose_bp.route('/user_info', methods=['POST'])
def save_user_info_api():
    """Save user information endpoint"""
    logger.debug("POST /pdn-diagnose/user_info called")
    api_usage["save_user_info"] += 1
    logger.debug(f"API Usage: {dict(api_usage)}")
    logger.info("Request: %s %s", request.method, request.url)
    logger.info("Response: %s", 200)
    
    try:
        user_data = request.get_json()
        email = user_data.get('email', 'anonymous')
        save_user_metadata(user_data, email)
        session["user_data"] = user_data
        return jsonify({"message": "User information saved successfully."})
    except Exception as e:
        logger.error(f"Error saving user info: {e}")
        return jsonify({"error": str(e)}), 400

@pdn_diagnose_bp.route('/login', methods=['POST'])
def login_user():
    """User login endpoint"""
    logger.debug("POST /pdn-diagnose/login called")
    api_usage["login"] += 1
    logger.debug(f"API Usage: {dict(api_usage)}")
    logger.info("Request: %s %s", request.method, request.url)
    logger.info("Response: %s", 200)
    
    try:
        login_data = request.get_json()
        if login_data.get('password') == current_app.config.get('ADMIN_PASSWORD', 'pdn'):
            session["email"] = login_data.get('email')
            return jsonify({"message": "Login successful"})
        else:
            return jsonify({"error": "Invalid credentials"}), 401
    except Exception as e:
        logger.error(f"Login error: {e}")
        return jsonify({"error": "Login failed"}), 400

@pdn_diagnose_bp.route('/questionnaire/<int:question_number>')
def get_question_route(question_number):
    """Get specific question by number"""
    logger.debug(f"GET /pdn-diagnose/questionnaire/{question_number} called")
    api_usage[f"get_question_{question_number}"] += 1
    logger.debug(f"API Usage: {dict(api_usage)}")
    logger.info("Request: %s %s", request.method, request.url)
    logger.info("Response: %s", 200)
    
    questions = current_app.config.get('PDN_QUESTIONS', {})
    return get_question(question_number, questions)

@pdn_diagnose_bp.route('/answer', methods=['POST'])
def submit_answer_route():
    """Submit answer for a question"""
    logger.debug("POST /pdn-diagnose/answer called")
    api_usage["submit_answer"] += 1
    logger.debug(f"API Usage: {dict(api_usage)}")
    logger.info("Request: %s %s", request.method, request.url)
    logger.info("Response: %s", 200)
    
    try:
        data = request.get_json()
        logger.info(f"Received answer data: {data}")
        
        question_number = data.get('question_number')
        selected_option_code = data.get('selected_option_code')
        ranking = data.get('ranking')
        email = session.get('email', 'anonymous')
        
        logger.info(f"Processed data - question_number: {question_number}, selected_option_code: {selected_option_code}, ranking: {ranking}, email: {email}")
        
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
        try:
            questions = current_app.config.get('PDN_QUESTIONS', {})
            question_data = get_question(question_number, questions)
            if 'question' in question_data:
                question_text = question_data['question']
                question_options = question_data['options']
        except Exception as e:
            logger.error(f"Could not get question text for question {question_number}: {e}")
        
        # Create answer data dictionary
        answer_data = {
            'selected_option_code': selected_option_code,
            'ranking': ranking,
            'question_options': question_options
        }
        
        # Save answer with question text
        try:
            save_answer(email, question_number, answer_data, question_text)
            logger.info(f"Answer saved successfully for question {question_number}")
        except Exception as save_error:
            logger.error(f"Error saving answer: {save_error}")
            return jsonify({"error": f"Failed to save answer: {str(save_error)}"}), 500
        
        # Store in memory for current session
        user_answers[email][question_number] = answer_data
        
        return jsonify({"message": "Answer saved successfully"})
    except Exception as e:
        logger.error(f"Error submitting answer: {e}")
        return jsonify({"error": str(e)}), 400

@pdn_diagnose_bp.route('/complete_questionnaire', methods=['POST'])
def complete_questionnaire():
    """Complete questionnaire and calculate PDN code"""
    logger.debug("POST /pdn-diagnose/complete_questionnaire called")
    api_usage["complete_questionnaire"] += 1
    logger.debug(f"API Usage: {dict(api_usage)}")
    logger.info("Request: %s %s", request.method, request.url)
    logger.info("Response: %s", 200)
    
    try:
        email = session.get('email', 'anonymous')
        logger.info(f"Completing questionnaire for email: {email}")
        
        user_answers_data = load_answers(email)
        #logger.info(f"Loaded answers data: {user_answers_data}")
        
        if not user_answers_data:
            logger.error(f"No answers found for email: {email}")
            return jsonify({"error": "No answers found"}), 400
        
        # Calculate PDN code
        pdn_code = calculate_pdn_code(user_answers_data)

        logger.info(f"PDN code for {email}: {pdn_code}")

        if not pdn_code:
            logger.error(f"Could not calculate PDN code for user {email}")
            return jsonify({"error": "Could not calculate PDN code - insufficient answers"}), 400
        
        # Update CSV with the calculated PDN code
        try:
            from ..utils.csv_metadata_handler import UserMetadataHandler
            csv_handler = UserMetadataHandler()
            csv_handler.update_pdn_code(email, pdn_code)
            logger.info(f"Successfully updated CSV with PDN code {pdn_code} for {email}")
        except Exception as csv_error:
            logger.warning(f"Failed to update CSV with PDN code: {csv_error}")
            # Don't fail the entire request if CSV update fails
        
        return jsonify({"pdn_code": pdn_code, "message": "Questionnaire completed successfully"})
    except Exception as e:
        logger.error(f"Error completing questionnaire: {e}")
        return jsonify({"error": str(e)}), 400

@pdn_diagnose_bp.route('/pdn_report')
def pdn_report():
    """PDN report page"""
    logger.debug("GET /pdn-diagnose/pdn_report called")
    api_usage["pdn_report"] += 1
    logger.debug(f"API Usage: {dict(api_usage)}")
    logger.info("Request: %s %s", request.method, request.url)
    logger.info("Response: %s", 200)
    
    email = session.get('email', 'anonymous')
    return render_template("pdn_report.html", 
                         include_menu=True,
                         email=email)

@pdn_diagnose_bp.route('/get_report_data', methods=['GET'])
def get_report_data():
    """Get report data for the frontend"""
    try:
        # Get the current user's email from session
        email = session.get('email', 'anonymous')
        logger.info(f"Getting report data for email: {email}")
        
        # Load user answers
        user_answers_data = load_answers(email)
        
        if not user_answers_data:
            logger.error(f"No answers found for email: {email}")
            return jsonify({'error': 'No answers found'}), 400
        
        # Calculate PDN code
        pdn_code = calculate_pdn_code(user_answers_data)
        
        if not pdn_code:
            logger.error(f"Could not calculate PDN code for user {email}")
            return jsonify({'error': 'Could not calculate PDN code'}), 400
        
        # Load report data
        report_data = load_pdn_report(pdn_code)
        
        if not report_data:
            logger.error(f"Could not load PDN report for code {pdn_code}")
            return jsonify({'error': 'Could not load PDN report'}), 400
        
        # Get user metadata
        user_data = session.get('user_data', {})
        
        # Prepare response data
        response_data = {
            'metadata': {
                'first_name': user_data.get('first_name', 'User'),
                'last_name': user_data.get('last_name', ''),
                'email': email
            },
            'results': {
                'pdn_code': pdn_code,
            }
        }
        
        return jsonify(response_data)
    
    except Exception as e:
        logger.error(f"Error getting report data: {str(e)}")
        return jsonify({'error': 'Internal server error'}), 500

@pdn_diagnose_bp.route('/get_user_name')
def get_user_name():
    """Get user name from session"""
    logger.debug("GET /pdn-diagnose/get_user_name called")
    api_usage["get_user_name"] += 1
    logger.debug(f"API Usage: {dict(api_usage)}")
    logger.info("Request: %s %s", request.method, request.url)
    logger.info("Response: %s", 200)
    
    # TODO: Get user name from session or database
    user_data = session.get('user_data', {})
    user_name = user_data.get('first_name', 'User')
    return jsonify({"user_name": user_name})

@pdn_diagnose_bp.route('/send_email', methods=['POST'])
def send_pdn_email():
    """Send PDN report email to user"""
    logger.debug("POST /pdn-diagnose/send_email called")
    api_usage["send_email"] += 1
    logger.debug(f"API Usage: {dict(api_usage)}")
    logger.info("Request: %s %s", request.method, request.url)
    logger.info("Response: %s", 200)
    
    try:
        email = session.get('email', 'anonymous')
        user_answers_data = load_answers(email)
        
        if not user_answers_data:
            return jsonify({"error": "No answers found"}), 400
        
        # Calculate PDN code
        pdn_code = calculate_pdn_code(user_answers_data)
        
        if not pdn_code:
            return jsonify({"error": "Could not calculate PDN code"}), 400
        
        # Load report data
        report_data = load_pdn_report(pdn_code)
        
        if not report_data:
            return jsonify({"error": "Could not load PDN report"}), 400
        
        # Send email
        email_sent = send_pdn_code_email(user_answers_data, "pdn_code")
        
        if email_sent:
            return jsonify({
                "success": True,
                "message": f"Email sent successfully to {email}",
                "pdn_code": pdn_code
            })
        else:
            return jsonify({"error": "Failed to send email"}), 500
            
    except Exception as e:
        logger.error(f"Error sending email: {e}")
        return jsonify({"error": f"Error sending email: {str(e)}"}), 500 