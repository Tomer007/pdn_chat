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
      diagnose_login.html
      user_form.html
      chat.html
      pdn_report.html
    static/
    ...
  pdn_admin/
    admin_routes.py
    admin_api.py
    audio_routes.py
    templates/
      admin_login.html      # Separate login page
      admin_dashboard.html  # Pure dashboard (no login modal)
    ...
  pdn_chat_ai/
    chat_routes.py
    templates/
    ...
  utils/
    answer_storage.py
    pdn_calculator.py
    report_generator.py
    csv_metadata_handler.py
    email_sender.py
    questionnaire.py
    ...
  data/
    questions.json
    config.yaml
    pdn_reports.json
    ...
  static/                   # Centralized static files
    css/
    js/
    images/
    ...
  templates/partials/       # Shared Jinja partials (footer)
```

## Tech Stack
- Python 3.x
- Flask
- JavaScript (frontend logic)
- Tailwind CSS (via CDN for development)
- HTML2PDF.js (for PDF generation)
 
## Shared Partials
- Footer: `{% include 'partials/footer.html' %}` is used in diagnose, admin, and chat templates for a consistent, card-styled footer within `container mx-auto p-6 max-w-4xl`.

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
- `GET /pdn-admin/` - Admin login page (separate from dashboard)
- `GET /pdn-admin/dashboard` - Admin dashboard (requires authentication)
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
- `POST /pdn-admin/api/save-audio` - Save user audio file

### PDN Chat AI Module (`/pdn-chat-ai`)
**Chat Interface:**
- `GET /pdn-chat-ai/` - Chat interface page (includes questionnaire functionality)
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
- Users are redirected to `/pdn-diagnose/pdn_report` after completion

## Admin Dashboard Features
- **Separate Login Page:** Clean login interface at `/pdn-admin/`
- **Pure Dashboard:** Dashboard at `/pdn-admin/dashboard` without embedded login
- **User Management:** View, edit, and manage user data
- **Audio Management:** Upload and manage user voice recordings
- **Email System:** Send PDN reports to users
- **Data Export:** Download metadata as CSV
- **Visual Indicators:** Red highlighting for users with inconsistent PDN codes

## Audio Upload
- Audio is uploaded via `/pdn-admin/api/save-audio`
- Audio files are saved under `saved_results/<user>/<filename>.wav`
- Supported in both chat interface and admin dashboard

## Running the App
1. Activate your virtual environment:
   ```bash
   source venv/bin/activate  # On macOS/Linux
   # or
   venv\Scripts\activate     # On Windows
   ```

2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

3. Run the app:
   ```bash
   python app.py
   ```

4. Access the application:
   - Main app: `http://127.0.0.1:8001/`
   - Admin login: `http://127.0.0.1:8001/pdn-admin/`
   - Admin dashboard: `http://127.0.0.1:8001/pdn-admin/dashboard`
   - Chat interface: `http://127.0.0.1:8001/pdn-chat-ai/`
   - Diagnose interface: `http://127.0.0.1:8001/pdn-diagnose/`

## Configuration
- Admin password: Set in `config.py` or environment variable `ADMIN_PASSWORD` (default: 'pdn')
- Session management: File-based sessions (configurable)
- Static files: Centralized in `app/static/`

## Logs & Debugging
- Logs are written to `logs/app.log`
- To tail logs: `tail -f logs/app.log`
- Check logs for import errors, endpoint errors, or calculation issues

## Troubleshooting

### Common Issues
- **404 Errors:** Ensure you're using the correct URL prefixes (`/pdn-admin/`, `/pdn-diagnose/`, `/pdn-chat-ai/`)
- **Static File Issues:** Static files are now centralized in `app/static/`
- **Admin Access:** Use `/pdn-admin/` for login, `/pdn-admin/dashboard` for the dashboard
- **Session Issues:** Clear browser cache or restart the application

### Error Resolution
- **400 Errors on Answer Submission:** Check that answers include `selected_option_code` or `ranking` as appropriate
- **400 Errors on Questionnaire Completion:** Verify answer structure matches expected format
- **Import Errors:** Ensure all dependencies are installed and virtual environment is activated
- **PDN Report Loading:** Ensure the correct endpoint `/pdn-diagnose/get_report_data` is being called

## Recent Updates (Latest)
- **Unified Footer:** Added shared footer partials and included across pages (`templates/partials/footer.html`)
- **Report UI Refresh:** Modern blue theme aligned with chat; personalized header with user name
- **Questionnaire UX:** Added progress bar; re-record buttons for voice prompts; validation for duration
- **Header Consistency:** Standardized gradient header styling across chat, diagnose, report
- **Centralized Static Files:** Moved assets to `app/static/`
- **Refactored Admin Interface:** Separated login and dashboard into distinct pages
- **Fixed PDN Report:** Ensured data loads from `/pdn-diagnose/get_report_data`

## Known Issues
- **Tailwind CSS CDN Warnings:** In development, Tailwind is loaded via CDN which may show warnings
- **Session Management:** Currently uses file-based sessions; consider Redis for production
- **Admin Authentication:** Simple password-based authentication; consider implementing proper session management for production

## Contributing
- Fork the repo and create a feature branch
- Submit pull requests with clear descriptions
- Report issues via GitHub Issues

## Test Coverage
- Tests are located in the `tests/` directory
- Run tests with `pytest` or your preferred test runner

## Security Notes
- Admin password should be changed in production
- Consider implementing proper session management
- Review and secure file upload endpoints
- Implement rate limiting for production use