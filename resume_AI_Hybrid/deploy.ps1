# Deploy Resume RAG Application to Azure App Service
# This script builds and deploys the containerized application

param(
    [string]$ResourceGroup = "rg-resume-rag",
    [string]$Location = "eastus",
    [string]$AppName = "resume-rag-app-$(Get-Date -Format 'yyyyMMddHHmm')",
    [string]$ImageName = "resume-rag-app",
    [string]$ImageTag = "latest"
)

$ErrorActionPreference = "Stop"

# Configuration
$AcrName = "resumeragacr$(Get-Date -Format 'yyyyMMddHHmm')"

Write-Host "🚀 Starting deployment of Resume RAG Application..." -ForegroundColor Green

# Check if Azure CLI is logged in
try {
    az account show | Out-Null
    Write-Host "✅ Azure CLI authentication verified" -ForegroundColor Green
} catch {
    Write-Host "❌ Please login to Azure CLI first: az login" -ForegroundColor Red
    exit 1
}

# Create resource group
Write-Host "📦 Creating resource group: $ResourceGroup" -ForegroundColor Yellow
az group create --name $ResourceGroup --location $Location

# Create Azure Container Registry
Write-Host "🐳 Creating Azure Container Registry: $AcrName" -ForegroundColor Yellow
az acr create --resource-group $ResourceGroup --name $AcrName --sku Basic --admin-enabled true

# Get ACR login server
$AcrLoginServer = az acr show --name $AcrName --resource-group $ResourceGroup --query loginServer --output tsv
Write-Host "✅ ACR Login Server: $AcrLoginServer" -ForegroundColor Green

# Login to ACR
Write-Host "🔑 Logging into ACR..." -ForegroundColor Yellow
az acr login --name $AcrName

# Build and push Docker image
Write-Host "🏗️ Building Docker image..." -ForegroundColor Yellow
docker build -t "$ImageName`:$ImageTag" .

Write-Host "🏷️ Tagging image for ACR..." -ForegroundColor Yellow
docker tag "$ImageName`:$ImageTag" "$AcrLoginServer/$ImageName`:$ImageTag"

Write-Host "⬆️ Pushing image to ACR..." -ForegroundColor Yellow
docker push "$AcrLoginServer/$ImageName`:$ImageTag"

# Get Azure OpenAI configuration from environment or prompt
$AzureOpenAiEndpoint = $env:AZURE_OPENAI_ENDPOINT
if (-not $AzureOpenAiEndpoint) {
    $AzureOpenAiEndpoint = Read-Host "🔑 Please enter your Azure OpenAI endpoint"
}

$AzureOpenAiKey = $env:AZURE_OPENAI_KEY
if (-not $AzureOpenAiKey) {
    $AzureOpenAiKey = Read-Host "🔑 Please enter your Azure OpenAI key" -AsSecureString
    $AzureOpenAiKey = [System.Runtime.InteropServices.Marshal]::PtrToStringAuto([System.Runtime.InteropServices.Marshal]::SecureStringToBSTR($AzureOpenAiKey))
}

$AzureOpenAiDeployment = $env:AZURE_OPENAI_CHATGPT_DEPLOYMENT
if (-not $AzureOpenAiDeployment) {
    $AzureOpenAiDeployment = Read-Host "🔑 Please enter your Azure OpenAI deployment name (default: gpt-4)"
    if (-not $AzureOpenAiDeployment) { $AzureOpenAiDeployment = "gpt-4" }
}

# Deploy infrastructure using Bicep
Write-Host "🏗️ Deploying infrastructure..." -ForegroundColor Yellow
az deployment group create `
    --resource-group $ResourceGroup `
    --template-file infra/main.bicep `
    --parameters `
        appName=$AppName `
        acrName=$AcrName `
        azureOpenAiEndpoint=$AzureOpenAiEndpoint `
        azureOpenAiKey=$AzureOpenAiKey `
        azureOpenAiDeployment=$AzureOpenAiDeployment `
        dockerImageName=$ImageName `
        dockerImageTag=$ImageTag

# Get the app service URL
$AppUrl = az webapp show --name $AppName --resource-group $ResourceGroup --query defaultHostName --output tsv

Write-Host "🎉 Deployment completed successfully!" -ForegroundColor Green
Write-Host "📱 Application URL: https://$AppUrl" -ForegroundColor Green
Write-Host "🏗️ Resource Group: $ResourceGroup" -ForegroundColor Green
Write-Host "🐳 Container Registry: $AcrLoginServer" -ForegroundColor Green

# Test the deployment
Write-Host "🧪 Testing deployment..." -ForegroundColor Yellow
try {
    $response = Invoke-WebRequest -Uri "https://$AppUrl" -UseBasicParsing -TimeoutSec 30
    if ($response.StatusCode -eq 200) {
        Write-Host "✅ Application is responding successfully!" -ForegroundColor Green
    } else {
        Write-Host "⚠️ Application returned status code: $($response.StatusCode)" -ForegroundColor Yellow
    }
} catch {
    Write-Host "❌ Application may not be ready yet. Please check the logs." -ForegroundColor Red
    Write-Host "📊 Check logs with: az webapp log tail --name $AppName --resource-group $ResourceGroup" -ForegroundColor Yellow
}

Write-Host "🔗 Useful commands:" -ForegroundColor Green
Write-Host "View logs: az webapp log tail --name $AppName --resource-group $ResourceGroup" -ForegroundColor Yellow
Write-Host "Restart app: az webapp restart --name $AppName --resource-group $ResourceGroup" -ForegroundColor Yellow
Write-Host "Delete resources: az group delete --name $ResourceGroup --yes --no-wait" -ForegroundColor Yellow