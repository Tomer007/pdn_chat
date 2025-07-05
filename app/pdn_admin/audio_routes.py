import logging
from datetime import datetime
from pathlib import Path

from flask import Blueprint, request, jsonify
from werkzeug.utils import secure_filename

from ..utils.pdn_file_path import PDNFilePath

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

audio_bp = Blueprint('audio', __name__)


@audio_bp.route('/api/save-audio', methods=['POST'])
def save_audio():
    """
    Save user audio file to the backend server
    """
    try:
        # Validate input
        username = request.form.get('username')
        audio = request.files.get('audio')

        if not username or not username.strip():
            return jsonify({"error": "Username is required"}), 400
        if not audio:
            return jsonify({"error": "Audio file is required"}), 400

        pdn_file_path = PDNFilePath()
        user_dir = pdn_file_path.get_user_dir(username)
        user_dir.mkdir(parents=True, exist_ok=True)

        # Create filename
        file_extension = Path(audio.filename).suffix if audio.filename else '.wav'
        filename = secure_filename(f"{username}{file_extension}")
        file_path = user_dir / filename

        # Save the file
        audio.save(file_path)
        logger.info(f"Audio saved successfully: {file_path}")

        return jsonify({
            "success": True,
            "message": "Audio saved successfully",
            "file_path": str(file_path),
            "filename": filename,
            "username": username,
            "timestamp": datetime.now().strftime("%Y%m%d_%H%M%S")
        })
    except Exception as e:
        logger.error(f"Error saving audio: {str(e)}")
        return jsonify({"error": f"Internal server error: {str(e)}"}), 500



