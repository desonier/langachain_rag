#!/bin/bash

# Production startup script for Azure App Service

export PYTHONPATH="/app"
export PYTHONUNBUFFERED=1
export PYTHONDONTWRITEBYTECODE=1

# Get port from environment (Azure App Service sets this)
PORT=${PORT:-5001}

echo "🚀 Starting Resume RAG Application on port $PORT"
echo "📁 Working directory: $(pwd)"
echo "🐍 Python path: $PYTHONPATH"

# Create necessary directories
mkdir -p /app/data /app/resume_vectordb

# For production, use Gunicorn instead of Flask development server
cd /app
exec gunicorn \
    --bind 0.0.0.0:$PORT \
    --workers 2 \
    --threads 4 \
    --timeout 300 \
    --max-requests 1000 \
    --max-requests-jitter 100 \
    --preload \
    --access-logfile - \
    --error-logfile - \
    --log-level info \
    "common_tools.openwebui-resume-rag-admin.src.main:app"