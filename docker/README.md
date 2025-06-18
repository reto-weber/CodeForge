# CodeForge Standalone Docker Image

This directory contains the configuration for building a standalone Docker image of CodeForge that includes Docker-in-Docker (DinD) capabilities, allowing you to run the complete CodeForge platform in a single container.

## Quick Start

### Using Docker Compose (Recommended)

```bash
# Build and run the standalone container
docker-compose -f docker-compose.standalone.yml up --build

# Run in detached mode
docker-compose -f docker-compose.standalone.yml up -d --build

# Stop the container
docker-compose -f docker-compose.standalone.yml down
```

### Using Docker Commands

```bash
# Build the image
docker build -f Dockerfile.standalone -t codeforge:standalone .

# Run the container
docker run -d \
  --name codeforge-server \
  --privileged \
  -p 8000:8000 \
  -v codeforge-data:/app/data \
  -v codeforge-logs:/app/logs \
  codeforge:standalone

# View logs
docker logs -f codeforge-server

# Stop the container
docker stop codeforge-server
docker rm codeforge-server
```

## What's Included

The standalone image includes:

- **FastAPI Web Server**: The main CodeForge application server
- **Docker-in-Docker**: Complete Docker runtime for executing user code
- **Language Executors**: Pre-built images for Python, C, C++, Java, and Eiffel
- **Session Management**: Persistent user sessions and container management
- **Security**: Isolated code execution in temporary containers

## Features

- ✅ **Complete Isolation**: Each code execution runs in its own container
- ✅ **Multi-Language Support**: Python, C, C++, Java, Eiffel
- ✅ **Persistent Data**: User sessions and logs are preserved
- ✅ **Health Checks**: Built-in health monitoring
- ✅ **Auto-Restart**: Automatic recovery from failures

## Configuration

### Environment Variables

- `PYTHONPATH=/app` - Python module path
- `CODEFORGE_ENV=docker` - Runtime environment indicator
- `DOCKER_HOST=unix:///var/run/docker.sock` - Docker socket location

### Volumes

- `codeforge-data:/app/data` - Persistent application data
- `codeforge-logs:/app/logs` - Application logs

### Ports

- `8000` - FastAPI web server
- `2376` - Docker API (optional, for debugging)

## Building the Image

The build process:

1. Starts with `docker:27-dind` base image
2. Installs Python 3 and dependencies
3. Copies application code and configuration
4. Sets up Docker-in-Docker environment
5. Configures startup scripts

## Runtime Process

When the container starts:

1. **Docker Daemon**: Starts the Docker daemon for container execution
2. **Image Building**: Builds language-specific execution images
3. **FastAPI Server**: Starts the web application server
4. **Health Checks**: Monitors service health

## Accessing the Application

Once running, access CodeForge at:
- **Web Interface**: http://localhost:8000
- **API Documentation**: http://localhost:8000/api/docs
- **Health Check**: http://localhost:8000/

## Troubleshooting

### Common Issues

1. **Permission Denied**: Ensure the container runs with `--privileged` flag
2. **Port Conflicts**: Change port mapping if 8000 is already in use
3. **Build Failures**: Check Docker daemon is running on host

### Debug Mode

```bash
# Run with debug output
docker run -it --privileged -p 8000:8000 codeforge:standalone /bin/bash

# Inside container, start services manually:
dockerd --host=unix:///var/run/docker.sock &
cd /app/docker && ./build-images.sh
cd /app && python3 src/main.py
```

### View Logs

```bash
# Container logs
docker logs codeforge-server

# Application logs (if using volumes)
docker exec codeforge-server tail -f /app/logs/codeforge.log
```

## Security Considerations

- The container requires `--privileged` mode for Docker-in-Docker
- User code execution is isolated in temporary containers
- No persistent storage of user code by default
- Network isolation between execution containers

## Performance Notes

- Initial startup may take 2-3 minutes to build execution images
- Each language execution creates a new container
- Resource usage scales with concurrent users
- Consider setting resource limits in production

## Production Deployment

For production use:

```yaml
# docker-compose.prod.yml
version: '3.8'
services:
  codeforge:
    image: codeforge:standalone
    restart: always
    ports:
      - "80:8000"
    volumes:
      - ./data:/app/data
      - ./logs:/app/logs
    deploy:
      resources:
        limits:
          memory: 2G
          cpus: '1.0'
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/"]
      interval: 30s
      timeout: 10s
      retries: 3
```

## License

This Docker configuration is part of the CodeForge project and follows the same MIT license.
