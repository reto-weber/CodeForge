#!/bin/bash
# Quick start script for Unix/Linux/macOS

echo "🚀 Starting Code Compiler and Runner..."
echo "======================================="

# Check if virtual environment exists
if [ -d "venv" ]; then
    echo "✅ Virtual environment found"
    source venv/bin/activate
    echo "✅ Virtual environment activated"
else
    echo "❌ Virtual environment not found!"
    echo "Please run: python -m venv venv && source venv/bin/activate && pip install -r requirements.txt"
    exit 1
fi

# Check if dependencies are installed
if python -c "import fastapi" 2>/dev/null; then
    echo "✅ Dependencies are installed"
else
    echo "🔄 Installing dependencies..."
    pip install -r requirements.txt
fi

echo "🌐 Starting server at http://localhost:8000"
echo "📂 Examples available for: Python, C, C++, Java"
echo "🛑 Press Ctrl+C to stop the server"
echo ""

python main.py
