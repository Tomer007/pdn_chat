# PDN Chat Application

A web-based application for PDN (Personality Diagnostic Network) assessment and analysis.

## Features

- User authentication and session management
- Interactive questionnaire system
- PDN code calculation and analysis
- Detailed personality reports
- Chat interface for user interaction
- API documentation with Swagger UI

## Tech Stack

- **Backend**: FastAPI (Python)
- **Frontend**: HTML, CSS, JavaScript
- **Templates**: Jinja2
- **Data Storage**: JSON/YAML
- **Authentication**: Session-based
- **Documentation**: Swagger UI/ReDoc

## Installation

1. Clone the repository:
```bash
git clone [your-repository-url]
cd pdn_chat
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Run the application:
```bash
uvicorn app.main:app --reload
```

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

This project is proprietary software. All rights reserved.

Copyright (c) 2024 Tomer Gur

This software and its contents are protected by copyright law. Unauthorized copying, modification, distribution, or use of this software, via any medium, is strictly prohibited.

For licensing inquiries, please contact:
- Email: tomergur@gmail.com

## Setup

1. Clone the repository:
```bash
git clone [repository-url]
cd pdn_chat
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Set up environment variables:
```bash
cp .env.example .env
# Edit .env with your configuration
```

4. Run the application:
```bash
uvicorn app.main:app --reload
```

## Usage

1. Run the application:
```bash
python app/main.py
```

2. Follow the questionnaire instructions
3. Get your PDN code and personality analysis

## PDN Codes

The system generates PDN codes based on:
- Primary traits (A, T, P, E)
- Energy types (D, S, F)

Example codes:
- P10: Pleasure with Dynamic energy
- E1: Empire with Dynamic energy
- A7: Achievement with Dynamic energy
- T4: Trust with Dynamic energy

## Contributing

1. Fork the repository
2. Create your feature branch
3. Commit your changes
4. Push to the branch
5. Create a Pull Request

## Contact

For any questions or inquiries, please contact:
- Email: tomergur@gmail.com
