#!/bin/bash

# Activate virtual environment script for WSL/Linux

if [ ! -d "venv" ]; then
    echo "Virtual environment not found. Please run setup.sh first."
    exit 1
fi

echo "Activating virtual environment..."
echo "Run the following command to activate:"
echo "source venv/bin/activate"
echo ""
echo "After activation, you can:"
echo "  - Start the server: ./start.sh"
echo "  - Run directly: python3 main.py"
echo "  - Deactivate later: deactivate"
