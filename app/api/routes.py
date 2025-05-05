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
        return {"message": "Invalid credentials"}

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


# @router.get("/result")
# async def get_result_route(request: Request):
    email = request.session.get("email", "anonymous")
    questions = request.app.state.questions
    user_answers = load_answers(email)

    if not user_answers:
        raise HTTPException(status_code=400, detail="No answers found")

    result = get_result(email)

    questions_data = []
    for q_num, answer_code in user_answers.items():
        question = questions.get(str(q_num))
        if question:
            questions_data.append({
                "question_number": int(q_num),
                "question_text": question["text"],
                "answer_label": next((opt["text"] for opt in question["options"] 
                                if opt["code"] == answer_code["code"]), ""),
                "answer_code": answer_code["code"]
            })

    save_user_results(email, questions_data)
    clear_answers(email)  # Clear answers after saving results

    return result





    trait_scores = {"A": 0, "T": 0, "P": 0, "E": 0}
    energy_scores = {"D": 0, "S": 0, "F": 0}
    user_answers = load_answers(email)

    for q_num, code in user_answers.items():
        if code == "AP":
            trait_scores["A"] += 1
        elif code == "ET":
            trait_scores["T"] += 1
        elif code == "AE":
            trait_scores["E"] += 1
        elif code == "TP":
            trait_scores["P"] += 1

    primary_trait = max(trait_scores, key=trait_scores.get)
    dominant_energy = "D"  # (לשדרוג בעתיד)

    pdn_matrix = {
        "P": {"D": "P10", "S": "P2", "F": "P6"},
        "E": {"D": "E1", "S": "E5", "F": "E9"},
        "A": {"D": "A7", "S": "A11", "F": "A3"},
        "T": {"D": "T4", "S": "T8", "F": "T12"}
    }

    pdn_code = pdn_matrix.get(primary_trait, {}).get(dominant_energy, "NA")

    user = User(
        name=name,
        email=email,
        pdn_code=pdn_code,
        trait=primary_trait,
        energy=dominant_energy,
        answers=str(user_answers)
    )

    save_user_to_db(user)

    return {
        "message": "User saved successfully.",
        "pdn_code": pdn_code,
        "trait": primary_trait,
        "energy": dominant_energy
    }

@router.get("/admin/users")
async def get_all_users():
    users = load_all_users_from_db()
    return users

@router.get("/admin/stats")
async def get_admin_stats():
    users = load_all_users_from_db()

    trait_counter = Counter()
    energy_counter = Counter()

    for user in users:
        if user.trait:
            trait_counter[user.trait] += 1
        if user.energy:
            energy_counter[user.energy] += 1

    return {
        "trait_distribution": dict(trait_counter),
        "energy_distribution": dict(energy_counter),
        "total_users": len(users)
    }

@router.get("/admin/dashboard", response_class=HTMLResponse)
async def admin_dashboard(request: Request):
    return templates.TemplateResponse("admin_dashboard.html", {
        "request": request,
        "include_menu": True
    })

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

