#!/bin/bash
# Quick Launch Script - Dashboard
# Aviation Intelligence & Risk Prediction Platform

echo "✈️  AIRP Dashboard Launcher"
echo "==========================="
echo ""

# Check if virtual environment exists
if [ ! -d ".venv" ]; then
    echo "❌ Virtual environment not found"
    echo "   Run ./setup.sh first"
    exit 1
fi

# Activate virtual environment
source .venv/bin/activate

# Check if streamlit is installed
if ! command -v streamlit &> /dev/null; then
    echo "❌ Streamlit not installed"
    echo "   Run: pip install -r requirements.txt"
    exit 1
fi

echo "🚀 Launching dashboard..."
echo "   URL: http://localhost:8501"
echo ""
echo "   Press Ctrl+C to stop"
echo ""

# Launch dashboard
streamlit run 6_dashboard/app.py
