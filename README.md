# PDN Chat Application

## Overview
PDN Chat is a modular Flask application for administering, diagnosing, and interacting with users through a structured questionnaire and chat interface. The app is organized into three main modules:

- `pdn_diagnose`: User questionnaire, answer submission, and PDN code calculation
- `pdn_admin`: Admin dashboard, audio upload, and management
- `pdn_chat_ai`: Chat interface and AI interaction

## Project Structure
```
app/
  pdn_diagnose/
    diagnosis_routes.py
    templates/
    static/
    ...
  pdn_admin/
    admin_routes.py
    audio_routes.py
    ...
  pdn_chat_ai/
    chat_routes.py
    ...
  utils/
    answer_storage.py
    pdn_calculator.py
    ...
  data/
    questions.json
    ...
```

## Tech Stack
- Python 3.x
- Flask
- JavaScript (frontend logic)
- Tailwind CSS (via CDN for development; see Known Issues)

## URL Structure & Endpoints

### Root Endpoint
- **Home:** `GET /` - Welcome message with module links

### PDN Diagnose Module (`/pdn-diagnose`)
**User Interface:**
- `GET /pdn-diagnose/` - Login page
- `GET /pdn-diagnose/user_info` - User information form
- `POST /pdn-diagnose/user_info` - Save user information
- `POST /pdn-diagnose/login` - User login

**Questionnaire:**
- `GET /pdn-diagnose/questionnaire/<question_number>` - Get specific question
- `POST /pdn-diagnose/answer` - Submit answer for a question
- `POST /pdn-diagnose/complete_questionnaire` - Complete questionnaire and calculate PDN code

**Reports & Results:**
- `GET /pdn-diagnose/pdn_report` - View PDN report
- `GET /pdn-diagnose/get_report_data` - Get report data as JSON
- `GET /pdn-diagnose/get_user_name` - Get user name
- `POST /pdn-diagnose/send_email` - Send PDN report via email

### PDN Admin Module (`/pdn-admin`)
**Admin Interface:**
- `GET /pdn-admin/` - Admin dashboard page
- `POST /pdn-admin/login` - Admin login
- `GET /pdn-admin/logout` - Admin logout

**Data Management:**
- `GET /pdn-admin/metadata` - Get metadata CSV data
- `GET /pdn-admin/metadata/csv` - Download metadata as CSV
- `GET /pdn-admin/user/questionnaire/<email>` - Get user questionnaire data
- `GET /pdn-admin/user/voice/<email>` - Get user voice recording URL
- `PUT /pdn-admin/user/diagnose/<email>` - Update user diagnose information
- `POST /pdn-admin/user/send_email/<email>` - Send email to user

**Audio Management:**
- `GET /pdn-admin/audio/<path:file_path>` - Serve audio files

**Admin API Endpoints:**
- `POST /pdn-admin/api/login` - Admin API login
- `GET /pdn-admin/api/logout` - Admin API logout
- `GET /pdn-admin/api/metadata` - Get metadata via API
- `GET /pdn-admin/api/metadata/csv` - Download metadata CSV via API
- `GET /pdn-admin/api/user/questionnaire/<email>` - Get user questionnaire via API
- `GET /pdn-admin/api/user/voice/<email>` - Get user voice via API
- `PUT /pdn-admin/api/user/diagnose/<email>` - Update user diagnose via API
- `POST /pdn-admin/api/user/send_email/<email>` - Send user email via API
- `GET /pdn-admin/api/audio/<path:file_path>` - Serve audio files via API

**Audio Upload:**
- `POST /pdn-admin/api/save-audio` - Save user audio file
- `GET /pdn-admin/api/audio/<username>` - Get user audio files

### PDN Chat AI Module (`/pdn-chat-ai`)
**Chat Interface:**
- `GET /pdn-chat-ai/` - Chat interface page
- `POST /pdn-chat-ai/chat` - Handle chat messages
- `GET /pdn-chat-ai/context` - Get user context for chat
- `GET /pdn-chat-ai/history` - Get chat history
- `POST /pdn-chat-ai/clear_history` - Clear chat history
- `GET /pdn-chat-ai/settings` - Get chat settings
- `PUT /pdn-chat-ai/settings` - Update chat settings

### Static Files
- `GET /static/<path:filename>` - Serve static files (CSS, JS, images)

## Questionnaire Flow
- 65 questions, divided into several parts (A-F)
- Questions 1-26: Single-choice (code in `selected_option_code`)
- Questions 27-65: Ranking or other types (data in `ranking`)
- Answers are saved per user and used for PDN code calculation
- Completion triggers PDN code calculation and report generation

## Audio Upload
- Audio is uploaded via `/pdn-admin/api/save-audio` (used in chat and admin dashboard)
- Audio files are saved under `saved_results/<user>/<filename>.wav`

## Running the App
- Activate your virtual environment
- Install dependencies: `pip install -r requirements.txt`
- Run the app: `python run.py` or `flask run` (ensure `FLASK_APP=app`)
- The app runs on `http://127.0.0.1:8001/` by default

## Logs & Debugging
- Logs are written to `app.log` (and/or `logs/app.log`)
- To tail logs: `tail -f app.log` or `tail -f logs/app.log`
- Check logs for import errors, endpoint errors, or calculation issues

## Troubleshooting
- **400 Errors on Answer Submission:** Check that answers include `selected_option_code` or `ranking` as appropriate
- **400 Errors on Questionnaire Completion:** Verify answer structure matches expected format
- **Import Errors:** Ensure all dependencies are installed and virtual environment is activated
- **Static File Issues:** Check that static files are in the correct location (`app/pdn_diagnose/static/`)

## Known Issues
- **Tailwind CSS CDN Warnings:** In development, Tailwind is loaded via CDN which may show warnings
- **Answer Structure:** Some endpoints expect `selected_option_code` while others expect `code` - this is being standardized
- **Session Management:** Currently uses file-based sessions; consider Redis for production

## Contributing
- Fork the repo and create a feature branch
- Submit pull requests with clear descriptions
- Report issues via GitHub Issues

## Test Coverage
- Tests are located in the `tests/` directory
- Run tests with `pytest` or your preferred test runner

## Recent Changes
- Modularized app structure under `app/`
- Fixed answer submission and questionnaire completion endpoints
- Added comprehensive error handling and logging
- Updated URL structure documentation