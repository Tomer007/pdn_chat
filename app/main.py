from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

app = FastAPI(title="PDN Chat")

# Mount static files
app.mount("/static", StaticFiles(directory="app/static"), name="static")

# Import your routes
# from app.pdn_admin import admin_routes
# from app.pdn_chat_ai import chat_routes
# from app.pdn_diagnose import diagnosis_routes

# app.include_router(admin_routes.router)
# app.include_router(chat_routes.router)
# app.include_router(diagnosis_routes.router)

@app.get("/")
async def root():
    return {"message": "PDN Chat API"} 