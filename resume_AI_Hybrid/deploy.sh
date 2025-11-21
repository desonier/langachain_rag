#!/bin/bash

# Deploy Resume RAG Application to Azure App Service
# This script builds and deploys the containerized application

set -e

# Configuration
RESOURCE_GROUP="rg-resume-rag"
LOCATION="eastus"
ACR_NAME="resumeragacr$(date +%s)"
APP_NAME="resume-rag-app-$(date +%s)"
IMAGE_NAME="resume-rag-app"
IMAGE_TAG="latest"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${GREEN}🚀 Starting deployment of Resume RAG Application...${NC}"

# Check if Azure CLI is logged in
if ! az account show > /dev/null 2>&1; then
    echo -e "${RED}❌ Please login to Azure CLI first: az login${NC}"
    exit 1
fi

# Create resource group
echo -e "${YELLOW}📦 Creating resource group: $RESOURCE_GROUP${NC}"
az group create --name $RESOURCE_GROUP --location $LOCATION

# Create Azure Container Registry
echo -e "${YELLOW}🐳 Creating Azure Container Registry: $ACR_NAME${NC}"
az acr create --resource-group $RESOURCE_GROUP --name $ACR_NAME --sku Basic --admin-enabled true

# Get ACR login server
ACR_LOGIN_SERVER=$(az acr show --name $ACR_NAME --resource-group $RESOURCE_GROUP --query loginServer --output tsv)
echo -e "${GREEN}✅ ACR Login Server: $ACR_LOGIN_SERVER${NC}"

# Login to ACR
echo -e "${YELLOW}🔑 Logging into ACR...${NC}"
az acr login --name $ACR_NAME

# Build and push Docker image
echo -e "${YELLOW}🏗️ Building Docker image...${NC}"
docker build -t $IMAGE_NAME:$IMAGE_TAG .

echo -e "${YELLOW}🏷️ Tagging image for ACR...${NC}"
docker tag $IMAGE_NAME:$IMAGE_TAG $ACR_LOGIN_SERVER/$IMAGE_NAME:$IMAGE_TAG

echo -e "${YELLOW}⬆️ Pushing image to ACR...${NC}"
docker push $ACR_LOGIN_SERVER/$IMAGE_NAME:$IMAGE_TAG

# Get Azure OpenAI configuration from environment or prompt
if [ -z "$AZURE_OPENAI_ENDPOINT" ]; then
    echo -e "${YELLOW}🔑 Please enter your Azure OpenAI endpoint:${NC}"
    read -r AZURE_OPENAI_ENDPOINT
fi

if [ -z "$AZURE_OPENAI_KEY" ]; then
    echo -e "${YELLOW}🔑 Please enter your Azure OpenAI key:${NC}"
    read -rs AZURE_OPENAI_KEY
fi

if [ -z "$AZURE_OPENAI_DEPLOYMENT" ]; then
    echo -e "${YELLOW}🔑 Please enter your Azure OpenAI deployment name (default: gpt-4):${NC}"
    read -r AZURE_OPENAI_DEPLOYMENT
    AZURE_OPENAI_DEPLOYMENT=${AZURE_OPENAI_DEPLOYMENT:-gpt-4}
fi

# Deploy infrastructure using Bicep
echo -e "${YELLOW}🏗️ Deploying infrastructure...${NC}"
az deployment group create \
    --resource-group $RESOURCE_GROUP \
    --template-file infra/main.bicep \
    --parameters \
        appName=$APP_NAME \
        acrName=$ACR_NAME \
        azureOpenAiEndpoint=$AZURE_OPENAI_ENDPOINT \
        azureOpenAiKey=$AZURE_OPENAI_KEY \
        azureOpenAiDeployment=$AZURE_OPENAI_DEPLOYMENT \
        dockerImageName=$IMAGE_NAME \
        dockerImageTag=$IMAGE_TAG

# Get the app service URL
APP_URL=$(az webapp show --name $APP_NAME --resource-group $RESOURCE_GROUP --query defaultHostName --output tsv)

echo -e "${GREEN}🎉 Deployment completed successfully!${NC}"
echo -e "${GREEN}📱 Application URL: https://$APP_URL${NC}"
echo -e "${GREEN}🏗️ Resource Group: $RESOURCE_GROUP${NC}"
echo -e "${GREEN}🐳 Container Registry: $ACR_LOGIN_SERVER${NC}"

# Test the deployment
echo -e "${YELLOW}🧪 Testing deployment...${NC}"
if curl -f -s "https://$APP_URL" > /dev/null; then
    echo -e "${GREEN}✅ Application is responding successfully!${NC}"
else
    echo -e "${RED}❌ Application may not be ready yet. Please check the logs.${NC}"
    echo -e "${YELLOW}📊 Check logs with: az webapp log tail --name $APP_NAME --resource-group $RESOURCE_GROUP${NC}"
fi

echo -e "${GREEN}🔗 Useful commands:${NC}"
echo -e "View logs: ${YELLOW}az webapp log tail --name $APP_NAME --resource-group $RESOURCE_GROUP${NC}"
echo -e "Restart app: ${YELLOW}az webapp restart --name $APP_NAME --resource-group $RESOURCE_GROUP${NC}"
echo -e "Delete resources: ${YELLOW}az group delete --name $RESOURCE_GROUP --yes --no-wait${NC}"