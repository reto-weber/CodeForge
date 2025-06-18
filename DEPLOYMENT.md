# CodeForge Standalone Docker Deployment Guide

This guide will help you deploy CodeForge as a standalone Docker container with Docker-in-Docker support.

## 📋 Prerequisites

- Docker Engine 20.10 or later
- Docker Compose 2.0 or later (optional, but recommended)
- At least 2GB RAM available
- Ports 8000 available (or configure different ports)

## 🚀 Quick Deployment

### Method 1: Using Docker Compose (Recommended)

```bash
# Clone or download the CodeForge repository
git clone <repository-url>
cd ap_online

# Build and start the service
docker-compose -f docker-compose.standalone.yml up -d --build

# Check status
docker-compose -f docker-compose.standalone.yml ps

# View logs
docker-compose -f docker-compose.standalone.yml logs -f

# Stop the service
docker-compose -f docker-compose.standalone.yml down
```

### Method 2: Using Build Script

```bash
# Build the image
./build-standalone.sh

# Run the container
docker run -d \
  --name codeforge-server \
  --privileged \
  -p 8000:8000 \
  -v codeforge-data:/app/data \
  -v codeforge-logs:/app/logs \
  codeforge:standalone
```

### Method 3: Manual Docker Commands

```bash
# Build the image
docker build -f Dockerfile.standalone -t codeforge:standalone .

# Create volumes
docker volume create codeforge-data
docker volume create codeforge-logs

# Run the container
docker run -d \
  --name codeforge-server \
  --privileged \
  -p 8000:8000 \
  -v codeforge-data:/app/data \
  -v codeforge-logs:/app/logs \
  --restart unless-stopped \
  codeforge:standalone
```

## 🔧 Configuration Options

### Environment Variables

```bash
# Custom configuration
docker run -d \
  --name codeforge-server \
  --privileged \
  -p 8000:8000 \
  -e CODEFORGE_ENV=production \
  -e PYTHONPATH=/app \
  codeforge:standalone
```

### Port Configuration

```bash
# Use different port
docker run -d \
  --name codeforge-server \
  --privileged \
  -p 3000:8000 \
  codeforge:standalone

# Access at http://localhost:3000
```

### Volume Mounts

```bash
# Mount local directories
docker run -d \
  --name codeforge-server \
  --privileged \
  -p 8000:8000 \
  -v ./data:/app/data \
  -v ./logs:/app/logs \
  -v ./config:/app/src/config \
  codeforge:standalone
```

## 🧪 Testing the Deployment

### Automated Testing

```bash
# Run the test script
./test-standalone.sh
```

### Manual Testing

```bash
# Check if container is running
docker ps | grep codeforge

# Check logs
docker logs codeforge-server

# Test health endpoint
curl http://localhost:8000/health

# Test main page
curl http://localhost:8000/
```

### Verify Language Support

```bash
# Check available Docker images inside container
docker exec codeforge-server docker images | grep code-executor
```

## 📊 Monitoring and Maintenance

### Health Monitoring

```bash
# Check health status
curl -s http://localhost:8000/health | jq

# Expected response:
{
  "status": "healthy",
  "timestamp": 1735372800.123,
  "docker": "healthy",
  "active_sessions": 0,
  "active_processes": 0,
  "supported_languages": ["python", "c", "cpp", "java", "eiffel"]
}
```

### Log Management

```bash
# View real-time logs
docker logs -f codeforge-server

# Check log files (if using volumes)
tail -f ./logs/codeforge.log

# Rotate logs
docker exec codeforge-server logrotate /etc/logrotate.conf
```

### Resource Monitoring

```bash
# Check resource usage
docker stats codeforge-server

# Check disk usage
docker exec codeforge-server df -h
```

## 🔐 Security Considerations

### Production Security

```bash
# Run with resource limits
docker run -d \
  --name codeforge-server \
  --privileged \
  -p 8000:8000 \
  --memory=2g \
  --cpus=1.0 \
  --ulimit nofile=1024:1024 \
  codeforge:standalone
```

### Network Security

```bash
# Bind to specific interface
docker run -d \
  --name codeforge-server \
  --privileged \
  -p 127.0.0.1:8000:8000 \
  codeforge:standalone

# Use with reverse proxy (nginx, traefik, etc.)
```

## 🚀 Production Deployment

### Docker Compose Production

```yaml
# docker-compose.prod.yml
version: '3.8'
services:
  codeforge:
    image: codeforge:standalone
    container_name: codeforge-prod
    restart: always
    ports:
      - "127.0.0.1:8000:8000"
    volumes:
      - ./data:/app/data
      - ./logs:/app/logs
    deploy:
      resources:
        limits:
          memory: 4G
          cpus: '2.0'
        reservations:
          memory: 1G
          cpus: '0.5'
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/health"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 120s
    logging:
      driver: "json-file"
      options:
        max-size: "10m"
        max-file: "3"
```

### With Nginx Reverse Proxy

```nginx
# /etc/nginx/sites-available/codeforge
server {
    listen 80;
    server_name your-domain.com;
    
    location / {
        proxy_pass http://localhost:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        
        # WebSocket support (if needed)
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
    }
}
```

## 🔄 Updates and Maintenance

### Updating the Application

```bash
# Pull latest changes
git pull

# Rebuild and restart
docker-compose -f docker-compose.standalone.yml down
docker-compose -f docker-compose.standalone.yml up -d --build
```

### Backup and Restore

```bash
# Backup data
docker run --rm -v codeforge-data:/data -v $(pwd):/backup alpine tar czf /backup/codeforge-data-backup.tar.gz -C /data .

# Restore data
docker run --rm -v codeforge-data:/data -v $(pwd):/backup alpine tar xzf /backup/codeforge-data-backup.tar.gz -C /data
```

## 🆘 Troubleshooting

### Common Issues

1. **Container won't start**
   ```bash
   # Check if privileged mode is allowed
   docker run --rm --privileged alpine echo "test"
   
   # Check logs
   docker logs codeforge-server
   ```

2. **Port already in use**
   ```bash
   # Find what's using the port
   sudo netstat -tulpn | grep :8000
   
   # Use different port
   docker run -p 8001:8000 codeforge:standalone
   ```

3. **Health check failing**
   ```bash
   # Check if application is starting
   docker exec codeforge-server ps aux | grep python
   
   # Check internal connectivity
   docker exec codeforge-server curl localhost:8000/health
   ```

4. **Docker-in-Docker issues**
   ```bash
   # Check if Docker daemon is running inside container
   docker exec codeforge-server docker info
   
   # Check Docker socket
   docker exec codeforge-server ls -la /var/run/docker.sock
   ```

### Debug Mode

```bash
# Run in interactive mode for debugging
docker run -it --privileged -p 8000:8000 codeforge:standalone /bin/bash

# Inside container, start services manually:
dockerd --host=unix:///var/run/docker.sock &
cd /app/docker && ./build-images.sh
cd /app && python3 src/main.py
```

## 📈 Performance Tuning

### Resource Optimization

```bash
# Monitor resource usage
docker stats codeforge-server

# Adjust memory limits based on usage
docker update --memory=3g codeforge-server
```

### Container Cleanup

```bash
# Clean up old execution containers
docker exec codeforge-server docker container prune -f

# Clean up unused images
docker exec codeforge-server docker image prune -f
```

## 📝 Support

For issues and support:
1. Check the logs: `docker logs codeforge-server`
2. Run the test script: `./test-standalone.sh`
3. Check the health endpoint: `curl http://localhost:8000/health`
4. Review this troubleshooting guide

## 📄 License

This deployment configuration is part of the CodeForge project under MIT License.
