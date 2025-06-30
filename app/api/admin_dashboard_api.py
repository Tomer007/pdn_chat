import csv
import io
from datetime import datetime
from typing import Dict
from fastapi import APIRouter, HTTPException, Depends
from fastapi.responses import StreamingResponse, FileResponse
from fastapi.security import HTTPBasic, HTTPBasicCredentials
import secrets
from app.utils.csv_metadata_handler import CSVMetadataHandler
from app.utils.email_sender import send_email
from app.utils.answer_storage import load_answers
from app.utils.report_generator import load_pdn_report
from flask import Blueprint
from pathlib import Path

# Security
security = HTTPBasic()
admin_router = APIRouter(prefix="/admin", tags=["admin"])

# In-memory session storage (in production, use proper session management)
admin_sessions = set()

# Create the blueprint
admin_bp = Blueprint('admin', __name__)

def verify_admin_credentials(credentials: HTTPBasicCredentials = Depends(security)):
    """Verify admin credentials"""
    if credentials.password == "Pdn":
        # Store session token
        session_token = secrets.token_urlsafe(32)
        admin_sessions.add(session_token)
        return session_token
    raise HTTPException(
        status_code=401,
        detail="Invalid credentials",
        headers={"WWW-Authenticate": "Basic"},
    )

def verify_session(session_token: str):
    """Verify admin session"""
    if session_token not in admin_sessions:
        raise HTTPException(status_code=401, detail="Invalid session")
    return True

# Hardcoded CSV data as specified
HARDCODED_CSV_DATA = [
    {
        "email": "tomergur@example.com",
        "date": "2025-01-15",
        "pdn_code": "E1",
        "diagnose_pdn_code": "N/A",
        "diagnose_comments": "",
        "first_name": "תומר",
        "last_name": "גור",
        "phone": "054-5555555",
        "native_language": "עברית",
        "gender": "זכר",
        "education_level": "תואר ראשון",
        "job_title": "מפתח תוכנה",
        "birth_year": "1990",
        "link_to_user": "/user/user1@example.com",
        "questionnaire": "/api/user/questionnaire/user1@example.com",
        "voice": "/api/user/voice/user1@example.com"
    },
    {
        "email": "user2@example.com",
        "date": "2025-01-16",
        "pdn_code": "A7",
        "diagnose_pdn_code": "A7",
        "diagnose_comments": "משתמש מוחצן ומאורגן",
        "first_name": "שרה",
        "last_name": "לוי",
        "phone": "052-9876543",
        "native_language": "עברית",
        "gender": "נקבה",
        "education_level": "תואר שני",
        "job_title": "מנהלת פרויקטים",
        "birth_year": "1985",
        "link_to_user": "/user/user2@example.com",
        "questionnaire": "/api/user/questionnaire/user2@example.com",
        "voice": "/api/user/voice/user2@example.com"
    },
    {
        "email": "tomergur@gmail.com",
        "date": "2025-01-17",
        "pdn_code": "T4",
        "diagnose_pdn_code": "T4",
        "diagnose_comments": "משתמש גמיש ומופנם",
        "first_name": "תומר",
        "last_name": "גור",
        "phone": "054-5555555",
        "native_language": "עברית",
        "gender": "זכר",
        "education_level": "תואר ראשון",
        "job_title": "מהנדס תוכנה",
        "birth_year": "1992",
        "link_to_user": "/user/tomergur@gmail.com",
        "questionnaire": "/api/user/questionnaire/tomergur@gmail.com",
        "voice": "/api/user/voice/tomergur@gmail.com"
    }
]

@admin_router.post("/login")
async def admin_login(credentials: HTTPBasicCredentials = Depends(security)):
    """Admin login endpoint"""
    if credentials.password.lower() == "pdn":
        session_token = secrets.token_urlsafe(32)
        admin_sessions.add(session_token)
        return {
            "success": True,
            "message": "Login successful",
            "session_token": session_token
        }
    
    # Log failed login attempt
    print(f"Failed login attempt with password: {credentials.password}")
    
    raise HTTPException(
        status_code=401,
        detail="Invalid credentials",
        headers={"WWW-Authenticate": "Basic"},
    )

@admin_router.get("/logout")
async def admin_logout(session_token: str):
    """Admin logout endpoint"""
    if session_token in admin_sessions:
        admin_sessions.remove(session_token)
    return {"success": True, "message": "Logout successful"}

@admin_router.get("/metadata")
#TODO add dynamic data from csv
async def get_metadata(session_token: str):
    """Get metadata CSV data"""
    verify_session(session_token)
    return {"data": HARDCODED_CSV_DATA}

@admin_router.get("/metadata/csv")
async def get_metadata_csv(session_token: str):
    """Get metadata as CSV download"""
    verify_session(session_token)
    
    # Create CSV in memory
    output = io.StringIO()
    writer = csv.DictWriter(output, fieldnames=HARDCODED_CSV_DATA[0].keys())
    writer.writeheader()
    writer.writerows(HARDCODED_CSV_DATA)
    
    output.seek(0)
    return StreamingResponse(
        io.BytesIO(output.getvalue().encode('utf-8')),
        media_type="text/csv",
        headers={"Content-Disposition": f"attachment; filename=pdn_metadata_{datetime.now().strftime('%Y%m%d')}.csv"}
    )

@admin_router.get("/user/questionnaire/{email}")
async def get_user_questionnaire(email: str, session_token: str):
    """Get user questionnaire data"""
    verify_session(session_token)
    
    # Find user in data
    csv_metadata_handler = CSVMetadataHandler()
    questionnaire_data = csv_metadata_handler.get_user_files(email, "answers")
    if not questionnaire_data:
        raise HTTPException(status_code=404, detail="User not found")
    return questionnaire_data

@admin_router.get("/user/voice/{email}")
async def get_user_voice(email: str, session_token: str):
    """Get user voice recording URL"""
    verify_session(session_token)
    
    try:
        # Find user in data
        csv_metadata_handler = CSVMetadataHandler()
        user_audio_path = csv_metadata_handler.get_user_audio_path(email, "wav")
        
        # Check if path is None or empty
        if not user_audio_path:
            raise HTTPException(status_code=404, detail="User voice recording not found")
        
        # Verify the file actually exists
        audio_file_path = Path(user_audio_path)
        if not audio_file_path.exists():
            raise HTTPException(status_code=404, detail="Voice recording file not found")
        
        # Return voice file info
        return {
            "email": email,
            "voice_url": user_audio_path,
            "file_exists": True
        }
    except HTTPException:
        raise
    except Exception as e:
        print(f"Error finding user metadata: {e}")
        raise HTTPException(status_code=404, detail="User not found")

@admin_router.put("/user/diagnose/{email}")
async def update_user_diagnose(
    email: str, 
    diagnose_data: Dict[str, str], 
    session_token: str
):
    """Update user diagnose information"""
    verify_session(session_token)
    
    # Find and update user in data
    user_data = next((user for user in HARDCODED_CSV_DATA if user["email"] == email), None)
    if not user_data:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Update diagnose fields with safe defaults
    if "diagnose_pdn_code" in diagnose_data:
        user_data["diagnose_pdn_code"] = diagnose_data["diagnose_pdn_code"]
    elif "diagnose_pdn_code" not in user_data:
        user_data["diagnose_pdn_code"] = user_data.get("pdn_code", "")
    
    if "diagnose_comments" in diagnose_data:
        user_data["diagnose_comments"] = diagnose_data["diagnose_comments"]
    elif "diagnose_comments" not in user_data:
        user_data["diagnose_comments"] = ""
    
    return {
        "success": True,
        "message": "Diagnose updated successfully",
        "user": user_data
    }

@admin_router.post("/user/send_email/{email}")
async def send_user_email(email: str, session_token: str):
    """Send PDN report email to user"""
    verify_session(session_token)
    
    try:
        # Load user answers
        user_answers = load_answers(email)
        if not user_answers:
            raise HTTPException(status_code=404, detail="User answers not found")
        
        # Calculate PDN code
        pdn_code = "E5"
        #pdn_code = calculate_pdn_code(user_answers)

        if not pdn_code:
            raise HTTPException(status_code=400, detail="Could not calculate PDN code")
        
        # Load report data
        report_data = load_pdn_report(pdn_code)
        if not report_data:
            raise HTTPException(status_code=400, detail="Could not load PDN report")
        
        # Send email
        email_sent = send_email(user_answers, pdn_code, report_data)
        
        if email_sent:
            return {
                "success": True,
                "message": f"Email sent successfully to {email}",
                "pdn_code": pdn_code
            }
        else:
            raise HTTPException(status_code=500, detail="Failed to send email")
            
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error sending email: {str(e)}")

# Replace the Flask blueprint route with FastAPI route
@admin_router.get("/audio/{file_path:path}")
async def serve_audio(file_path: str, session_token: str):
    """Serve audio files with authentication."""
    print(f"Audio request for file_path: {file_path}")  # Debug log
    print(f"Session token: {session_token}")  # Debug log
    
    if not session_token:
        print("No session token provided")  # Debug log
        raise HTTPException(status_code=401, detail="No session token provided")
    
    # Verify session
    verify_session(session_token)
    
    # Construct the full path to the audio file
    audio_path = Path('saved_results') / file_path
    print(f"Looking for file at: {audio_path.absolute()}")  # Debug log
    
    # Security check: ensure the path is within the allowed directory
    try:
        audio_path = audio_path.resolve()
        saved_results_path = Path('saved_results').resolve()
        if not str(audio_path).startswith(str(saved_results_path)):
            print("Path traversal attempt detected")  # Debug log
            raise HTTPException(status_code=403, detail="Access denied")
    except Exception as e:
        print(f"Path resolution error: {e}")  # Debug log
        raise HTTPException(status_code=400, detail="Invalid file path")
    
    # Check if file exists
    if not audio_path.exists():
        print(f"File not found: {audio_path}")  # Debug log
        raise HTTPException(status_code=404, detail="Audio file not found")
    
    print(f"File found, serving: {audio_path}")  # Debug log
    
    try:
        # Use FastAPI's FileResponse instead of Flask's send_file
        return FileResponse(
            path=audio_path,
            media_type='audio/wav',
            filename=audio_path.name
        )
    except Exception as e:
        print(f"Error serving audio file: {e}")  # Debug log
        raise HTTPException(status_code=500, detail="Error serving audio file")

def is_valid_session(session_token):
    """Check if session token is valid."""
    # Implement your session validation logic here
    # This should match the logic you use in other admin routes
    return session_token in admin_sessions  # Replace with your actual session validation
