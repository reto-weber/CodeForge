#!/bin/bash

# Docker setup script for FastAPI Code Compiler project on WSL/Linux

echo "Building Docker execution environment..."

# Check if Docker is installed
if ! command -v docker &> /dev/null; then
    echo "Docker is not installed. Please install Docker first:"
    echo "sudo apt update && sudo apt install docker.io"
    echo "sudo systemctl enable docker"
    echo "sudo usermod -aG docker $USER"
    echo "Then log out and log back in for group changes to take effect."
    exit 1
fi

# Check if Docker is running
if ! docker info &> /dev/null; then
    echo "Docker daemon is not running. Starting Docker..."
    sudo systemctl start docker
fi

# Build the execution Docker image
echo "Building Docker execution image..."
docker build -f Dockerfile.execution -t code-executor:latest .

if [ $? -eq 0 ]; then
    echo "Docker image built successfully!"
    echo "You can now run the application with: python3 main.py"
    echo "Or use Docker Compose with: docker-compose up"
else
    echo "Failed to build Docker image!"
    echo "Make sure Docker is running and try again."
    exit 1
fi
