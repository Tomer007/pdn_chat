import json
import yaml
from collections import Counter
from pathlib import Path
from typing import Dict

from fastapi import APIRouter, Request, Response
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel, EmailStr
from app.utils.answer_storage import load_answers, clear_answers, save_user_metadata


from app.models.user import UserInfoRequest
from app.utils.user_manager import load_all_users_from_db, save_user_to_db
from app.utils.questionnaire import get_question, submit_answer  

from app.utils.json_saver import save_user_results
from app.utils.answer_storage import save_answer



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
    return templates.TemplateResponse("user_form.html", {
        "request": request,
        "include_menu": True
    })

@router.post("/user_info")
async def save_user_info_api(user_info: UserInfoRequest):
    # Save to JSON instead of SQLite
    user_data = user_info.dict()
    email = user_info.email or "anonymous"
    save_user_metadata(user_data, email)
    return {"message": "User information saved successfully."}

@router.get("/login", response_class=HTMLResponse)
async def login_page(request: Request):
    return templates.TemplateResponse("login.html", {
        "request": request,
        "include_menu": True
    })

@router.post("/login")
async def login_user(request: Request, login_data: LoginRequest):
    if login_data.password == "2":
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
    email = request.session.get("email", "anonymous")

    # Save answer
    save_answer(email, question_number, selected_option_code)
    
    # Get questions from app state
    questions = request.app.state.questions
    
    # Pass all parameters to submit_answer
    result = submit_answer(
        question_number=question_number,
        selected_option_code=selected_option_code,
        selected_option_text=selected_option_text,
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


@router.get("/result")
async def get_result_route(request: Request):
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


@router.post("/save_result")
async def save_result(name: str, email: EmailStr):


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
    # Get JSON data from request body
    user_data = await request.json()
    
    metadata = {
        'name': user_data['name'],
        'last_name': user_data['last_name'],
        'mother_language': user_data['mother_language'],
        'gender': user_data['gender'],
        'job_title': user_data['job_title'],
        'birth_year': user_data['birth_year']
    }
    
    # Save the metadata using the email from the session
    email = request.session.get("email", "anonymous")
    save_user_metadata(metadata, email)
    
    return JSONResponse(content={"message": "User information saved successfully"})

@router.get("/pdn_report", response_class=HTMLResponse)
async def pdn_report(request: Request):
    return templates.TemplateResponse("pdn_report.html", {
        "request": request,
        "include_menu": True
    })

@router.get("/get_report_data")
async def get_report_data(request: Request):
    email = request.session.get("email", "anonymous")
    
    # Load user metadata and answers
    user_data = load_answers(email)
    metadata = user_data.get('metadata', {})
    answers = user_data.get('answers', {})
    
    # Calculate PDN results (this is a placeholder - implement actual logic)
    results = {
        "pdn_code": "P10",
        "foundation": "P (נתינה והנאה)",
        "energy": "D (דינמית)",
        "type": "משפיע רגשי עם עשייה חזקה",
        "about_you": [
            "אתה אדם שמונע מתוך חיבור עמוק לרגשות ולמשמעות – אך בשונה מהטיפוס הזורם, אתה לא מסתפק בתחושות: אתה פועל, מזיז, יוזם. אתה מאמין בנתינה, אבל כזו שמשאירה חותם.",
            "האנרגיה שלך גבוהה ודינמית – אתה מחפש מרחבים לפעול, להוביל אנשים, ולהכניס ערך אמיתי לחיים של אחרים. אתה מוביל מתוך הקשבה, משפיע מתוך הלב, אך רוצה תוצאות."
        ],
        "strengths": [
            "אכפתיות אמיתית – עם יכולת ביצוע גבוהה",
            "הובלה רגשית – שמחברת אנשים למשמעות",
            "דחף פנימי לעזור, לקדם, להזיז",
            "כושר ריכוז גבוה כשיש ערך אישי",
            "יכולת לבטא רגש בצורה ישירה ומובנת"
        ],
        "challenges": [
            "מתעייף כשאין הערכה למה שאתה נותן",
            "נוטה לקחת אחריות גם כשזה לא שלך",
            "קושי לבקש עזרה – אתה רגיל להיות בצד הנותן",
            "רגיש מאוד למערכות יחסים \"חסרות לב\""
        ],
        "growth": [
            "מרחבים עם חיבור חברתי אמיתי (לא פורמלי)",
            "תפקידים שמאפשרים הובלה רגשית ולא רק משימתית",
            "שיח רגשי פתוח – בבית, בזוגיות, בעבודה",
            "שילוב בין עשייה לעומק – לא רק להפעיל, אלא גם להקשיב",
            "זמן שקט למילוי עצמי – להיטען רגשית מחדש"
        ],
        "suitable_fields": [
            "ניהול קהילתי, הדרכה חינוכית",
            "יזמות חברתית עם ערך מוסף",
            "תפקידי גישור, ליווי רגשי, תמיכה בצוותים",
            "הובלת קבוצות עם אווירה אישית וחמה"
        ],
        "summary": {
            "points": [
                "אתה לא רק אדם רגשי – אתה אדם שפועל מהרגש.",
                "אתה לא רק נותן – אתה נותן כדי ליצור שינוי.",
                "בעולם שצריך רגישות עם אומץ, אתה הנוכחות שמביאה את שניהם יחד."
            ],
            "quote": "אני נותן מעצמי כי אכפת לי, אבל גם לי מותר לעצור ולמלא את הלב מחדש."
        }
    }
    
    return {
        "metadata": metadata,
        "results": results
    }


