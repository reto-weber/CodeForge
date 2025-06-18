#!/bin/bash

# Build script for CodeForge Standalone Docker Image
set -e

echo "🚀 Building CodeForge Standalone Docker Image..."
echo "This may take several minutes on first build."
echo ""

# Get the directory where this script is located
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$SCRIPT_DIR"

cd "$PROJECT_ROOT"

# Build the standalone image
echo "Building standalone image..."
DOCKER_BUILDKIT=0 docker build -f Dockerfile.standalone -t codeforge:standalone .

if [ $? -eq 0 ]; then
    echo ""
    echo "✅ Successfully built CodeForge standalone image!"
    echo ""
    echo "🎉 Ready to run! Use one of these commands:"
    echo ""
    echo "Quick start with Docker Compose:"
    echo "  docker-compose -f docker-compose.standalone.yml up -d"
    echo ""
    echo "Or run directly with Docker:"
    echo "  docker run -d --name codeforge-server --privileged -p 8000:8000 codeforge:standalone"
    echo ""
    echo "Access the application at: http://localhost:8000"
    echo ""
else
    echo "❌ Failed to build CodeForge standalone image"
    exit 1
fi
