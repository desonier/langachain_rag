#!/bin/bash

# Build Docker container using .env file values
# Usage: ./build_container.sh

# Colors for output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

echo -e "${GREEN}🐳 Building Resume RAG Docker Container with .env Configuration${NC}"
echo "============================================================"

# Function to load .env file
load_env_file() {
    local env_file=".env"
    
    if [[ ! -f "$env_file" ]]; then
        echo -e "${RED}❌ .env file not found at: $env_file${NC}"
        echo -e "${YELLOW}📝 Please copy .env.example to .env and fill in your values:${NC}"
        echo -e "${CYAN}   cp .env.example .env${NC}"
        exit 1
    fi
    
    echo -e "${BLUE}📁 Loading environment variables from: $env_file${NC}"
    
    # Export variables from .env file
    while IFS='=' read -r key value; do
        # Skip comments and empty lines
        if [[ $key =~ ^[[:space:]]*# ]] || [[ -z $key ]]; then
            continue
        fi
        
        # Remove leading/trailing whitespace and quotes
        key=$(echo "$key" | xargs)
        value=$(echo "$value" | xargs)
        value="${value%\"}"
        value="${value#\"}"
        value="${value%\'}"
        value="${value#\'}"
        
        if [[ -n $key && -n $value ]]; then
            export "$key"="$value"
            echo -e "  ✅ Loaded: $key"
        fi
    done < "$env_file"
}

# Check if Docker is running
if ! command -v docker &> /dev/null; then
    echo -e "${RED}❌ Docker is not available. Please install Docker.${NC}"
    exit 1
fi

if ! docker --version &> /dev/null; then
    echo -e "${RED}❌ Docker is not running. Please start Docker.${NC}"
    exit 1
fi

echo -e "${GREEN}✅ Docker is available${NC}"

# Load environment variables from .env file
load_env_file

# Validate required environment variables
required_vars=("AZURE_OPENAI_ENDPOINT" "AZURE_OPENAI_KEY" "AZURE_OPENAI_CHATGPT_DEPLOYMENT")
missing_vars=()

for var in "${required_vars[@]}"; do
    value="${!var}"
    if [[ -z "$value" || "$value" == "your_value_here" || "$value" == "YOUR_AZURE_OPENAI_ENDPOINT" ]]; then
        missing_vars+=("$var")
    fi
done

if [[ ${#missing_vars[@]} -gt 0 ]]; then
    echo -e "${RED}❌ Missing or placeholder values for required environment variables:${NC}"
    for var in "${missing_vars[@]}"; do
        echo -e "${YELLOW}   - $var${NC}"
    done
    echo -e "${YELLOW}📝 Please update your .env file with actual values${NC}"
    exit 1
fi

# Display configuration (masked for security)
echo -e "\n${BLUE}🔧 Configuration Summary:${NC}"
endpoint_masked="${AZURE_OPENAI_ENDPOINT}"
key_masked="${AZURE_OPENAI_KEY:0:8}..."
deployment="${AZURE_OPENAI_CHATGPT_DEPLOYMENT}"
api_version="${AZURE_OPENAI_API_VERSION:-2024-02-15-preview}"

echo -e "  📡 Endpoint: ${CYAN}$endpoint_masked${NC}"
echo -e "  🔑 API Key: ${CYAN}$key_masked${NC}"
echo -e "  🚀 Deployment: ${CYAN}$deployment${NC}"
echo -e "  📅 API Version: ${CYAN}$api_version${NC}"

# Set container and image names
image_name="resume-rag-app"
container_name="resume-rag-local"
port=5001

# Build Docker image
echo -e "\n${BLUE}🏗️ Building Docker image...${NC}"
if docker build -t "$image_name" .; then
    echo -e "${GREEN}✅ Docker image '$image_name' built successfully${NC}"
else
    echo -e "${RED}❌ Failed to build Docker image${NC}"
    exit 1
fi

# Stop and remove existing container if it exists
echo -e "\n${BLUE}🧹 Cleaning up existing containers...${NC}"
docker stop "$container_name" 2>/dev/null || true
docker rm "$container_name" 2>/dev/null || true

# Prepare environment variables for container
env_args=()
for var in "${required_vars[@]}"; do
    value="${!var}"
    if [[ -n "$value" ]]; then
        env_args+=("-e" "$var=$value")
    fi
done

# Add API version if set
if [[ -n "$AZURE_OPENAI_API_VERSION" ]]; then
    env_args+=("-e" "AZURE_OPENAI_API_VERSION=$AZURE_OPENAI_API_VERSION")
fi

# Run the container
echo -e "${BLUE}🚀 Starting container '$container_name'...${NC}"
echo -e "${CYAN}📡 Port mapping: localhost:$port -> container:80${NC}"

if docker run -d --name "$container_name" -p "${port}:80" "${env_args[@]}" "$image_name"; then
    echo -e "${GREEN}✅ Container started successfully${NC}"
    
    # Wait for container to be ready
    echo -e "\n${BLUE}⏳ Waiting for application to start...${NC}"
    max_attempts=30
    attempt=0
    ready=false
    
    while [[ $attempt -lt $max_attempts && $ready == false ]]; do
        ((attempt++))
        sleep 2
        
        if curl -s -f "http://localhost:$port" > /dev/null 2>&1; then
            ready=true
            break
        fi
        
        echo -e "  ${YELLOW}⏳ Attempt $attempt/$max_attempts - waiting for application...${NC}"
    done
    
    if [[ $ready == true ]]; then
        echo -e "${GREEN}✅ Application is ready!${NC}"
        echo -e "\n${BLUE}🌐 Application URLs:${NC}"
        echo -e "  ${CYAN}📊 Main Dashboard: http://localhost:$port${NC}"
        echo -e "  ${CYAN}🔍 Query Interface: http://localhost:$port/admin/query${NC}"
        echo -e "  ${CYAN}📁 Collections: http://localhost:$port/admin/collections${NC}"
        echo -e "  ${CYAN}🔧 Database Manager: http://localhost:$port/admin/database${NC}"
        
        echo -e "\n${BLUE}📋 Container Management:${NC}"
        echo -e "  ${YELLOW}🔍 View logs: docker logs $container_name${NC}"
        echo -e "  ${YELLOW}🛑 Stop: docker stop $container_name${NC}"
        echo -e "  ${YELLOW}🗑️ Remove: docker rm $container_name${NC}"
        echo -e "  ${YELLOW}📊 Stats: docker stats $container_name${NC}"
    else
        echo -e "${RED}❌ Application failed to start within $((max_attempts * 2)) seconds${NC}"
        echo -e "${YELLOW}📋 Container logs:${NC}"
        docker logs "$container_name"
    fi
else
    echo -e "${RED}❌ Failed to start container${NC}"
    exit 1
fi

echo -e "\n${GREEN}🎉 Container build and deployment completed!${NC}"
echo -e "${CYAN}🔗 Open http://localhost:$port in your browser to access the application${NC}"