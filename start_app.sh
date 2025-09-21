#!/bin/bash

# PDN Chat Application Startup Script
# This script helps you start the application with proper environment setup

echo "🚀 Starting PDN Chat Application..."

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo "❌ Virtual environment not found. Please run: python -m venv venv"
    exit 1
fi

# Activate virtual environment
echo "📦 Activating virtual environment..."
source venv/bin/activate

# Check if OPENAI_API_KEY is set
if [ -z "$OPENAI_API_KEY" ]; then
    echo "⚠️  OPENAI_API_KEY not set. The application will start but AI features won't work."
    echo "   To set it: export OPENAI_API_KEY='your-api-key-here'"
    echo "   Or create a .env file with: OPENAI_API_KEY=your-api-key-here"
    echo ""
fi

# Start the application
echo "🎯 Starting Flask application on http://localhost:8001"
echo "   Press Ctrl+C to stop the application"
echo ""

python run.py
