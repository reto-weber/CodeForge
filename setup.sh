#!/bin/bash

# Setup script for FastAPI Code Compiler project on WSL/Linux

echo "Setting up FastAPI Code Compiler project..."

# Check if Python 3 is installed
if ! command -v python3 &> /dev/null; then
    echo "Python 3 is not installed. Please install Python 3 first."
    exit 1
fi

# Check and install essential development tools
echo "Checking for essential development tools..."

# Check for GCC
if ! command -v gcc &> /dev/null; then
    echo "GCC not found. Installing build-essential..."
    sudo apt update && sudo apt install -y build-essential
fi

# Check for G++
if ! command -v g++ &> /dev/null; then
    echo "G++ not found. Should be installed with build-essential..."
fi

# Check for Java
if ! command -v javac &> /dev/null; then
    echo "Java compiler not found. Installing OpenJDK..."
    sudo apt install -y default-jdk
fi

# Check for Docker (optional)
if ! command -v docker &> /dev/null; then
    echo "Docker not found. You can install it later for containerized execution."
    echo "To install Docker: sudo apt install docker.io && sudo systemctl enable docker"
fi

# Remove old Windows virtual environment if it exists
if [ -d "venv" ]; then
    echo "Removing old Windows virtual environment..."
    rm -rf venv
fi

# Create new virtual environment
echo "Creating virtual environment..."
python3 -m venv venv

# Activate virtual environment
echo "Activating virtual environment..."
source venv/bin/activate

# Upgrade pip
echo "Upgrading pip..."
pip install --upgrade pip

# Install requirements
if [ -f "requirements.txt" ]; then
    echo "Installing requirements..."
    pip install -r requirements.txt
else
    echo "requirements.txt not found. Installing basic dependencies..."
    pip install fastapi uvicorn jinja2 python-multipart
fi

echo "Setup complete!"
echo "To activate the virtual environment in the future, run: source venv/bin/activate"
echo "To start the server, run: ./start.sh"
