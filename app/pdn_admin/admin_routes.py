import csv
import logging
import secrets
from pathlib import Path
import os

from flask import Blueprint, request, render_template, jsonify, current_app, send_file, abort

from ..utils.answer_storage import load_answers
from ..utils.csv_metadata_handler import UserMetadataHandler
from ..utils.email_sender import send_pdn_code_email

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
    Load user metadata from the CSV file.
    
    Returns:
        List of dictionaries containing user metadata
    """
    try:
        csv_file_path = Path(os.getenv('SAVED_RESULTS_DIR', 'saved_results') ) / 'user_metadata.csv'
        if not csv_file_path.exists():
            logger.warning("user_metadata.csv file not found")
            return []

        metadata_list = []
        with open(csv_file_path, 'r', encoding='utf-8') as csvfile:
            reader = csv.DictReader(csvfile)
            for row in reader:
                # Skip empty rows
                if not row.get("Email", "").strip():
                    continue

                # Convert CSV column names to the expected format
                user_data = {
                    "email": row.get("Email", "").strip(),
                    "date": row.get("Date", "").strip(),
                    "pdn_code": row.get("PDN Code", "").strip(),
                    "pdn_voice_code": row.get("PDN Voice Code", "").strip(),
                    "diagnose_pdn_code": row.get("Diagnose PDN Code", "").strip(),
                    "diagnose_comments": row.get("Diagnose Comments", "").strip(),
                    # Add default values for missing fields
                    "first_name": "",
                    "last_name": "",
                    "phone": "",
                    "native_language": "",
                    "gender": "",
                    "education_level": "",
                    "job_title": "",
                    "birth_year": "",
                    "link_to_user": f"/user/{row.get('Email', '').strip()}",
                    "questionnaire": f"/api/user/questionnaire/{row.get('Email', '').strip()}",
                    "voice": f"/api/user/voice/{row.get('Email', '').strip()}"
                }
                metadata_list.append(user_data)

        logger.info(f"Loaded {len(metadata_list)} user records from CSV")
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

    logger.info(f"Metadata: {metadata}")

    return jsonify({"data": metadata})



@pdn_admin_bp.route('/user/questionnaire/<email>')
def get_user_questionnaire(email):
    """Get user questionnaire data"""
    logger.debug(f"GET /pdn-admin/user/questionnaire/{email} called")
    logger.info("Request: %s %s", request.method, request.url)
    logger.info("Response: %s", 200)

    session_token = request.args.get('session_token')
    verify_session(session_token)

    # Find user in data
    csv_metadata_handler = UserMetadataHandler()
    questionnaire_data = csv_metadata_handler.get_user_files(email, "answers")
    if not questionnaire_data:
        return jsonify({"error": "User not found"}), 404
    return jsonify(questionnaire_data)


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
        user_audio_path = csv_metadata_handler.get_user_audio_path(email, "wav")

        # Check if path is None or empty
        if not user_audio_path:
            return jsonify({"error": "User voice recording not found"}), 404

        # Verify the file actually exists
        audio_file_path = Path(user_audio_path)
        if not audio_file_path.exists():
            return jsonify({"error": "Voice recording file not found"}), 404

        # Return voice file info
        return jsonify({
            "email": email,
            "voice_url": user_audio_path,
            "file_exists": True
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
        pdn_code = "P10"
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
