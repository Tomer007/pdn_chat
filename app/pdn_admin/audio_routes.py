import shutil
from datetime import datetime
from pathlib import Path
import logging
from flask import Blueprint, request, jsonify, current_app, abort
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

@audio_bp.route('/api/audio/<username>', methods=['GET'])
def get_user_audio_files(username):
    """
    Get list of audio files for a specific user
    """
    try:
        pdn_file_path = PDNFilePath()
        user_dir = pdn_file_path.get_user_dir(username)
        if not user_dir.exists():
            return jsonify({
                "success": True,
                "message": "No audio files found for this user",
                "files": []
            })
        audio_files = []
        for file_path in user_dir.glob("*_audio_*"):
            if file_path.is_file():
                audio_files.append({
                    "filename": file_path.name,
                    "file_path": str(file_path),
                    "size": file_path.stat().st_size,
                    "created": datetime.fromtimestamp(file_path.stat().st_ctime).isoformat()
                })
        audio_files.sort(key=lambda x: x["created"], reverse=True)
        return jsonify({
            "success": True,
            "message": f"Found {len(audio_files)} audio files",
            "files": audio_files
        })
    except Exception as e:
        logger.error(f"Error getting audio files: {str(e)}")
        return jsonify({"error": f"Internal server error: {str(e)}"}), 500

def save_audio_file(email: str, audio_data: bytes):
    """Save audio file for user"""
    try:
        user_dir = Path("saved_results") / email.replace("@", "").replace(".", "")
        user_dir.mkdir(parents=True, exist_ok=True)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{email}_{timestamp}.wav"
        filepath = user_dir / filename
        with open(filepath, 'wb') as f:
            f.write(audio_data)
        print(f"Audio saved successfully: {filepath}")
        return str(filepath)
    except Exception as e:
        print(f"Error saving audio: {e}")
        raise 