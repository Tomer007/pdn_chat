import csv
import io
import logging
import secrets
from datetime import datetime
from pathlib import Path

from flask import Blueprint, request, jsonify, current_app, send_file, abort
from werkzeug.exceptions import HTTPException

from ..utils.answer_storage import load_answers
# Import utilities
from ..utils.csv_metadata_handler import UserMetadataHandler
from ..utils.email_sender import send_email
from ..utils.report_generator import load_pdn_report

# Import logger

# Configure logging
logger = logging.getLogger(__name__)

# Create blueprint for admin API endpoints
admin_api_bp = Blueprint('admin_api', __name__)

# Admin sessions storage (in production, use Redis or database)
admin_sessions = set()


def verify_session(session_token: str):
    """Verify admin session"""
    if session_token not in admin_sessions:
        raise HTTPException(status_code=401, detail="Invalid session")
    return True


def load_user_metadata():
    """
    Load user metadata from the CSV file.
    
    Returns:
        List of dictionaries containing user metadata
    """
    try:
        csv_file_path = Path('saved_results/user_metadata.csv')
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


@admin_api_bp.route('/api/login', methods=['POST'])
def admin_login():
    """Admin login endpoint"""
    logger.debug("POST /pdn-admin/api/login called")
    logger.info("Request: %s %s", request.method, request.url)
    logger.info("Response: %s", 200)

    try:
        login_data = request.get_json()
        password = login_data.get('password', '')

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


@admin_api_bp.route('/api/logout')
def admin_logout():
    """Admin logout endpoint"""
    logger.debug("GET /pdn-admin/api/logout called")
    logger.info("Request: %s %s", request.method, request.url)
    logger.info("Response: %s", 200)

    session_token = request.args.get('session_token')
    if session_token and session_token in admin_sessions:
        admin_sessions.remove(session_token)
    return jsonify({"success": True, "message": "Logout successful"})


@admin_api_bp.route('/api/metadata')
def get_metadata():
    """Get metadata CSV data"""
    logger.debug("GET /pdn-admin/api/metadata called")
    logger.info("Request: %s %s", request.method, request.url)
    logger.info("Response: %s", 200)

    session_token = request.args.get('session_token')
    verify_session(session_token)

    return jsonify({"data": get_user_metadata()})


@admin_api_bp.route('/api/metadata/csv')
def get_metadata_csv():
    """Get metadata as CSV download"""
    logger.debug("GET /pdn-admin/api/metadata/csv called")
    logger.info("Request: %s %s", request.method, request.url)
    logger.info("Response: %s", 200)

    session_token = request.args.get('session_token')
    verify_session(session_token)

    # Create CSV in memory
    output = io.StringIO()
    writer = csv.DictWriter(output, fieldnames=get_user_metadata()[0].keys())
    writer.writeheader()
    writer.writerows(get_user_metadata())

    output.seek(0)

    return send_file(
        io.BytesIO(output.getvalue().encode('utf-8')),
        mimetype='text/csv',
        as_attachment=True,
        download_name=f"pdn_metadata_{datetime.now().strftime('%Y%m%d')}.csv"
    )


@admin_api_bp.route('/api/user/questionnaire/<email>')
def get_user_questionnaire(email):
    """Get user questionnaire data"""
    logger.debug(f"GET /pdn-admin/api/user/questionnaire/{email} called")
    logger.info("Request: %s %s", request.method, request.url)
    logger.info("Response: %s", 200)

    session_token = request.args.get('session_token')
    verify_session(session_token)

    # Load user answers using the correct function
    questionnaire_data = load_answers(email)
    if not questionnaire_data:
        return jsonify({"error": "User answers not found"}), 404

    # Add questions data to the response
    from flask import current_app
    questions_data = current_app.config.get('PDN_QUESTIONS', {})
    questionnaire_data['questions_data'] = questions_data

    return jsonify(questionnaire_data)


@admin_api_bp.route('/api/user/voice/<email>')
def get_user_voice(email):
    """Get user voice recording URL"""
    logger.debug(f"GET /pdn-admin/api/user/voice/{email} called")
    logger.info("Request: %s %s", request.method, request.url)
    logger.info("Response: %s", 200)

    session_token = request.args.get('session_token')
    verify_session(session_token)

    try:
        # Find user in data
        user_audio_path = UserMetadataHandler().get_user_audio_path(email, "wav")

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


@admin_api_bp.route('/api/user/diagnose/<email>', methods=['PUT'])
def update_user_diagnose(email):
    """Update user diagnose information"""
    logger.debug(f"PUT /pdn-admin/api/user/diagnose/{email} called")
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
        if "diagnose_pdn_code" in diagnose_data:
            user_data["diagnose_pdn_code"] = diagnose_data["diagnose_pdn_code"]
        elif "diagnose_pdn_code" not in user_data:
            user_data["diagnose_pdn_code"] = user_data.get("pdn_code", "")

        if "diagnose_comments" in diagnose_data:
            user_data["diagnose_comments"] = diagnose_data["diagnose_comments"]
        elif "diagnose_comments" not in user_data:
            user_data["diagnose_comments"] = ""

        return jsonify({
            "success": True,
            "message": "Diagnose updated successfully",
            "user": user_data
        })
    except Exception as e:
        logger.error(f"Error updating diagnose: {e}")
        return jsonify({"error": "Failed to update diagnose"}), 400


@admin_api_bp.route('/api/user/send_email/<email>', methods=['POST'])
def send_user_email(email):
    """Send PDN report email to user"""
    logger.debug(f"POST /pdn-admin/api/user/send_email/{email} called")
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
        pdn_code = "E5"  # TODO: Implement calculate_pdn_code
        # pdn_code = calculate_pdn_code(user_answers)

        if not pdn_code:
            return jsonify({"error": "Could not calculate PDN code"}), 400

        # Load report data
        report_data = load_pdn_report(pdn_code)
        if not report_data:
            return jsonify({"error": "Could not load PDN report"}), 400

        # Send email
        email_sent = send_email(user_answers, pdn_code, report_data)

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


@admin_api_bp.route('/api/audio/<path:file_path>')
def serve_audio(file_path):
    """Serve audio files with authentication."""
    logger.debug(f"GET /pdn-admin/api/audio/{file_path} called")
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



