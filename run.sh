#!/bin/bash

# AI Academic Paper Assistant - Run Script
# This script helps start the application with proper configuration

set -e

echo "========================================="
echo "AI Academic Paper Assistant"
echo "========================================="

# Check if .env file exists
if [ ! -f .env ]; then
    echo "⚠️  Warning: .env file not found!"
    echo "Creating .env from example..."
    if [ -f .env.example ]; then
        cp .env.example .env
        echo "✅ Created .env file from .env.example"
        echo "Please edit .env file to add your API keys"
    else
        echo "❌ Error: .env.example not found!"
        exit 1
    fi
fi

# Check if requirements are installed
echo "Checking dependencies..."
if ! pip show streamlit > /dev/null 2>&1; then
    echo "Installing dependencies from requirements.txt..."
    pip install -r requirements.txt
fi

# Check if at least one API key is set
if [ -z "$OPENAI_API_KEY" ] && [ -z "$ANTHROPIC_API_KEY" ]; then
    echo "⚠️  Warning: No LLM API keys detected in environment."
    echo "The application will work for paper search but won't generate AI answers."
    echo "To enable AI answers, set OPENAI_API_KEY or ANTHROPIC_API_KEY in .env file"
    echo ""
fi

# Run integration test
echo "Running integration test..."
if python test_integration.py; then
    echo "✅ Integration test passed!"
else
    echo "⚠️  Integration test had issues (this might be normal due to API rate limits)"
fi

echo ""
echo "========================================="
echo "Starting AI Academic Paper Assistant..."
echo "========================================="
echo "Access the application at: http://localhost:8501"
echo "Press Ctrl+C to stop the application"
echo ""

# Start Streamlit application
streamlit run app.py --server.port 8501 --server.address 0.0.0.0