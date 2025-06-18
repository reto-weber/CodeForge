#!/bin/bash

# Test script for CodeForge Standalone Docker Image
set -e

echo "🧪 Testing CodeForge Standalone Docker Build..."
echo ""

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Get the directory where this script is located
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

cd "$PROJECT_ROOT"

# Function to print colored output
print_status() {
    local color=$1
    local message=$2
    echo -e "${color}${message}${NC}"
}

# Check if Docker is available
if ! docker --version >/dev/null 2>&1; then
    print_status $RED "❌ Docker is not available. Please install Docker first."
    exit 1
fi

print_status $GREEN "✅ Docker is available"

# Check if we can run privileged containers
if ! docker run --rm --privileged alpine echo "Privileged mode test" >/dev/null 2>&1; then
    print_status $RED "❌ Cannot run privileged containers. Make sure Docker allows privileged mode."
    exit 1
fi

print_status $GREEN "✅ Privileged mode is available"

# Build the standalone image
print_status $YELLOW "🔨 Using existing standalone image..."
if docker image inspect codeforge:standalone >/dev/null 2>&1; then
    print_status $GREEN "✅ Image exists, using codeforge:standalone"
    docker tag codeforge:standalone codeforge:test
elif docker build -f Dockerfile.standalone -t codeforge:test . >/dev/null 2>&1; then
    print_status $GREEN "✅ Image built successfully"
else
    print_status $RED "❌ Failed to build image"
    exit 1
fi

# Test running the container
print_status $YELLOW "🚀 Testing container startup..."
CONTAINER_ID=$(docker run -d --name codeforge-test --privileged -p 8001:8000 codeforge:test)

if [ $? -eq 0 ]; then
    print_status $GREEN "✅ Container started successfully"
else
    print_status $RED "❌ Failed to start container"
    exit 1
fi

# Wait for the service to be ready
print_status $YELLOW "⏳ Waiting for service to be ready..."
timeout=120
while [ $timeout -gt 0 ]; do
    if curl -f http://localhost:8001/health >/dev/null 2>&1; then
        print_status $GREEN "✅ Service is responding to health checks"
        break
    fi
    echo -n "."
    sleep 2
    timeout=$((timeout-2))
done

if [ $timeout -le 0 ]; then
    print_status $RED "❌ Service did not become ready in time"
    docker logs codeforge-test
    docker stop codeforge-test >/dev/null 2>&1
    docker rm codeforge-test >/dev/null 2>&1
    exit 1
fi

# Test the main page
print_status $YELLOW "🌐 Testing main page..."
if curl -f http://localhost:8001/ >/dev/null 2>&1; then
    print_status $GREEN "✅ Main page is accessible"
else
    print_status $RED "❌ Main page is not accessible"
fi

# Cleanup
print_status $YELLOW "🧹 Cleaning up..."
docker stop codeforge-test >/dev/null 2>&1
docker rm codeforge-test >/dev/null 2>&1
docker rmi codeforge:test >/dev/null 2>&1

print_status $GREEN ""
print_status $GREEN "🎉 All tests passed! The standalone Docker image is working correctly."
print_status $GREEN ""
print_status $GREEN "Ready to build and deploy:"
print_status $GREEN "  ./build-standalone.sh"
print_status $GREEN "  docker-compose -f docker-compose.standalone.yml up -d"
print_status $GREEN ""
