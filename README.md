# PDN (Personality Diagnostic Navigator) System

A comprehensive personality assessment system that helps users discover their PDN code through an interactive questionnaire.

## Features

- 🎯 Interactive questionnaire with multiple stages
- 💫 Modern, responsive UI with smooth animations
- 🔍 Dynamic stage instructions with visual feedback
- 📊 Real-time answer tracking and analysis
- 📝 Detailed personality report generation
- 🔒 Secure user data management

## Project Structure

```
.
├── app/
│   ├── api/          # API routes and endpoints
│   ├── models/       # Pydantic models for data validation
│   ├── templates/    # HTML templates with modern UI
│   ├── static/       # Static files (CSS, JS, Images)
│   ├── utils/        # Helper functions and utilities
│   └── data/         # Questionnaire data and configurations
├── saved_results/    # User responses and reports
├── tests/           # Unit tests
└── requirements.txt # Project dependencies
```

## Key Components

### Questionnaire Stages
1. **Part A**: Behavioral Assessment
   - Evaluates AP (Impulsive, Spontaneous) vs ET (Planned, Organized)
   - Analyzes AE (Assertive, Expressive) vs TP (Reserved, Agreeable)

2. **Part B**: Deep Behavioral Analysis
   - Examines behavioral patterns in various situations
   - Provides detailed personality insights

3. **Part C**: Emotional and Social Assessment
   - Evaluates emotional and social interaction patterns
   - Assesses response to social challenges

### User Interface
- Modern glass-morphism design
- Smooth animations and transitions
- Responsive layout for all devices
- RTL support for Hebrew language
- Interactive elements with visual feedback

## Getting Started

1. Clone the repository
2. Create a virtual environment:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```
3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
4. Run the application:
   ```bash
   uvicorn app.main:app --reload
   ```
5. Visit http://localhost:8000/

## Development

- The application uses FastAPI for the backend
- Frontend is built with HTML, Tailwind CSS, and JavaScript
- User data is stored securely in JSON files
- The system supports multiple questionnaire stages with dynamic instructions

## Recent Updates

- Added dynamic stage instructions with emojis
- Implemented modern UI with glass-morphism effects
- Enhanced user experience with smooth animations
- Improved questionnaire flow and navigation
- Added secure answer storage and analysis

## License

This project is licensed under the MIT License - see the LICENSE file for details.
