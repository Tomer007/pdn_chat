import json
from pathlib import Path

import yaml
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from starlette.middleware.sessions import SessionMiddleware
from fastapi.middleware.cors import CORSMiddleware
import logging
from fastapi.openapi.docs import get_swagger_ui_html
from fastapi.openapi.utils import get_openapi

from app.api.routes import router as api_router

app = FastAPI(
    title="PDN Diagnosis System API",
    description="API for the PDN Diagnosis System",
    version="1.0.0",
    docs_url="/docs",  # Enable Swagger UI
    redoc_url="/redoc"  # Enable ReDoc
)
app.add_middleware(SessionMiddleware, secret_key="your-very-secret-key")

# Mount static folder
app.mount("/static", StaticFiles(directory="app/static"), name="static")

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

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

@app.middleware("http")
async def log_requests(request, call_next):
    logger.info(f"Request: {request.method} {request.url}")
    response = await call_next(request)
    logger.info(f"Response: {response.status_code}")
    return response

# Custom OpenAPI schema
def custom_openapi():
    if app.openapi_schema:
        return app.openapi_schema
    
    openapi_schema = get_openapi(
        title="PDN Diagnosis System API",
        version="1.0.0",
        description="API for the PDN Diagnosis System",
        routes=app.routes,
    )
    
    app.openapi_schema = openapi_schema
    return app.openapi_schema

app.openapi = custom_openapi

# Custom docs endpoint
@app.get("/docs", include_in_schema=False)
async def custom_swagger_ui_html():
    return get_swagger_ui_html(
        openapi_url=app.openapi_url,
        title=app.title + " - Swagger UI",
        oauth2_redirect_url=app.swagger_ui_oauth2_redirect_url,
        swagger_js_url="/static/swagger-ui-bundle.js",
        swagger_css_url="/static/swagger-ui.css",
    )
