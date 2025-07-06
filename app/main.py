from flask import Flask, send_from_directory

app = Flask(__name__, 
            static_folder="static",
            template_folder="templates")

# Import your routes
# from app.pdn_admin import admin_routes
# from app.pdn_chat_ai import chat_routes
# from app.pdn_diagnose import diagnosis_routes

# app.register_blueprint(admin_routes.pdn_admin_bp)
# app.register_blueprint(chat_routes.pdn_chat_ai_bp)
# app.register_blueprint(diagnosis_routes.pdn_diagnose_bp)

@app.route("/")
def root():
    return {"message": "PDN Chat API"} 