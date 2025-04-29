from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from app.api.routes import router as api_router
import yaml
import json
from pathlib import Path
from starlette.middleware.sessions import SessionMiddleware

app = FastAPI(
    title="PDN FastAPI App",
    description="PDN Diagnosis System",
    version="1.0.0",
)
app.add_middleware(SessionMiddleware, secret_key="your-very-secret-key")

# Mount static folder
app.mount("/static", StaticFiles(directory="app/static"), name="static")

# Global variables at startup
@app.on_event("startup")
async def startup_event():
    config_path = Path(__file__).resolve().parent.parent / "app/data" / "config.yaml"
    questions_path = Path(__file__).resolve().parent.parent / "app/data" / "questions.json"

    # Load config
    with open(config_path, "r", encoding="utf-8") as f:
        app.state.config = yaml.safe_load(f)

    # Load questions
    with open(questions_path, "r", encoding="utf-8") as f:
        app.state.questions = json.load(f)

# Include routers
app.include_router(api_router)

@app.get("/")
async def root():
    return {"message": "Welcome to PDN FastAPI!"}

def get_question(question_number: int, questions: dict):
    """
    Fetch a specific question by its number.
    Returns the question text and its options.
    """
    question = questions.get(str(question_number))
    if not question:
        return {"message": "No more questions."}

    return {
        "question_number": question_number,
        "question": question["text"],
        "options": question["options"]
    }
