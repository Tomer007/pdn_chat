from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from starlette.requests import Request

# Import your routers (make sure these use FastAPI's APIRouter)
from app.pdn_admin.admin_routes import router as admin_router
from app.pdn_chat_ai.chat_routes import router as chat_ai_router
from app.pdn_diagnose.diagnosis_routes import router as diagnose_router
 
app = FastAPI()

# Mount static files
app.mount("/static", StaticFiles(directory="app/static"), name="static")

# Set up templates
templates = Jinja2Templates(directory="app/pdn_admin/templates")

# Include routers
app.include_router(admin_router, prefix="/pdn-admin")
app.include_router(chat_ai_router, prefix="/pdn-chat-ai")
app.include_router(diagnose_router, prefix="/pdn-diagnose")

@app.get("/", response_class=HTMLResponse)
async def root(request: Request):
    return {"message": "PDN Chat API"} 