# Resume RAG Application - Azure Deployment Guide

This guide explains how to containerize and deploy your Resume RAG application to Azure App Service.

## 🏗️ Architecture

The application is containerized using Docker and deployed to Azure App Service with:
- **Azure Container Registry** for storing Docker images
- **Azure App Service** for hosting the containerized application
- **Application Insights** for monitoring and logging
- **Azure OpenAI** integration for RAG functionality

## 📋 Prerequisites

1. **Azure CLI** installed and authenticated
   ```bash
   az login
   ```

2. **Docker Desktop** installed and running

3. **Azure OpenAI Service** deployed with a model deployment

4. **Environment Variables** (optional, can be provided during deployment):
   - `AZURE_OPENAI_ENDPOINT`
   - `AZURE_OPENAI_KEY`
   - `AZURE_OPENAI_CHATGPT_DEPLOYMENT`

## 🚀 Quick Deployment

### Option 1: Using PowerShell (Windows)
```powershell
.\deploy.ps1
```

### Option 2: Using Bash (Linux/Mac/WSL)
```bash
chmod +x deploy.sh
./deploy.sh
```

### Option 3: Manual Deployment

1. **Create Resource Group**
   ```bash
   az group create --name rg-resume-rag --location eastus
   ```

2. **Build and Push Docker Image**
   ```bash
   # Create ACR
   az acr create --resource-group rg-resume-rag --name resumeragacr --sku Basic --admin-enabled true
   
   # Login to ACR
   az acr login --name resumeragacr
   
   # Build and push image
   docker build -t resume-rag-app:latest .
   docker tag resume-rag-app:latest resumeragacr.azurecr.io/resume-rag-app:latest
   docker push resumeragacr.azurecr.io/resume-rag-app:latest
   ```

3. **Deploy Infrastructure**
   ```bash
   az deployment group create \
     --resource-group rg-resume-rag \
     --template-file infra/main.bicep \
     --parameters @infra/main.parameters.json
   ```

## 🔧 Configuration

### Environment Variables

The following environment variables are automatically configured in Azure App Service:

| Variable | Description | Required |
|----------|-------------|----------|
| `AZURE_OPENAI_ENDPOINT` | Your Azure OpenAI endpoint URL | Yes |
| `AZURE_OPENAI_KEY` | Your Azure OpenAI API key | Yes |
| `AZURE_OPENAI_CHATGPT_DEPLOYMENT` | Model deployment name | Yes |
| `AZURE_OPENAI_API_VERSION` | API version (default: 2024-02-15-preview) | No |
| `VECTOR_DB_PATH` | Path for ChromaDB storage | No |
| `PORT` | Application port (set by Azure) | No |

### Azure App Service Settings

The Bicep template configures:
- **Linux container** with custom Docker image
- **Application Insights** for monitoring
- **Always On** enabled (for non-F1 tiers)
- **HTTPS only** enforced
- **Managed Identity** enabled

## 📊 Monitoring and Troubleshooting

### View Application Logs
```bash
az webapp log tail --name <app-name> --resource-group rg-resume-rag
```

### Check Application Status
```bash
az webapp show --name <app-name> --resource-group rg-resume-rag --query state
```

### Restart Application
```bash
az webapp restart --name <app-name> --resource-group rg-resume-rag
```

### Application Insights
Monitor your application performance and errors through:
- Azure Portal → Application Insights → your app insights resource
- View metrics, logs, and performance data

## 🔒 Security Considerations

1. **Managed Identity**: The app uses system-assigned managed identity
2. **HTTPS Only**: All traffic is forced to use HTTPS
3. **TLS 1.2**: Minimum TLS version enforced
4. **Container Security**: App runs as non-root user
5. **Key Vault**: Consider using Azure Key Vault for secrets in production

## 📈 Scaling and Performance

### App Service Plan Options
- **F1 (Free)**: Development/testing only
- **B1 (Basic)**: Small production workloads
- **S1 (Standard)**: Medium production workloads with auto-scaling
- **P1V2 (Premium)**: High performance with more features

### Scaling Configuration
```bash
# Scale out (add instances)
az appservice plan update --name <plan-name> --resource-group rg-resume-rag --number-of-workers 3

# Scale up (change tier)
az appservice plan update --name <plan-name> --resource-group rg-resume-rag --sku S1
```

## 🗄️ Data Persistence

**Important**: ChromaDB data is stored in `/tmp/resume_vectordb` which is ephemeral in containers.

For production, consider:
1. **Azure Files** for persistent storage
2. **Azure Cosmos DB** for vector storage
3. **Azure Storage** for uploaded documents

## 🧹 Cleanup

Delete all resources:
```bash
az group delete --name rg-resume-rag --yes --no-wait
```

## 📝 Customization

### Modify Docker Image
1. Update `Dockerfile` or application code
2. Rebuild and push image to ACR
3. Restart the App Service

### Update Configuration
1. Modify `infra/main.bicep` or `infra/main.parameters.json`
2. Redeploy using `az deployment group create`

### Add Custom Domain
```bash
az webapp config hostname add --webapp-name <app-name> --resource-group rg-resume-rag --hostname yourdomain.com
```

## 🤝 Support

- **Application Logs**: Check Azure App Service logs for runtime issues
- **Container Logs**: Use `az webapp log tail` for container-specific issues
- **Application Insights**: Monitor performance and errors
- **Azure Support**: Create support tickets for Azure-specific issues

## 📚 Additional Resources

- [Azure App Service Documentation](https://docs.microsoft.com/azure/app-service/)
- [Azure Container Registry Documentation](https://docs.microsoft.com/azure/container-registry/)
- [Azure OpenAI Service Documentation](https://docs.microsoft.com/azure/cognitive-services/openai/)
- [Application Insights Documentation](https://docs.microsoft.com/azure/azure-monitor/app/app-insights-overview/)