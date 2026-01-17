#!/bin/bash
# Quick Setup Script for Mac/Linux
# Aviation Intelligence & Risk Prediction Platform

echo "🚀 AIRP - Quick Setup Script"
echo "============================"
echo ""

# Check Python
echo "📋 Checking Python..."
if command -v python3 &> /dev/null; then
    PYTHON_VERSION=$(python3 --version)
    echo "✅ $PYTHON_VERSION found"
else
    echo "❌ Python 3 not found. Please install Python 3.8+"
    exit 1
fi

# Check PostgreSQL
echo ""
echo "📋 Checking PostgreSQL..."
if command -v psql &> /dev/null; then
    PSQL_VERSION=$(psql --version)
    echo "✅ $PSQL_VERSION found"
else
    echo "⚠️  PostgreSQL not found. Please install PostgreSQL 13+"
    echo "   Mac: brew install postgresql@15"
    echo "   Linux: sudo apt install postgresql postgresql-contrib"
fi

# Create virtual environment
echo ""
echo "📦 Creating virtual environment..."
if [ -d ".venv" ]; then
    echo "⚠️  Virtual environment already exists"
    read -p "   Recreate? (y/n) " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        rm -rf .venv
        python3 -m venv .venv
        echo "✅ Virtual environment recreated"
    fi
else
    python3 -m venv .venv
    echo "✅ Virtual environment created"
fi

# Activate and install dependencies
echo ""
echo "📥 Installing dependencies..."
source .venv/bin/activate
pip install --upgrade pip -q
pip install -r requirements.txt -q
echo "✅ Dependencies installed"

# Check config
echo ""
echo "⚙️  Checking configuration..."
if [ -f "config.yaml" ]; then
    echo "✅ config.yaml found"
else
    echo "⚠️  config.yaml not found"
    if [ -f "config.yaml.example" ]; then
        cp config.yaml.example config.yaml
        echo "   Created from example - please edit with your settings"
    fi
fi

# Summary
echo ""
echo "========================"
echo "✅ Setup Complete!"
echo "========================"
echo ""
echo "📝 Next steps:"
echo "   1. Edit config.yaml with your database credentials"
echo "   2. Run: source .venv/bin/activate"
echo "   3. Initialize database: python 2_database/db_setup.py"
echo "   4. Load airports: python 1_data_ingestion/airport_loader.py"
echo "   5. Launch dashboard: streamlit run 6_dashboard/app.py"
echo ""
echo "📖 Full guide: See SETUP_GUIDE.md"
echo ""
