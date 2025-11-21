# Resume RAG Azure Deployment - Quick Reference

## Prerequisites ✅
- Azure CLI installed and logged in (`az login`)
- Docker Desktop running
- PowerShell 5.1+ or Bash
- Azure subscription with permissions to create resources

## Environment Variables 🔧
Set these before deploying:
```powershell
$env:AZURE_OPENAI_ENDPOINT = "https://your-resource.openai.azure.com/"
$env:AZURE_OPENAI_KEY = "your-api-key"
$env:AZURE_OPENAI_CHATGPT_DEPLOYMENT = "gpt-4"  # your deployment name
```

## Quick Deploy 🚀
```powershell
# Test locally first (optional but recommended)
python test_docker.py

# Deploy to Azure
.\deploy.ps1
```

## What Gets Created 📦
- **Resource Group**: `resume-rag-rg`
- **Container Registry**: `resumerag[uniqueid]`
- **App Service Plan**: Linux, B1 SKU
- **Web App**: Container-based
- **Application Insights**: Monitoring and logging

## URLs After Deployment 🌐
- **Application**: `https://resume-rag-app-[uniqueid].azurewebsites.net`
- **SCM**: `https://resume-rag-app-[uniqueid].scm.azurewebsites.net`
- **Application Insights**: Available in Azure Portal

## Common Commands 📝

### Local Testing
```powershell
# Test container locally
python test_docker.py

# Manual Docker build/run
docker build -t resume-rag-app .
docker run -p 5001:80 resume-rag-app
```

### Azure Management
```powershell
# Check deployment status
az webapp show --name resume-rag-app-[uniqueid] --resource-group resume-rag-rg --query "state"

# View logs
az webapp log tail --name resume-rag-app-[uniqueid] --resource-group resume-rag-rg

# Restart app
az webapp restart --name resume-rag-app-[uniqueid] --resource-group resume-rag-rg

# Update environment variables
az webapp config appsettings set --name resume-rag-app-[uniqueid] --resource-group resume-rag-rg --settings AZURE_OPENAI_ENDPOINT="new-value"
```

### Cleanup
```powershell
# Delete everything
az group delete --name resume-rag-rg --yes --no-wait
```

## Troubleshooting 🔧

### Container Won't Start
1. Check Application Insights logs in Azure Portal
2. View streaming logs: `az webapp log tail --name [app-name] --resource-group resume-rag-rg`
3. Verify environment variables are set correctly

### Application Errors
1. Check `/admin/collections` endpoint for ChromaDB issues
2. Test Azure OpenAI connection in the query interface
3. Monitor Application Insights for performance issues

### Build Failures
1. Ensure Docker Desktop is running
2. Check Azure CLI login status: `az account show`
3. Verify permissions on Azure subscription

## Security Notes 🔒
- Container runs as non-root user
- HTTPS enforced by default
- Managed identity configured for Azure services
- Application Insights for monitoring

## Cost Estimation 💰
- **App Service Plan (B1)**: ~$13/month
- **Container Registry**: ~$5/month
- **Application Insights**: Free tier (5GB/month)
- **Total**: ~$18/month for basic usage

## Next Steps 📈
After deployment:
1. Test all functionality at the app URL
2. Upload your resume documents via the admin interface
3. Configure collections and test queries
4. Monitor performance via Application Insights
5. Set up CI/CD pipeline for updates (optional)

---
📚 **Full Documentation**: See `DEPLOYMENT.md`  
🐳 **Local Testing**: Run `python test_docker.py`  
🚀 **Deploy**: Run `.\deploy.ps1`