# Docker Configuration Guide

This guide provides detailed information about the Docker setup for the LangChain RAG application with ChromaDB.

## Docker Architecture

The application uses a multi-container Docker setup orchestrated by Docker Compose:

```
┌─────────────────────────────────────┐
│     Docker Compose Network          │
│                                     │
│  ┌──────────────────────────────┐  │
│  │  langchain-app Container     │  │
│  │                              │  │
│  │  - Python 3.11               │  │
│  │  - LangChain Framework       │  │
│  │  - ChromaDB (embedded)       │  │
│  │  - HuggingFace Embeddings    │  │
│  └──────────────────────────────┘  │
│              │                      │
│              ▼                      │
│  ┌──────────────────────────────┐  │
│  │  Volume: chroma_data         │  │
│  │  (Persistent Storage)        │  │
│  └──────────────────────────────┘  │
└─────────────────────────────────────┘
```

## Dockerfile Explained

The Dockerfile is optimized for production use:

```dockerfile
FROM python:3.11-slim
# Uses slim Python image to minimize size

WORKDIR /app
# Sets working directory

RUN apt-get update && apt-get install -y build-essential
# Installs necessary build tools for compiling Python packages

RUN pip install --no-cache-dir --trusted-host ... -r requirements.txt
# Installs Python dependencies without caching to reduce image size

COPY app.py .
# Copies application code

RUN mkdir -p /app/chroma_data
# Creates directory for ChromaDB data

ENV PYTHONUNBUFFERED=1
# Ensures Python output is sent straight to terminal

CMD ["python", "app.py"]
# Runs the application
```

## Docker Compose Configuration

### Services

#### langchain-app
- **Purpose**: Main application service
- **Build**: Built from local Dockerfile
- **Volumes**:
  - `./chroma_data:/app/chroma_data` - Persists ChromaDB data
  - `./app.py:/app/app.py` - Enables live code editing (development)
- **Environment**: Accepts OPENAI_API_KEY from .env file
- **Network**: Connected to `langchain-network`

#### chromadb (Optional - Commented)
- **Purpose**: Standalone ChromaDB server
- **Image**: Official ChromaDB image
- **Port**: 8000 (HTTP API)
- **Use case**: When you want to separate the vector database from the application

### Networks

- **langchain-network**: Bridge network for inter-container communication

## Building the Image

### Standard Build

```bash
docker compose build
```

### Build with No Cache

```bash
docker compose build --no-cache
```

### Build Specific Service

```bash
docker compose build langchain-app
```

## Running Containers

### Start All Services

```bash
docker compose up
```

### Start in Detached Mode

```bash
docker compose up -d
```

### Start with Build

```bash
docker compose up --build
```

### Start Specific Service

```bash
docker compose up langchain-app
```

## Managing Containers

### View Running Containers

```bash
docker compose ps
```

### View Logs

```bash
# All services
docker compose logs

# Specific service
docker compose logs langchain-app

# Follow logs
docker compose logs -f

# Last N lines
docker compose logs --tail=100
```

### Stop Containers

```bash
# Stop services
docker compose stop

# Stop and remove containers
docker compose down

# Stop and remove containers + volumes
docker compose down -v
```

### Restart Containers

```bash
docker compose restart
```

## Volume Management

### List Volumes

```bash
docker volume ls | grep langchain
```

### Inspect Volume

```bash
docker volume inspect langachain_rag_chroma_data
```

### Backup ChromaDB Data

```bash
# Create backup
docker run --rm -v langachain_rag_chroma_data:/data \
  -v $(pwd):/backup alpine tar czf /backup/chroma_backup.tar.gz -C /data .

# Restore backup
docker run --rm -v langachain_rag_chroma_data:/data \
  -v $(pwd):/backup alpine tar xzf /backup/chroma_backup.tar.gz -C /data
```

## Development Workflow

### Live Code Editing

The docker-compose.yml mounts `app.py` as a volume, allowing you to:

1. Edit `app.py` locally
2. Restart the container to apply changes:
   ```bash
   docker compose restart langchain-app
   ```

### Debugging

#### Access Container Shell

```bash
docker compose exec langchain-app /bin/bash
```

#### Run Commands in Container

```bash
docker compose exec langchain-app python -c "import langchain; print(langchain.__version__)"
```

#### Check Python Packages

```bash
docker compose exec langchain-app pip list
```

## Troubleshooting

### Container Won't Start

1. Check logs:
   ```bash
   docker compose logs langchain-app
   ```

2. Verify image built correctly:
   ```bash
   docker images | grep langchain
   ```

3. Check port conflicts:
   ```bash
   docker compose ps
   ```

### Permission Issues

If you encounter permission errors with volumes:

```bash
# Fix ownership
sudo chown -R $USER:$USER chroma_data

# Or run with correct permissions
docker compose run --user $(id -u):$(id -g) langchain-app
```

### Memory Issues

Increase Docker memory limit:
- **Docker Desktop**: Settings → Resources → Memory → Increase limit
- **Linux**: Edit `/etc/docker/daemon.json`:
  ```json
  {
    "default-ulimits": {
      "memlock": {
        "Hard": -1,
        "Soft": -1
      }
    }
  }
  ```

### Clean Up Docker Resources

```bash
# Remove stopped containers
docker compose down

# Remove unused images
docker image prune

# Remove unused volumes
docker volume prune

# Remove everything (careful!)
docker system prune -a
```

## Performance Optimization

### Multi-stage Builds

For production, consider using multi-stage builds to reduce image size:

```dockerfile
FROM python:3.11-slim as builder
WORKDIR /app
COPY requirements.txt .
RUN pip install --user --no-cache-dir -r requirements.txt

FROM python:3.11-slim
WORKDIR /app
COPY --from=builder /root/.local /root/.local
COPY app.py .
ENV PATH=/root/.local/bin:$PATH
CMD ["python", "app.py"]
```

### Build Cache

Docker caches layers. Optimize by:
1. Copy requirements.txt before app code
2. Install dependencies before copying application code
3. Place frequently changing files at the end

### Resource Limits

Add resource limits in docker-compose.yml:

```yaml
services:
  langchain-app:
    # ... other config ...
    deploy:
      resources:
        limits:
          cpus: '2'
          memory: 4G
        reservations:
          cpus: '1'
          memory: 2G
```

## Production Deployment

### Best Practices

1. **Use specific image tags** instead of `latest`
2. **Don't mount source code** in production
3. **Use secrets management** for API keys
4. **Enable health checks**:
   ```yaml
   healthcheck:
     test: ["CMD", "python", "-c", "import requests; requests.get('http://localhost:8000/health')"]
     interval: 30s
     timeout: 10s
     retries: 3
   ```
5. **Use logging driver**:
   ```yaml
   logging:
     driver: "json-file"
     options:
       max-size: "10m"
       max-file: "3"
   ```

### Security

1. **Run as non-root user**:
   ```dockerfile
   RUN useradd -m -u 1000 appuser
   USER appuser
   ```

2. **Scan images for vulnerabilities**:
   ```bash
   docker scan langachain_rag-langchain-app
   ```

3. **Use secrets** instead of environment variables for sensitive data

## Monitoring

### Resource Usage

```bash
# Real-time stats
docker stats

# Container inspect
docker compose exec langchain-app top
```

### Logs Management

```bash
# Export logs
docker compose logs > app_logs.txt

# Search logs
docker compose logs | grep ERROR
```

## References

- [Docker Documentation](https://docs.docker.com/)
- [Docker Compose Documentation](https://docs.docker.com/compose/)
- [Best Practices for Dockerfile](https://docs.docker.com/develop/develop-images/dockerfile_best-practices/)
