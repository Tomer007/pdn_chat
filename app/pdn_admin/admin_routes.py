import csv
import logging
import os
import secrets
from datetime import datetime, timedelta

from flask import Blueprint, request, render_template, jsonify, current_app, send_file, abort
from pathlib import Path

from ..utils.answer_storage import load_answers
from ..utils.csv_metadata_handler import UserMetadataHandler
from ..utils.email_sender import send_pdn_code_email
from ..utils.pdn_calculator import calculate_pdn_code
from ..utils.pdn_file_path import PDNFilePath


# Configure logging
logger = logging.getLogger(__name__)

# Add expiration tracking
SESSION_TIMEOUT = timedelta(hours=2)



# Create blueprint
pdn_admin_bp = Blueprint('pdn_admin', __name__,
                         template_folder='templates',
                         static_folder='../static')

# Admin sessions storage (in production, use Redis or database)
admin_sessions = {}  # session_token -> user_info

def create_session(email):
    # Remove any existing sessions for this email
    for token, session in list(admin_sessions.items()):
        if session.get("email") == email:
            del admin_sessions[token]
            logger.info(f"Removed old session for {email}")

    token = secrets.token_urlsafe(32)
    now = datetime.now()
    admin_sessions[token] = {
        "email": email,
        "username": email,
        "login_time": now,
        "expires_at": now + SESSION_TIMEOUT
    }
    logger.info(f"Created new session for {email}: {token}")
    return token


def verify_session(session_token: str):

    if not session_token or session_token not in admin_sessions:
        abort(401, description="Invalid or expired session")

    session = admin_sessions[session_token]
    if datetime.now() > session["expires_at"]:
        del admin_sessions[session_token]
        abort(401, description="Session expired")

    return session  # Return session info to avoid redundant lookups

# Clean up expired sessions periodically
def cleanup_expired_sessions():
    now = datetime.now()
    expired = [token for token, session in admin_sessions.items()
               if now > session["expires_at"]]
    for token in expired:
        del admin_sessions[token]

def load_user_metadata():
    """
    Load user metadata from the CSV file and JSON files.
    
    Returns:
        List of dictionaries containing user metadata
    """
    try:
        csv_file_path = Path(os.getenv('SAVED_RESULTS_DIR', 'saved_results')) / 'user_metadata.csv'
        logger.info("CSV file path: %s", csv_file_path)
        if not csv_file_path.exists():
            logger.warning("user_metadata.csv file not found")
            return []

        metadata_list = []
        csv_metadata_handler = UserMetadataHandler()

        with open(csv_file_path, 'r', encoding='utf-8') as csvfile:
            reader = csv.DictReader(csvfile)
            for row in reader:
                # Skip empty rows
                if not row.get("Email", "").strip():
                    continue

                email = row.get("Email", "").strip()

                # Load additional metadata from JSON file
                json_metadata = {}
                try:
                    questionnaire_data = csv_metadata_handler.get_user_files(email, "answers")
                    if questionnaire_data and 'metadata' in questionnaire_data:
                        json_metadata = questionnaire_data['metadata']
                except Exception as e:
                    logger.warning("Could not load JSON metadata for %s: %s", email, e)

                # Convert CSV column names to the expected format and merge with JSON metadata
                user_data = {
                    "user_id": (row.get("User ID") or "").strip(),
                    "email": email,
                    "date": (row.get("Date") or "").strip(),
                    "pdn_code": (row.get("PDN Code") or "").strip(),
                    "pdn_voice_code": (row.get("PDN Voice Code") or "").strip(),
                    "diagnose_pdn_code": (row.get("Diagnose PDN Code") or "").strip(),
                    "diagnose_comments": (row.get("Diagnose Comments") or "").strip(),
                    "pdn_update_comments": (row.get("PDN Update Comments") or "").strip(),
                    # Load from JSON metadata if available, otherwise use CSV or defaults
                    "first_name": (json_metadata.get("first_name") or row.get("First Name") or "").strip(),
                    "last_name": (json_metadata.get("last_name") or row.get("Last Name") or "").strip(),
                    "phone": (json_metadata.get("phone") or row.get("Phone") or "").strip(),
                    "native_language": (
                                json_metadata.get("native_language") or json_metadata.get("mother_language") or row.get(
                            "Native Language") or "").strip(),
                    "gender": (json_metadata.get("gender") or row.get("Gender") or "").strip(),
                    "education_level": (
                                json_metadata.get("education_level") or json_metadata.get("education") or row.get(
                            "Education Level") or "").strip(),
                    "job_title": (json_metadata.get("job_title") or row.get("Job Title") or "").strip(),
                    "birth_year": (json_metadata.get("birth_year") or row.get("Birth Year") or "").strip(),
                    "link_to_user": f"/user/{email}",
                    "questionnaire": f"/api/user/questionnaire/{email}",
                    "voice": f"/api/user/voice/{email}"
                }
                metadata_list.append(user_data)

        logger.info("Loaded %d user records from CSV and JSON", len(metadata_list))
        return metadata_list

    except Exception as e:
        logger.error("Error loading user metadata from CSV: %s", e)
        return []

def get_user_metadata():
    """
    Get user metadata, loading from CSV if needed.
    
    Returns:
        List of dictionaries containing user metadata
    """
    return load_user_metadata()

def get_session_user_info(session_token: str):

    if not session_token:
        logger.warning("No session token provided for user info")
        abort(401, description="No session token provided")

    """Get user info from session token"""
    if session_token in admin_sessions:
        return admin_sessions[session_token]

    logger.warning("Invalid session token: %s, active sessions: %s", session_token, list(admin_sessions.keys()))
    abort(401, description="Invalid session")


@pdn_admin_bp.route('/')
def admin_login_page():
    """Admin login page"""
    logger.debug("GET /pdn-admin/ called")
    logger.debug("Request: %s %s", request.method, request.url)
    return render_template("admin_login.html")


@pdn_admin_bp.route('/dashboard')
def admin_dashboard_page():
    """Admin dashboard page"""
    logger.debug("GET /pdn-admin/dashboard called")
    logger.debug("Request: %s %s", request.method, request.url)
    return render_template("admin_dashboard.html")


@pdn_admin_bp.route('/login', methods=['POST'])
def admin_login():
    """Admin login endpoint"""
    logger.debug("POST /pdn-admin/login called")
    logger.debug("Request: %s %s", request.method, request.url)

    try:
        login_data = request.get_json()
        email = login_data.get('email', '')
        password = login_data.get('password', '')

        if password.lower() == current_app.config.get('ADMIN_PASSWORD', 'pdn').lower():
            session_token = create_session(email)
            return jsonify({
                "success": True,
                "message": "Login successful",
                "session_token": session_token
            })

        # Log failed login attempt
        logger.warning("Failed login attempt with password: %s", password)

        return jsonify({"error": "Invalid credentials"}), 401

    except Exception as e:
        logger.error("Login error: %s", e)
        return jsonify({"error": "Login failed"}), 400


@pdn_admin_bp.route('/logout')
def admin_logout():
    """Admin logout endpoint"""
    logger.debug("GET /pdn-admin/logout called")
    logger.debug("Request: %s %s", request.method, request.url)

    cleanup_expired_sessions()
    
    session_token = request.args.get('session_token')
    if session_token and session_token in admin_sessions:
        del admin_sessions[session_token]
    return jsonify({"success": True, "message": "Logout successful"})


@pdn_admin_bp.route('/metadata/csv')
def get_metadata_csv():
    """Get metadata as CSV download"""
    logger.debug("GET /pdn-admin/metadata/csv called")
    logger.debug("Request: %s %s", request.method, request.url)

    session_token = request.args.get('session_token')

    verify_session(session_token)

    metadata = get_user_metadata()

    return jsonify({"data": metadata})


@pdn_admin_bp.route('/download/csv')
def download_csv_file():
    """Download the actual CSV file"""
    logger.debug("GET /pdn-admin/download/csv called")
    logger.debug("Request: %s %s", request.method, request.url)

    session_token = request.args.get('session_token')
    verify_session(session_token)

    try:
        csv_file_path = Path("saved_results/user_metadata.csv")
        if not csv_file_path.exists():
            logger.error("CSV file not found: %s", csv_file_path)
            return jsonify({"error": "CSV file not found"}), 404
    except Exception as e:
        logger.error("Error downloading CSV file: %s", e)
        return jsonify({"error": "Failed to download CSV file"}), 500


def remove_none_keys(obj):
    """Recursively remove None keys from dicts/lists."""
    if isinstance(obj, dict):
        return {k: remove_none_keys(v) for k, v in obj.items() if k is not None}
    elif isinstance(obj, list):
        return [remove_none_keys(item) for item in obj]
    else:
        return obj


@pdn_admin_bp.route('/user/questionnaire/<email>')
def get_user_questionnaire(email):
    """Get user questionnaire data"""
    logger.debug("GET /pdn-admin/user/questionnaire/%s called", email)
    logger.debug("Request: %s %s", request.method, request.url)

    session_token = request.args.get('session_token')
    #verify_session(session_token)

    try:
        # Find user in data
        csv_metadata_handler = UserMetadataHandler()
        logger.info("Loading questionnaire data for %s", email)

        questionnaire_data = csv_metadata_handler.get_user_files(email, "answers")
        logger.info("Questionnaire data loaded: %s", questionnaire_data is not None)

        if not questionnaire_data:
            logger.warning("No questionnaire data found for user: %s", email)
            return jsonify({"error": "User questionnaire not found"}), 404

        # Get user metadata from CSV (including User ID)
        logger.info("Loading CSV metadata for %s", email)
        user_metadata = csv_metadata_handler.get_user_by_email(email)
        logger.info("CSV metadata loaded: %s", user_metadata is not None)

        if user_metadata:
            # Merge CSV metadata with existing JSON metadata
            if 'metadata' in questionnaire_data:
                # Preserve JSON metadata and add CSV metadata
                questionnaire_data['metadata'].update(user_metadata)
            else:
                questionnaire_data['metadata'] = user_metadata
            logger.info(
                f"Successfully loaded questionnaire data for {email} with User ID: {user_metadata.get('User ID', 'N/A')}")
        else:
            logger.warning(f"No CSV metadata found for user: {email}")
            # Create a minimal metadata structure
            if 'metadata' not in questionnaire_data:
                questionnaire_data['metadata'] = {
                    'email': email,
                    'User ID': 'N/A'
                }

        logger.info(f"Returning questionnaire data with {len(questionnaire_data)} keys")
        # Clean None keys before returning
        clean_data = remove_none_keys(questionnaire_data)
        return jsonify(clean_data)

    except Exception as e:
        logger.error(f"Error loading questionnaire for {email}: {e}")
        import traceback
        logger.error(f"Full traceback: {traceback.format_exc()}")
        return jsonify({"error": f"Failed to load questionnaire: {str(e)}"}), 500


@pdn_admin_bp.route('/user/voice/<email>')
def get_user_voice(email):
    """Get user voice recording URL"""
    logger.debug(f"GET /pdn-admin/user/voice/{email} called")
    logger.debug("Request: %s %s", request.method, request.url)

    session_token = request.args.get('session_token')
    #verify_session(session_token)

    try:
        # Find user in data
        pdn_file_path = PDNFilePath()
        question1_filename = pdn_file_path.find_user_file(email, "question1.wav")
        question2_filename = pdn_file_path.find_user_file(email, "question2.wav")

        voice_recordings = {}

        if question1_filename is not None and question1_filename.exists():
            # Double-check that the file actually exists and is readable
            try:
                if question1_filename.is_file() and question1_filename.stat().st_size > 0:
                    voice_recordings['question1'] = {
                        'filename': str(question1_filename),
                        'path': str(question1_filename),
                        'exists': True
                    }
            except (OSError, IOError) as e:
                logger.warning(f"Error accessing question1 file {question1_filename}: {e}")

        if question2_filename is not None and question2_filename.exists():
            # Double-check that the file actually exists and is readable
            try:
                if question2_filename.is_file() and question2_filename.stat().st_size > 0:
                    voice_recordings['question2'] = {
                        'filename': str(question2_filename),
                        'path': str(question2_filename),
                        'exists': True
                    }
            except (OSError, IOError) as e:
                logger.warning(f"Error accessing question2 file {question2_filename}: {e}")

        # If no new format recordings found, try old format for backward compatibility
        if not voice_recordings:
            user_audio_path = pdn_file_path.find_user_file(email, ".wav")
            if user_audio_path is not None and user_audio_path.exists():
                # Double-check that the file actually exists and is readable
                try:
                    if user_audio_path.is_file() and user_audio_path.stat().st_size > 0:
                        voice_recordings['legacy'] = {
                            'filename': str(user_audio_path),
                            'path': str(user_audio_path),
                            'exists': True
                        }
                except (OSError, IOError) as e:
                    logger.warning(f"Error accessing legacy audio file {user_audio_path}: {e}")

        if not voice_recordings:
            return jsonify({"error": "User voice recording not found"}), 404

        # Return voice file info
        return jsonify({
            "email": email,
            "voice_recordings": voice_recordings,
            "has_recordings": True
        })
    except Exception as e:
        logger.error(f"Error finding user metadata: {e}")
        return jsonify({"error": "User not found"}), 404


@pdn_admin_bp.route('/user/diagnose/<email>', methods=['PUT'])
def update_user_diagnose(email):
    """Update user diagnose information"""
    logger.debug(f"PUT /pdn-admin/user/diagnose/{email} called")
    logger.debug("Request: %s %s", request.method, request.url)

    session_token = request.args.get('session_token')
    #verify_session(session_token)

    try:
        diagnose_data = request.get_json()

        # Find and update user in data
        user_data = next((user for user in get_user_metadata() if user["email"] == email), None)
        if not user_data:
            return jsonify({"error": "User not found"}), 404

        # Update diagnose fields with safe defaults
        diagnose_pdn_code = ""
        diagnose_comments = ""

        if "diagnose_pdn_code" in diagnose_data:
            diagnose_pdn_code = diagnose_data["diagnose_pdn_code"]
            user_data["diagnose_pdn_code"] = diagnose_pdn_code
        elif "diagnose_pdn_code" not in user_data:
            diagnose_pdn_code = user_data.get("pdn_code", "")
            user_data["diagnose_pdn_code"] = diagnose_pdn_code

        if "diagnose_comments" in diagnose_data:
            diagnose_comments = diagnose_data["diagnose_comments"]
            user_data["diagnose_comments"] = diagnose_comments
        elif "diagnose_comments" not in user_data:
            user_data["diagnose_comments"] = ""

        # Update CSV with the new diagnosis information
        try:
            csv_handler = UserMetadataHandler()
            csv_handler.update_diagnose_code(email, diagnose_pdn_code, diagnose_comments)
            logger.info(f"Successfully updated CSV with diagnose info for {email}")
        except Exception as csv_error:
            logger.warning(f"Failed to update CSV with diagnose info: {csv_error}")
            # Don't fail the entire request if CSV update fails

        return jsonify({
            "success": True,
            "message": "Diagnose updated successfully",
            "user": user_data
        })
    except Exception as e:
        logger.error(f"Error updating diagnose: {e}")
        return jsonify({"error": "Failed to update diagnose"}), 400


@pdn_admin_bp.route('/user/send_email/<email>', methods=['POST'])
def send_user_email(email):
    """Send PDN report email to user"""
    logger.debug(f"POST /pdn-admin/user/send_email/{email} called")
    logger.debug("Request: %s %s", request.method, request.url)

    session_token = request.args.get('session_token')
    #verify_session(session_token)

    try:
        # Load user answers
        user_answers = load_answers(email)
        if not user_answers:
            return jsonify({"error": "User answers not found"}), 404

        # Calculate PDN code
        calculation_result = calculate_pdn_code(user_answers)
        
        if isinstance(calculation_result, dict):
            pdn_code = calculation_result['pdn_code']
            needs_verification = calculation_result.get('needs_verification', False)
        else:
            pdn_code = calculation_result
            needs_verification = False

        logger.info(f"send_email PDN code: {pdn_code} for user {email}, needs_verification: {needs_verification}")

        if not pdn_code:
            return jsonify({"error": "Could not calculate PDN code"}), 400

        # Send email
        email_sent = send_pdn_code_email(user_answers, pdn_code)

        if email_sent:
            return jsonify({
                "success": True,
                "message": f"Email sent successfully to {email}",
                "pdn_code": pdn_code,
                "needs_verification": needs_verification
            })
        else:
            return jsonify({"error": "Failed to send email"}), 500

    except Exception as e:
        logger.error(f"Error sending email: {e}")
        return jsonify({"error": f"Error sending email: {str(e)}"}), 500


@pdn_admin_bp.route('/user/recalculate_pdn/<email>', methods=['POST'])
def recalculate_user_pdn(email):
    """Recalculate PDN code for a user"""
    logger.debug(f"POST /pdn-admin/user/recalculate_pdn/{email} called")
    logger.debug("Request: %s %s", request.method, request.url)

    session_token = request.args.get('session_token')
    #verify_session(session_token)

    try:
        # Load user answers
        user_answers = load_answers(email)
        if not user_answers:
            return jsonify({"error": "User answers not found"}), 404

        # Calculate PDN code using the calculate_pdn_code function with details
        calculation_result = calculate_pdn_code(user_answers, return_details=True)
        
        if isinstance(calculation_result, dict):
            pdn_code = calculation_result['pdn_code']
            calculation_details = calculation_result['calculation_details']
            needs_verification = calculation_result.get('needs_verification', False)
        else:
            pdn_code = calculation_result
            calculation_details = None
            needs_verification = False

        logger.info(f"recalculate_pdn PDN code: {pdn_code} for user {email}, needs_verification: {needs_verification}")

        if not pdn_code:
            return jsonify({"error": "Could not calculate PDN code"}), 400

        # Update CSV with the new PDN code and current date
        try:
            csv_handler = UserMetadataHandler()

            # Get user info from session
            user_info = get_session_user_info(session_token)
            updated_by = user_info.get("username", "Admin") if user_info else "Admin"

            # Update PDN code with comment
            pdn_updated = csv_handler.update_pdn_code_with_comment(email, pdn_code, updated_by)

            # Update date to current date
            current_date = datetime.now().strftime("%d/%m/%Y")
            date_updated = csv_handler._update_user_field(email, "Date", current_date)

            if pdn_updated and date_updated:
                logger.info(
                    f"Successfully updated CSV with PDN code {pdn_code} and date {current_date} for {email} by {updated_by}")

                # Get the updated comment from CSV
                user_data = csv_handler.get_user_by_email(email)
                pdn_update_comments = user_data.get("PDN Update Comments", "") if user_data else ""

                response_data = {
                    "success": True,
                    "message": f"PDN code recalculated successfully for {email}",
                    "pdn_code": pdn_code,
                    "date": current_date,
                    "updated_by": updated_by,
                    "pdn_update_comments": pdn_update_comments,
                    "needs_verification": needs_verification
                }
                
                # Add calculation details if available
                if calculation_details:
                    response_data["calculation_details"] = calculation_details
                
                return jsonify(response_data)
            else:
                logger.error(f"Failed to update CSV for {email}")
                return jsonify({"error": "Failed to update CSV with new PDN code"}), 500

        except Exception as csv_error:
            logger.error(f"Failed to update CSV with PDN code: {csv_error}")
            return jsonify({"error": f"Failed to update CSV: {str(csv_error)}"}), 500

    except Exception as e:
        logger.error(f"Error recalculating PDN code: {e}")
        return jsonify({"error": f"Error recalculating PDN code: {str(e)}"}), 500


@pdn_admin_bp.route('/audio/<path:file_path>')
def serve_audio(file_path):
    """Serve audio files with authentication."""
    logger.debug(f"GET /pdn-admin/audio/{file_path} called")
    logger.debug("Request: %s %s", request.method, request.url)

    # Extract session token from query parameters
    session_token = request.args.get('session_token')
    logger.debug(f"Session token: {session_token}")

    if not session_token:
        logger.warning("No session token provided")
        abort(401, description="No session token provided")

    # Verify session
    #verify_session(session_token)

    # Use the environment variable for saved_results directory
    saved_results_dir = os.getenv('SAVED_RESULTS_DIR', 'saved_results')

    # Handle the file path correctly
    # If the file_path already starts with the saved_results directory structure, use it as is
    if file_path.startswith('pdn/saved_results/'):
        # Remove the 'pdn/saved_results/' prefix and use the environment variable
        relative_path = file_path.replace('pdn/saved_results/', '')
        audio_path = Path(saved_results_dir) / relative_path
    elif file_path.startswith('saved_results/'):
        # Remove the 'saved_results/' prefix
        relative_path = file_path.replace('saved_results/', '')
        audio_path = Path(saved_results_dir) / relative_path
    else:
        # Use the file_path as is
        audio_path = Path(saved_results_dir) / file_path

    logger.debug(f"Looking for file at: {audio_path.absolute()}")

    # Security check: ensure the path is within the allowed directory
    try:
        audio_path = audio_path.resolve()
        saved_results_path = Path(saved_results_dir).resolve()
        if not str(audio_path).startswith(str(saved_results_path)):
            logger.warning("Path traversal attempt detected")
            abort(403, description="Access denied")
    except Exception as e:
        logger.error(f"Path resolution error: {e}")
        abort(400, description="Invalid file path")

    # Check if file exists
    if not audio_path.exists():
        logger.warning(f"File not found: {audio_path}")
        abort(404, description="Audio file not found")

    logger.debug(f"File found, serving: {audio_path}")

    try:
        return send_file(
            audio_path,
            mimetype='audio/wav',
            as_attachment=False,
            download_name=audio_path.name
        )
    except Exception as e:
        logger.error(f"Error serving audio file: {e}")
        abort(500, description="Error serving audio file")


@pdn_admin_bp.route('/api/save-audio', methods=['POST'])
def save_audio():
    """Save uploaded audio file."""
    logger.debug("POST /pdn-admin/api/save-audio called")
    logger.debug("Request: %s %s", request.method, request.url)
    
    try:
        # Check if audio file is present
        if 'audio' not in request.files:
            logger.warning("No audio file in request")
            return jsonify({"error": "No audio file provided"}), 400
        
        audio_file = request.files['audio']
        username = request.form.get('username', 'unknown')
        
        if audio_file.filename == '':
            logger.warning("No audio file selected")
            return jsonify({"error": "No audio file selected"}), 400
        
        # Get the filename from the form data
        filename = audio_file.filename
        
        # Create user directory if it doesn't exist
        pdn_file_path = PDNFilePath()
        user_dir = pdn_file_path.get_user_dir(username)
        user_dir.mkdir(parents=True, exist_ok=True)
        
        # Save the audio file
        audio_path = user_dir / filename
        audio_file.save(audio_path)
        
        logger.info(f"Audio file saved successfully: {audio_path}")
        
        return jsonify({
            "message": "Audio saved successfully",
            "filename": filename,
            "path": str(audio_path),
            "status": "success"
        })
        
    except Exception as e:
        logger.error(f"Error saving audio file: {str(e)}")
        return jsonify({"error": f"Failed to save audio: {str(e)}"}), 500


@pdn_admin_bp.route('/download-json')
def download_user_json():
    """Download user's JSON answers file."""
    logger.debug("GET /pdn-admin/download-json called")
    logger.debug("Request: %s %s", request.method, request.url)

    # Extract session token from query parameters
    session_token = request.args.get('session_token')
    if not session_token:
        logger.warning("No session token provided")
        abort(401, description="No session token provided")

    # Verify session
    verify_session(session_token)

    # Extract admin password from query parameters
    admin_password = request.args.get('admin_password')
    if not admin_password:
        logger.warning("No admin password provided")
        abort(401, description="Admin password required")

    # Verify admin password (same as email sending functionality)
    if admin_password != 'admin':
        logger.warning("Invalid admin password provided")
        response = jsonify({"error": "Invalid admin password"}), 401
        response.headers['X-Error-Type'] = 'invalid_password'
        return response

    # Get file path from query parameters
    file_path = request.args.get('file_path')
    if not file_path:
        logger.warning("No file path provided")
        abort(400, description="No file path provided")

    # Use the environment variable for saved_results directory
    saved_results_dir = os.getenv('SAVED_RESULTS_DIR', 'saved_results')

    # Construct the full file path
    if file_path.startswith('saved_results/'):
        # Remove the 'saved_results/' prefix
        relative_path = file_path.replace('saved_results/', '')
        json_path = Path(saved_results_dir) / relative_path
    else:
        # Use the file_path as is
        json_path = Path(saved_results_dir) / file_path

    logger.debug(f"Looking for JSON file at: {json_path.absolute()}")

    # Security check: ensure the path is within the allowed directory
    try:
        json_path = json_path.resolve()
        saved_results_path = Path(saved_results_dir).resolve()
        if not str(json_path).startswith(str(saved_results_path)):
            logger.warning("Path traversal attempt detected")
            abort(403, description="Access denied")
    except Exception as e:
        logger.error(f"Path resolution error: {e}")
        abort(400, description="Invalid file path")

    # Check if file exists
    if not json_path.exists():
        logger.warning(f"JSON file not found: {json_path}")
        abort(404, description="JSON file not found")

    # Check if it's a JSON file
    if not json_path.suffix.lower() == '.json':
        logger.warning(f"File is not a JSON file: {json_path}")
        abort(400, description="File is not a JSON file")

    logger.debug(f"JSON file found, serving: {json_path}")

    try:
        return send_file(
            json_path,
            mimetype='application/json',
            as_attachment=True,
            download_name=json_path.name
        )
    except Exception as e:
        logger.error(f"Error serving JSON file: {e}")
        abort(500, description="Error serving JSON file")
