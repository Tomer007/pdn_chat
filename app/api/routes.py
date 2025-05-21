import json
import yaml
from collections import Counter
from pathlib import Path
from typing import Dict

from fastapi import APIRouter, Request, Response, HTTPException
from fastapi.responses import HTMLResponse, JSONResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel, EmailStr
from app.utils.answer_storage import load_answers, clear_answers, save_user_metadata


from app.models.user import UserInfoRequest
from app.utils.user_manager import load_all_users_from_db, save_user_to_db
from app.utils.questionnaire import get_question, submit_answer
from app.utils.pdn_calculator import calculate_pdn_code
from app.utils.json_saver import save_user_results
from app.utils.answer_storage import save_answer
from app.utils.report_generator import load_pdn_report



router = APIRouter()
templates = Jinja2Templates(directory="app/templates")

# Temporary dictionary to store user answers in memory
user_answers: Dict[int, str] = {}

# Pydantic models for request validation
class StartRequest(BaseModel):
    name: str
    email: EmailStr

class AnswerRequest(BaseModel):
    question_number: int
    selected_option_code: str

class LoginRequest(BaseModel):
    email: EmailStr
    password: str

# -------------------------------
# API Endpoints
# -------------------------------

@router.get("/", response_class=HTMLResponse)
async def home(request: Request):
    return templates.TemplateResponse("login.html", {"request": request})

@router.get("/chat", response_class=HTMLResponse)
async def chat(request: Request):
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

@router.get("/user_info", response_class=HTMLResponse)
async def user_info_page(request: Request):
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

@router.post("/user_info")
async def save_user_info_api(request: Request):
    try:
        user_data = await request.json()
        email = user_data.get('email', 'anonymous')
        save_user_metadata(user_data, email)
        return {"message": "User information saved successfully."}
    except json.JSONDecodeError:
        raise HTTPException(status_code=400, detail="Invalid JSON data")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/login", response_class=HTMLResponse)
async def login_page(request: Request):
    return templates.TemplateResponse("login.html", {
        "request": request,
        "include_menu": True
    })

@router.post("/login")
async def login_user(request: Request, login_data: LoginRequest):
    if login_data.password == "1":
        request.session["email"] = login_data.email
        return {"message": "Login successful"}
    else:
        raise HTTPException(status_code=401, detail="Invalid credentials")

@router.post("/start")
async def start_user(start_request: StartRequest):
    user_data = {
        "name": start_request.name,
        "email": start_request.email
    }
    return {"message": "User registered successfully!", "user": user_data}

@router.get("/questionnaire/{question_number}")
async def get_question_route(request: Request, question_number: int):
    questions = request.app.state.questions
    return get_question(question_number, questions)


@router.post("/answer")
async def submit_answer_route(request: Request):
    data = await request.json()
    question_number = data.get("question_number")
    selected_option_code = data.get("selected_option_code")
    selected_option_text = data.get("selected_option_text")
    ranking = data.get("ranking") 
    email = request.session.get("email", "anonymous")

    # Get questions from app state
    questions = request.app.state.questions
    
    
    # Save answer with ranking if applicable
    save_answer(email, question_number, {
        "code": selected_option_code,
        "text": selected_option_text,
        "ranking": ranking 
    })
    
    # Pass all parameters to submit_answer
    result = submit_answer(
        question_number=question_number,
        selected_option_code=selected_option_code,
        selected_option_text=selected_option_text,
        ranking=ranking,
        email=email,
        questions=questions
    )
    
    # If this was the last question, include a flag
    if result.get("is_last", False):
        return {
            "message": "All questions completed",
            "is_last": True,
            "redirect_to": "/result"
        }
    
    return result

@router.post("/submit_user_info")
async def submit_user_info(request: Request):
    try:
        user_data = await request.json()
        request.session["user_data"] = user_data
        return {"status": "success"}
    except json.JSONDecodeError:
        raise HTTPException(status_code=400, detail="Invalid JSON data")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/pdn_report", response_class=HTMLResponse)
async def pdn_report(request: Request):
    return templates.TemplateResponse("pdn_report.html", {
        "request": request,
        "include_menu": True
    })

@router.get("/get_report_data")
async def get_report_data(request: Request): 
    print("get_report_data")
    email = request.session.get("email", "anonymous")
    # pdn_code = request.session.get("pdn_code", "ERROR")
    # if pdn_code == "ERROR":
    pdn_code = calculate_pdn_code(user_answers)

    # Load user metadata and answers
    user_data = load_answers(email)
    metadata = user_data.get('metadata', {})
    
    # Load the report data for the PDN code
    report_data = load_pdn_report(pdn_code)
    
    # Return the complete report data
    return {
        "metadata": metadata,
        "results": {
            "pdn_code": pdn_code,
            **report_data  # Include all the report sections
        }
    }

@router.post("/complete_questionnaire")
async def complete_questionnaire(request: Request):
    print("complete_questionnaire")
    email = request.session.get("email", "anonymous")
    user_answers = load_answers(email)
    
    if not user_answers:
        return {"error": "No answers found for this user"}
    
    # Calculate PDN code using the calculator
    pdn_code = calculate_pdn_code(user_answers)
    
    # Store the PDN code in the session
    request.session["pdn_code"] = pdn_code
    print("pdn_code", pdn_code)
    return {"message": "Questionnaire completed successfully", "pdn_code": pdn_code}

