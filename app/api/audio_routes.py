import os
import shutil
from datetime import datetime
from pathlib import Path
from fastapi import APIRouter, UploadFile, File, Form, HTTPException
from fastapi.responses import JSONResponse
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create router
audio_router = APIRouter(prefix="/api", tags=["audio"])

# Base directory for saved results
SAVED_RESULTS_DIR = Path(os.getenv('ANSWERS_DIR', 'saved_results'))

# Log the directory being used for debugging
logger.info(f"ANSWERS_DIR environment variable: {os.getenv('ANSWERS_DIR', 'NOT_SET')}")
logger.info(f"Using SAVED_RESULTS_DIR: {SAVED_RESULTS_DIR}")
logger.info(f"Current working directory: {os.getcwd()}")
logger.info(f"Absolute SAVED_RESULTS_DIR path: {SAVED_RESULTS_DIR.absolute()}")

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
        
        # Sanitize username for file system safety
        safe_username = "".join(c for c in username if c.isalnum() or c in (' ', '-', '_')).rstrip()
        safe_username = safe_username.replace(' ', '_')
        
        # Create user directory if it doesn't exist
        user_dir = SAVED_RESULTS_DIR / safe_username
        user_dir.mkdir(parents=True, exist_ok=True)
        
        # Generate timestamp for filename
        timestamp = datetime.now().strftime("%Y-%m-%d_%H%M")
        
        # Create filename
        file_extension = Path(audio.filename).suffix if audio.filename else '.wav'
        filename = f"{safe_username}_audio_{timestamp}{file_extension}"
        
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
                "username": safe_username,
                "timestamp": timestamp
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
        # Sanitize username
        safe_username = "".join(c for c in username if c.isalnum() or c in (' ', '-', '_')).rstrip()
        safe_username = safe_username.replace(' ', '_')
        
        # Check if user directory exists
        user_dir = SAVED_RESULTS_DIR / safe_username
        
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

@audio_router.delete("/audio/{username}/{filename}")
async def delete_user_audio(username: str, filename: str):
    """
    Delete a specific audio file for a user
    
    Args:
        username: The name of the user
        filename: The name of the file to delete
    
    Returns:
        JSON response with deletion status
    """
    try:
        # Sanitize username and filename
        safe_username = "".join(c for c in username if c.isalnum() or c in (' ', '-', '_')).rstrip()
        safe_username = safe_username.replace(' ', '_')
        
        # Validate filename format
        if not filename.startswith(f"{safe_username}_audio_"):
            raise HTTPException(status_code=400, detail="Invalid filename format")
        
        # Construct file path
        file_path = SAVED_RESULTS_DIR / safe_username / filename
        
        # Check if file exists
        if not file_path.exists():
            raise HTTPException(status_code=404, detail="Audio file not found")
        
        # Delete the file
        file_path.unlink()
        
        logger.info(f"Audio file deleted: {file_path}")
        
        return JSONResponse(
            status_code=200,
            content={
                "success": True,
                "message": "Audio file deleted successfully",
                "filename": filename
            }
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting audio file: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}") 