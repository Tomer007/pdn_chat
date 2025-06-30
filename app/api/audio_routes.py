import shutil
from datetime import datetime
from pathlib import Path
from fastapi import APIRouter, UploadFile, File, Form, HTTPException
from fastapi.responses import JSONResponse
import logging
from app.utils.pdn_file_path import PDNFilePath

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create router
audio_router = APIRouter(prefix="/api", tags=["audio"])


@audio_router.post("/save-audio")
async def save_audio(
    audio: UploadFile = File(...),
    username: str = Form(...)
):
    """
    Save user audio file to the backend server
    
    Args:
        audio: The audio file uploaded by the user
        username: The name of the user
    
    Returns:
        JSON response with file path and status
    """
    try:
        # Validate input
        if not username or not username.strip():
            raise HTTPException(status_code=400, detail="Username is required")
        
        if not audio:
            raise HTTPException(status_code=400, detail="Audio file is required")
        
        pdn_file_path = PDNFilePath()
        user_dir = pdn_file_path.get_user_dir(username)
        
        # Create filename
        file_extension = Path(audio.filename).suffix if audio.filename else '.wav'
        filename = f"{username}{file_extension}"
        
        # Full path for the file
        file_path = user_dir / filename
        
        # Save the file
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(audio.file, buffer)
        
        logger.info(f"Audio saved successfully: {file_path}")
        
        # Return success response
        return JSONResponse(
            status_code=200,
            content={
                "success": True,
                "message": "Audio saved successfully",
                "file_path": str(file_path),
                "filename": filename,
                "username": username,
                "timestamp": datetime.now().strftime("%Y%m%d_%H%M%S")
            }
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error saving audio: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")

@audio_router.get("/audio/{username}")
async def get_user_audio_files(username: str):
    """
    Get list of audio files for a specific user
    
    Args:
        username: The name of the user
    
    Returns:
        JSON response with list of audio files
    """
    try:
        pdn_file_path = PDNFilePath()
        user_dir = pdn_file_path.get_user_dir(username)
        
        # Check if user directory exists
        
        if not user_dir.exists():
            return JSONResponse(
                status_code=200,
                content={
                    "success": True,
                    "message": "No audio files found for this user",
                    "files": []
                }
            )
        
        # Get list of audio files
        audio_files = []
        for file_path in user_dir.glob("*_audio_*"):
            if file_path.is_file():
                audio_files.append({
                    "filename": file_path.name,
                    "file_path": str(file_path),
                    "size": file_path.stat().st_size,
                    "created": datetime.fromtimestamp(file_path.stat().st_ctime).isoformat()
                })
        
        # Sort by creation time (newest first)
        audio_files.sort(key=lambda x: x["created"], reverse=True)
        
        return JSONResponse(
            status_code=200,
            content={
                "success": True,
                "message": f"Found {len(audio_files)} audio files",
                "files": audio_files
            }
        )
        
    except Exception as e:
        logger.error(f"Error getting audio files: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")

def save_audio_file(email: str, audio_data: bytes):
    """Save audio file for user"""
    try:
        # Create directory for user if it doesn't exist
        user_dir = Path("saved_results") / email.replace("@", "").replace(".", "")
        user_dir.mkdir(parents=True, exist_ok=True)
        
        # Generate timestamp for unique filename
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")  # Fix: Define timestamp variable
        
        filename = f"{email}_{timestamp}.wav"
        filepath = user_dir / filename
        
        # Save the audio file
        with open(filepath, 'wb') as f:
            f.write(audio_data)
        
        print(f"Audio saved successfully: {filepath}")
        return str(filepath)
        
    except Exception as e:
        print(f"Error saving audio: {e}")
        raise

