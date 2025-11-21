# Building Docker Container with .env Configuration

## 📋 Step-by-Step Guide

### Step 1: Create your .env file

1. **Copy the example file:**
   ```powershell
   Copy-Item .env.example .env
   ```

2. **Edit the .env file** with your actual Azure OpenAI values:
   ```bash
   # Azure OpenAI Configuration
   AZURE_OPENAI_ENDPOINT=https://your-openai-resource.openai.azure.com/
   AZURE_OPENAI_KEY=your_actual_api_key_here
   AZURE_OPENAI_CHATGPT_DEPLOYMENT=gpt-4
   AZURE_OPENAI_API_VERSION=2024-02-15-preview
   ```

### Step 2: Build using automated script (Recommended)

**Option A: PowerShell (Windows)**
```powershell
.\build_container.ps1
```

**Option B: Bash (Linux/Mac/WSL)**
```bash
./build_container.sh
```

### Step 3: Manual build (Alternative)

If you prefer manual control, here are the individual steps:

#### 3.1. Load environment variables from .env
```powershell
# PowerShell - Load .env file
Get-Content .env | ForEach-Object {
    if ($_ -match '^([^#][^=]*?)=(.*)$') {
        $name = $matches[1].Trim()
        $value = $matches[2].Trim() -replace '^[''"]|[''"]$', ''
        [Environment]::SetEnvironmentVariable($name, $value, [EnvironmentVariableTarget]::Process)
        Write-Host "Loaded: $name"
    }
}
```

```bash
# Bash - Load .env file
export $(grep -v '^#' .env | xargs)
```

#### 3.2. Verify environment variables
```powershell
# PowerShell - Check variables
Write-Host "Endpoint: $env:AZURE_OPENAI_ENDPOINT"
Write-Host "Deployment: $env:AZURE_OPENAI_CHATGPT_DEPLOYMENT"
Write-Host "API Key: $($env:AZURE_OPENAI_KEY.Substring(0,8))..."
```

```bash
# Bash - Check variables
echo "Endpoint: $AZURE_OPENAI_ENDPOINT"
echo "Deployment: $AZURE_OPENAI_CHATGPT_DEPLOYMENT"
echo "API Key: ${AZURE_OPENAI_KEY:0:8}..."
```

#### 3.3. Build Docker image
```powershell
docker build -t resume-rag-app .
```

#### 3.4. Run container with environment variables
```powershell
# PowerShell
docker run -d --name resume-rag-local -p 5001:80 `
  -e AZURE_OPENAI_ENDPOINT=$env:AZURE_OPENAI_ENDPOINT `
  -e AZURE_OPENAI_KEY=$env:AZURE_OPENAI_KEY `
  -e AZURE_OPENAI_CHATGPT_DEPLOYMENT=$env:AZURE_OPENAI_CHATGPT_DEPLOYMENT `
  -e AZURE_OPENAI_API_VERSION=$env:AZURE_OPENAI_API_VERSION `
  resume-rag-app
```

```bash
# Bash
docker run -d --name resume-rag-local -p 5001:80 \
  -e AZURE_OPENAI_ENDPOINT="$AZURE_OPENAI_ENDPOINT" \
  -e AZURE_OPENAI_KEY="$AZURE_OPENAI_KEY" \
  -e AZURE_OPENAI_CHATGPT_DEPLOYMENT="$AZURE_OPENAI_CHATGPT_DEPLOYMENT" \
  -e AZURE_OPENAI_API_VERSION="$AZURE_OPENAI_API_VERSION" \
  resume-rag-app
```

#### 3.5. Check container status
```powershell
# Check if container is running
docker ps --filter name=resume-rag-local

# View logs
docker logs resume-rag-local

# Test application
Invoke-WebRequest http://localhost:5001
```

## 🔍 Verification Steps

1. **Container Health Check:**
   ```powershell
   # Check container is running
   docker ps --filter name=resume-rag-local --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}"
   
   # Test application response
   curl http://localhost:5001
   ```

2. **Test Application Endpoints:**
   ```powershell
   # Main dashboard
   Invoke-WebRequest http://localhost:5001
   
   # Query interface
   Invoke-WebRequest http://localhost:5001/admin/query
   
   # Collections page
   Invoke-WebRequest http://localhost:5001/admin/collections
   
   # API endpoint
   Invoke-WebRequest http://localhost:5001/api/collections
   ```

## 🛠️ Troubleshooting

### Common Issues:

1. **Container fails to start:**
   ```powershell
   # Check logs
   docker logs resume-rag-local
   
   # Check if port is available
   netstat -an | findstr :5001
   ```

2. **Environment variables not loaded:**
   ```powershell
   # Verify .env file format
   Get-Content .env
   
   # Check for special characters or extra spaces
   ```

3. **Docker build fails:**
   ```powershell
   # Check Docker Desktop is running
   docker --version
   
   # Clean up old containers/images
   docker system prune -f
   ```

### Environment Variable Validation:
```powershell
# PowerShell validation script
$required = @("AZURE_OPENAI_ENDPOINT", "AZURE_OPENAI_KEY", "AZURE_OPENAI_CHATGPT_DEPLOYMENT")
foreach ($var in $required) {
    $value = [Environment]::GetEnvironmentVariable($var)
    if (-not $value) {
        Write-Host "❌ Missing: $var" -ForegroundColor Red
    } else {
        Write-Host "✅ Found: $var" -ForegroundColor Green
    }
}
```

## 📱 Application URLs

Once the container is running successfully, access:

- **Main Dashboard**: http://localhost:5001
- **Query Interface**: http://localhost:5001/admin/query  
- **Collection Manager**: http://localhost:5001/admin/collections
- **Database Manager**: http://localhost:5001/admin/database
- **Stats Viewer**: http://localhost:5001/admin/stats

## 🧹 Cleanup

```powershell
# Stop and remove container
docker stop resume-rag-local
docker rm resume-rag-local

# Remove image (optional)
docker rmi resume-rag-app

# Clean up all unused resources
docker system prune -f
```