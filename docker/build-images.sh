#!/bin/bash

# Build script for language-specific Docker images
echo "Building language-specific Docker images..."

# Set the script directory as working directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# Function to build an image
build_image() {
    local language=$1
    local dockerfile=$2
    local image_name=$3
    
    echo "Building $language image..."
    docker build -f "$dockerfile" -t "$image_name" .
    
    if [ $? -eq 0 ]; then
        echo "✅ Successfully built $image_name"
    else
        echo "❌ Failed to build $image_name"
        exit 1
    fi
}

# Build all language images
build_image "Python" "Dockerfile.python" "code-executor-python:latest"
build_image "C" "Dockerfile.c" "code-executor-c:latest"
build_image "C++" "Dockerfile.cpp" "code-executor-cpp:latest"
build_image "Java" "Dockerfile.java" "code-executor-java:latest"
build_image "Eiffel" "Dockerfile.eiffel" "code-executor-eiffel:latest"

echo ""
echo "🎉 All language-specific Docker images built successfully!"
echo ""
echo "Available images:"
docker images | grep "code-executor"
echo ""
echo "To build using docker-compose instead, run:"
echo "docker-compose -f docker-compose.multi-lang.yml build"
