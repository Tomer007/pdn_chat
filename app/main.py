from app.pdn_admin.admin_routes import pdn_admin_bp
from app.pdn_chat_ai.chat_routes import pdn_chat_ai_bp
from app.pdn_diagnose.diagnosis_routes import pdn_diagnose_bp
import os

app = Flask(__name__, 
            static_folder="static",
            template_folder="templates")

app.secret_key = "your-very-secret-key"  # הוסף את השורה הזו

# Register blueprints
app.register_blueprint(pdn_admin_bp, url_prefix='/pdn-admin')
app.register_blueprint(pdn_chat_ai_bp, url_prefix='/pdn-chat-ai')
app.register_blueprint(pdn_diagnose_bp, url_prefix='/pdn-diagnose')

@app.route("/")
def root():
    return {"message": "PDN Chat API"}
