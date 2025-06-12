import json
import logging
from collections import defaultdict
from typing import Dict, Optional

from fastapi import APIRouter, Request, HTTPException
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel, EmailStr, Field

from app.utils.answer_storage import load_answers, save_user_metadata
from app.utils.answer_storage import save_answer
from app.utils.email_sender import send_email
from app.utils.pdn_calculator import calculate_pdn_code
from app.utils.questionnaire import get_question
from app.utils.report_generator import load_pdn_report
#from app.utils.store_pdn_report_in_Firebase import store_pdn_report_in_Firebase

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

router = APIRouter()
templates = Jinja2Templates(directory="app/templates")

# Temporary dictionary to store user answers in memory
user_answers: Dict[int, str] = {}

# Add to each endpoint
api_usage = defaultdict(int)


# Pydantic models for request validation
class StartRequest(BaseModel):
    name: str = Field(..., description="User's full name")
    email: EmailStr = Field(..., description="User's email address")

    class Config:
        schema_extra = {
            "example": {
                "name": "John Doe",
                "email": "john@example.com"
            }
        }


class AnswerRequest(BaseModel):
    question_number: int = Field(..., description="The question number being answered")
    selected_option_code: str = Field(..., description="The code of the selected option")
    ranking: Optional[Dict[str, int]] = Field(None, description="Ranking of options if applicable")

    class Config:
        schema_extra = {
            "example": {
                "question_number": 1,
                "selected_option_code": "A",
                "ranking": {"A": 1, "B": 2, "C": 3}
            }
        }


class LoginRequest(BaseModel):  
    email: EmailStr = Field(..., description="User's email address")
    password: str = Field(..., description="User's password")

    class Config:
        json_schema_extra = {
            "example": {
                "email": "john@example.com",
                "password": "password123"
            }
        }


# -------------------------------
# API Endpoints
# -------------------------------

@router.get("/", response_class=HTMLResponse, tags=["Pages"])
async def home(request: Request):
    """
    Home page endpoint.
    
    Returns the login page HTML template.
    """
    logger.debug("GET / called")
    api_usage["home"] += 1
    logger.debug(f"API Usage: {dict(api_usage)}")
    logger.info("Request: %s %s", request.method, request.url)
    logger.info("Response: %s", 200)
    logger.info("User answers: %s", user_answers)
    return templates.TemplateResponse("login.html", {"request": request})


@router.get("/chat", response_class=HTMLResponse, tags=["Pages"])
async def chat(request: Request):
    """
    Chat interface endpoint.
    
    Returns the chat page HTML template with chatbot configuration.
    """
    logger.debug("GET /chat called")
    api_usage["chat"] += 1
    logger.debug(f"API Usage: {dict(api_usage)}")
    logger.info("Request: %s %s", request.method, request.url)
    logger.info("Response: %s", 200)
    logger.info("User answers: %s", user_answers)
    config = request.app.state.config
    email = request.session.get("email", None)
    return templates.TemplateResponse(
        "chat.html",
        {
            "request": request,
            "welcome_message": config["chatbots"]["chatbot_PDN"]["welcome_message"],
            "email": email,
            "include_menu": True
        }
    )


@router.get("/user_info", response_class=HTMLResponse, tags=["User"])
async def user_info_page(request: Request):
    """
    User information page endpoint.
    
    Returns the user information form HTML template.
    """
    logger.debug("GET /user_info called")
    api_usage["user_info"] += 1
    logger.debug(f"API Usage: {dict(api_usage)}")
    logger.info("Request: %s %s", request.method, request.url)
    logger.info("Response: %s", 200)
    logger.info("User answers: %s", user_answers)
    email = request.session.get("email", "anonymous")
    # Load questions.json to get the instructions
    with open("app/data/questions.json", "r", encoding="utf-8") as f:
        questions = json.load(f)
    personal_instructions = questions["phases"]["PersonalDetails"]["instructions"]
    return templates.TemplateResponse("user_form.html", {
        "request": request,
        "include_menu": True,
        "email": email,
        "personal_instructions": personal_instructions
    })


@router.post("/user_info", tags=["User"])
async def save_user_info_api(request: Request):
    """
    Save user information endpoint.
    
    Saves user metadata and updates session data.
    """
    logger.debug("POST /user_info called")
    api_usage["save_user_info"] += 1
    logger.debug(f"API Usage: {dict(api_usage)}")
    logger.info("Request: %s %s", request.method, request.url)
    logger.info("Response: %s", 200)
    try:
        user_data = await request.json()
        email = user_data.get('email', 'anonymous')
        save_user_metadata(user_data, email)
        request.session["user_data"] = user_data
        return {"message": "User information saved successfully."}
    except json.JSONDecodeError:
        raise HTTPException(status_code=400, detail="Invalid JSON data")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/login")
async def login_user(request: Request, login_data: LoginRequest):
    logger.debug("POST /login called")
    api_usage["login"] += 1
    logger.debug(f"API Usage: {dict(api_usage)}")
    logger.info("Request: %s %s", request.method, request.url)
    logger.info("Response: %s", 200)
    if login_data.password == "pdn":
        request.session["email"] = login_data.email
        return {"message": "Login successful"}
    else:
        raise HTTPException(status_code=401, detail="Invalid credentials")


@router.get("/questionnaire/{question_number}")
async def get_question_route(request: Request, question_number: int):
    logger.debug(f"GET /questionnaire/{question_number} called")
    api_usage[f"get_question_{question_number}"] += 1
    logger.debug(f"API Usage: {dict(api_usage)}")
    logger.info("Request: %s %s", request.method, request.url)
    logger.info("Response: %s", 200)
    questions = request.app.state.questions
    return get_question(question_number, questions)


@router.post("/answer", tags=["Questionnaire"])
async def submit_answer_route(request: Request):
    """
    Submit answer endpoint.
    
    Saves user's answer for a specific question.
    """
    api_usage["submit_answer"] += 1
    logger.debug(f"API Usage: {dict(api_usage)}")
   
    data = await request.json()
    question = data.get("question")
    question_number = data.get("question_number")
    selected_option_code = data.get("selected_option_code")
    selected_option_text = data.get("selected_option_text")
    ranking = data.get("ranking")
    email = request.session.get("email", "anonymous")

    # Save answer with ranking if applicable
    save_answer(email, question_number, {
        "code": selected_option_code,
        "answer": selected_option_text,
        "ranking": ranking,
        "question": question
    })
    return {"message": "Answer saved successfully"}


@router.post("/complete_questionnaire")
async def complete_questionnaire(request: Request):
    logger.debug("POST /complete_questionnaire called")
    api_usage["complete_questionnaire"] += 1
    logger.debug(f"API Usage: {dict(api_usage)}")
    logger.info("Request: %s %s", request.method, request.url)
    logger.info("Response: %s", 200)
    email = request.session.get("email", "anonymous")
    user_answers = load_answers(email)

    if not user_answers:
        raise HTTPException(status_code=404, detail="No answers found for this user")

    return {
        "message": "Questionnaire completed successfully",
    }


@router.get("/pdn_report", response_class=HTMLResponse)
async def pdn_report(request: Request):
    logger.debug("GET /pdn_report called")
    api_usage["pdn_report"] += 1
    logger.debug(f"API Usage: {dict(api_usage)}")
    logger.info("Request: %s %s", request.method, request.url)
    logger.info("Response: %s", 200)
    return templates.TemplateResponse("pdn_report.html", {
        "request": request,
        "include_menu": True
    })


@router.get("/get_report_data")
async def get_report_data(request: Request):
    logger.debug("GET /get_report_data called")
    api_usage["get_report_data"] += 1
    logger.debug(f"API Usage: {dict(api_usage)}")
    logger.info("Request: %s %s", request.method, request.url)
    logger.info("Response: %s", 200)
    email = request.session.get("email", "anonymous")
    user_answers = load_answers(email)
    
    if not user_answers:
        raise HTTPException(status_code=404, detail="No answers found for this user")
        
    metadata = user_answers.get('metadata', {})
    pdn_code = calculate_pdn_code(user_answers)
    
    if not pdn_code:
        raise HTTPException(status_code=400, detail="Could not calculate PDN code")

    report_data = load_pdn_report(pdn_code)

    # Save the report data to the Firebase Firestore database
    #store_pdn_report_in_Firebase(user_answers, pdn_code, report_data)
    
    # Send email report
    email_sent = send_email(user_answers, pdn_code, report_data)
    if not email_sent:
        logger.warning("Failed to send email report")
    
    return {
        "metadata": metadata,
        "results": {
            "pdn_code": pdn_code,
            **report_data
        },
        "email_sent": email_sent
    }

@router.get('/get_user_name')
def get_user_name(request: Request):
    # Get the user's name from your session or database
    #TODO ADD user name
    email = request.session.get("email", "anonymous")
    return {"name": email}
