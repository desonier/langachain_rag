#!/bin/bash

# Test script to verify Docker setup
# This script builds the Docker image and checks if it can start

echo "======================================"
echo "Testing LangChain RAG Docker Setup"
echo "======================================"
echo ""

# Check if Docker is installed
if ! command -v docker &> /dev/null; then
    echo "❌ Docker is not installed"
    exit 1
fi
echo "✅ Docker is installed"

# Check if Docker Compose is available
if ! docker compose version &> /dev/null; then
    echo "❌ Docker Compose is not available"
    exit 1
fi
echo "✅ Docker Compose is available"

# Build the Docker image
echo ""
echo "Building Docker image..."
if docker compose build --quiet; then
    echo "✅ Docker image built successfully"
else
    echo "❌ Failed to build Docker image"
    exit 1
fi

# Check if image was created
if docker images | grep -q "langachain_rag-langchain-app"; then
    echo "✅ Docker image exists"
    IMAGE_SIZE=$(docker images langachain_rag-langchain-app --format "{{.Size}}")
    echo "   Image size: $IMAGE_SIZE"
else
    echo "❌ Docker image not found"
    exit 1
fi

echo ""
echo "======================================"
echo "✅ All tests passed!"
echo "======================================"
echo ""
echo "To run the application:"
echo "  docker compose up"
echo ""
echo "To run in detached mode:"
echo "  docker compose up -d"
echo ""
echo "To stop the application:"
echo "  docker compose down"
echo ""
