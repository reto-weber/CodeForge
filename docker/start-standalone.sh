#!/bin/bash
set -e

echo "Starting CodeForge Standalone Server with Docker-in-Docker..."

# Start Docker daemon in the background
echo "Starting Docker daemon..."
dockerd --host=unix:///var/run/docker.sock --host=tcp://0.0.0.0:2376 --tls=false &
DOCKERD_PID=$!

# Function to cleanup on exit
cleanup() {
    echo "Shutting down..."
    kill $DOCKERD_PID 2>/dev/null || true
    exit 0
}
trap cleanup SIGTERM SIGINT

# Wait for Docker daemon to be ready
echo "Waiting for Docker daemon to start..."
timeout=60
while ! docker info >/dev/null 2>&1; do
    if [ $timeout -le 0 ]; then
        echo "Timeout waiting for Docker daemon"
        exit 1
    fi
    echo "Waiting for Docker daemon... ($timeout seconds remaining)"
    sleep 2
    timeout=$((timeout-2))
done

echo "Docker daemon is ready!"

# Build execution images
echo "Building execution images..."
cd /app/docker
./build-images.sh

echo "Starting CodeForge FastAPI server..."
cd /app
exec python3 src/main.py
