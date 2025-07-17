import csv
import logging
import secrets
from pathlib import Path
import os

from flask import Blueprint, request, render_template, jsonify, current_app, send_file, abort

from ..utils.answer_storage import load_answers
from ..utils.csv_metadata_handler import UserMetadataHandler
from ..utils.email_sender import send_pdn_code_email
from ..utils.pdn_calculator import calculate_pdn_code
from ..utils.pdn_file_path import PDNFilePath

# Configure logging
logger = logging.getLogger(__name__)

# Create blueprint
pdn_admin_bp = Blueprint('pdn_admin', __name__,
                         template_folder='templates',
                         static_folder='../static')

# Admin sessions storage (in production, use Redis or database)
admin_sessions = set()


def load_user_metadata():
    """
    Load user metadata from the CSV file and JSON files.
    
    Returns:
        List of dictionaries containing user metadata
    """
    try:
        csv_file_path = Path(os.getenv('SAVED_RESULTS_DIR', 'saved_results') ) / 'user_metadata.csv'
        logger.info(f"CSV file path: {csv_file_path}")
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
                    logger.warning(f"Could not load JSON metadata for {email}: {e}")

                # Convert CSV column names to the expected format and merge with JSON metadata
                user_data = {
                    "user_id": (row.get("User ID") or "").strip(),
                    "email": email,
                    "date": (row.get("Date") or "").strip(),
                    "pdn_code": (row.get("PDN Code") or "").strip(),
                    "pdn_voice_code": (row.get("PDN Voice Code") or "").strip(),
                    "diagnose_pdn_code": (row.get("Diagnose PDN Code") or "").strip(),
                    "diagnose_comments": (row.get("Diagnose Comments") or "").strip(),
                    # Load from JSON metadata if available, otherwise use CSV or defaults
                    "first_name": (json_metadata.get("first_name") or row.get("First Name") or "").strip(),
                    "last_name": (json_metadata.get("last_name") or row.get("Last Name") or "").strip(),
                    "phone": (json_metadata.get("phone") or row.get("Phone") or "").strip(),
                    "native_language": (json_metadata.get("native_language") or json_metadata.get("mother_language") or row.get("Native Language") or "").strip(),
                    "gender": (json_metadata.get("gender") or row.get("Gender") or "").strip(),
                    "education_level": (json_metadata.get("education_level") or json_metadata.get("education") or row.get("Education Level") or "").strip(),
                    "job_title": (json_metadata.get("job_title") or row.get("Job Title") or "").strip(),
                    "birth_year": (json_metadata.get("birth_year") or row.get("Birth Year") or "").strip(),
                    "link_to_user": f"/user/{email}",
                    "questionnaire": f"/api/user/questionnaire/{email}",
                    "voice": f"/api/user/voice/{email}"
                }
                metadata_list.append(user_data)

        logger.info(f"Loaded {len(metadata_list)} user records from CSV and JSON")
        return metadata_list

    except Exception as e:
        logger.error(f"Error loading user metadata from CSV: {e}")
        return []


def get_user_metadata():
    """
    Get user metadata, loading from CSV if needed.
    
    Returns:
        List of dictionaries containing user metadata
    """
    return load_user_metadata()


def verify_session(session_token: str):
    """Verify admin session"""
    if session_token not in admin_sessions:
        abort(401, description="Invalid session")
    return True


@pdn_admin_bp.route('/')
def admin_login_page():
    """Admin login page"""
    logger.debug("GET /pdn-admin/ called")
    logger.info("Request: %s %s", request.method, request.url)
    logger.info("Response: %s", 200)
    return render_template("admin_login.html")


@pdn_admin_bp.route('/dashboard')
def admin_dashboard_page():
    """Admin dashboard page"""
    logger.debug("GET /pdn-admin/dashboard called")
    logger.info("Request: %s %s", request.method, request.url)
    logger.info("Response: %s", 200)
    return render_template("admin_dashboard.html")


@pdn_admin_bp.route('/login', methods=['POST'])
def admin_login():
    """Admin login endpoint"""
    logger.debug("POST /pdn-admin/login called")
    logger.info("Request: %s %s", request.method, request.url)
    logger.info("Response: %s", 200)

    try:
        login_data = request.get_json()
        password = login_data.get('password', '')

        # Simple password check (you can make this more secure)
        if password.lower() == current_app.config.get('ADMIN_PASSWORD', 'pdn').lower():
            session_token = secrets.token_urlsafe(32)
            admin_sessions.add(session_token)
            return jsonify({
                "success": True,
                "message": "Login successful",
                "session_token": session_token
            })

        # Log failed login attempt
        logger.warning(f"Failed login attempt with password: {password}")

        return jsonify({"error": "Invalid credentials"}), 401

    except Exception as e:
        logger.error(f"Login error: {e}")
        return jsonify({"error": "Login failed"}), 400


@pdn_admin_bp.route('/logout')
def admin_logout():
    """Admin logout endpoint"""
    logger.debug("GET /pdn-admin/logout called")
    logger.info("Request: %s %s", request.method, request.url)
    logger.info("Response: %s", 200)

    session_token = request.args.get('session_token')
    if session_token and session_token in admin_sessions:
        admin_sessions.remove(session_token)
    return jsonify({"success": True, "message": "Logout successful"})


@pdn_admin_bp.route('/metadata')
def get_metadata():
    """Get metadata CSV data"""
    logger.debug("GET /pdn-admin/metadata called")
    logger.info("Request: %s %s", request.method, request.url)
    logger.info("Response: %s", 200)

    # For now, allow access without session token for the dashboard
    # In production, you should implement proper session management
    return jsonify({"data": get_user_metadata()})


@pdn_admin_bp.route('/metadata/csv')
def get_metadata_csv():
    """Get metadata as CSV download"""
    logger.debug("GET /pdn-admin/metadata/csv called")
    logger.info("Request: %s %s", request.method, request.url)
    logger.info("Response: %s", 200)

    session_token = request.args.get('session_token')

    verify_session(session_token)

    metadata = get_user_metadata()

    return jsonify({"data": metadata})


@pdn_admin_bp.route('/download/csv')
def download_csv_file():
    """Download the actual CSV file"""
    logger.debug("GET /pdn-admin/download/csv called")
    logger.info("Request: %s %s", request.method, request.url)

    session_token = request.args.get('session_token')
    verify_session(session_token)

    try:
        csv_file_path = Path("saved_results/user_metadata.csv")
        if not csv_file_path.exists():
            logger.error("CSV file not found: %s", csv_file_path)
            return jsonify({"error": "CSV file not found"}), 404

        return send_file(
            csv_file_path,
            as_attachment=True,
            download_name="user_metadata.csv",
            mimetype="text/csv"
        )
    except Exception as e:
        logger.error(f"Error downloading CSV file: {e}")
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
    logger.debug(f"GET /pdn-admin/user/questionnaire/{email} called")
    logger.info("Request: %s %s", request.method, request.url)
    logger.info("Response: %s", 200)

    session_token = request.args.get('session_token')
    verify_session(session_token)

    try:
        # Find user in data
        csv_metadata_handler = UserMetadataHandler()
        logger.info(f"Loading questionnaire data for {email}")
        
        questionnaire_data = csv_metadata_handler.get_user_files(email, "answers")
        logger.info(f"Questionnaire data loaded: {questionnaire_data is not None}")
        
        if not questionnaire_data:
            logger.warning(f"No questionnaire data found for user: {email}")
            return jsonify({"error": "User questionnaire not found"}), 404
        
        # Get user metadata from CSV (including User ID)
        logger.info(f"Loading CSV metadata for {email}")
        user_metadata = csv_metadata_handler.get_user_by_email(email)
        logger.info(f"CSV metadata loaded: {user_metadata is not None}")
        
        if user_metadata:
            # Add user metadata to the questionnaire data
            questionnaire_data['metadata'] = user_metadata
            logger.info(f"Successfully loaded questionnaire data for {email} with User ID: {user_metadata.get('User ID', 'N/A')}")
        else:
            logger.warning(f"No CSV metadata found for user: {email}")
            # Create a minimal metadata structure
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
    logger.info("Request: %s %s", request.method, request.url)
    logger.info("Response: %s", 200)

    session_token = request.args.get('session_token')
    verify_session(session_token)

    try:
        # Find user in data
        csv_metadata_handler = UserMetadataHandler()
        pdn_file_path = PDNFilePath()
        user_dir = pdn_file_path.get_user_dir(email)
        
        # Look for both question recordings
        question1_filename = f"{email}_question1.wav"
        question2_filename = f"{email}_question2.wav"
        
        question1_path = user_dir / question1_filename
        question2_path = user_dir / question2_filename
        
        voice_recordings = {}
        
        if question1_path.exists():
            voice_recordings['question1'] = {
                'filename': question1_filename,
                'path': str(question1_path),
                'exists': True
            }
        
        if question2_path.exists():
            voice_recordings['question2'] = {
                'filename': question2_filename,
                'path': str(question2_path),
                'exists': True
            }
        
        # If no new format recordings found, try old format for backward compatibility
        if not voice_recordings:
            user_audio_path = csv_metadata_handler.get_user_audio_path(email, "wav")
            if user_audio_path:
                audio_file_path = Path(user_audio_path)
                if audio_file_path.exists():
                    voice_recordings['legacy'] = {
                        'filename': audio_file_path.name,
                        'path': user_audio_path,
                        'exists': True
                    }

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
    logger.info("Request: %s %s", request.method, request.url)
    logger.info("Response: %s", 200)

    session_token = request.args.get('session_token')
    verify_session(session_token)

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

        # Update CSV with the new diagnose information
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
    logger.info("Request: %s %s", request.method, request.url)
    logger.info("Response: %s", 200)

    session_token = request.args.get('session_token')
    verify_session(session_token)

    try:
        # Load user answers
        user_answers = load_answers(email)
        if not user_answers:
            return jsonify({"error": "User answers not found"}), 404
        
        # Calculate PDN code
        pdn_code = calculate_pdn_code(user_answers)

        if not pdn_code:
            return jsonify({"error": "Could not calculate PDN code"}), 400

        # Send email
        email_sent = send_pdn_code_email(user_answers, pdn_code)

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


@pdn_admin_bp.route('/audio/<path:file_path>')
def serve_audio(file_path):
    """Serve audio files with authentication."""
    logger.debug(f"GET /pdn-admin/audio/{file_path} called")
    logger.info("Request: %s %s", request.method, request.url)
    logger.info("Response: %s", 200)

    # Extract session token from query parameters
    session_token = request.args.get('session_token')
    logger.debug(f"Session token: {session_token}")

    if not session_token:
        logger.warning("No session token provided")
        abort(401, description="No session token provided")

    # Verify session
    verify_session(session_token)

    # Construct the full path to the audio file
    audio_path = Path('saved_results') / file_path
    logger.debug(f"Looking for file at: {audio_path.absolute()}")

    # Security check: ensure the path is within the allowed directory
    try:
        audio_path = audio_path.resolve()
        saved_results_path = Path('saved_results').resolve()
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
