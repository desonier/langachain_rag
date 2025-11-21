# Quick Docker Container Test Guide

## 🚀 Method 1: Simple Build & Run (Fastest)

### Step 1: Create .env file first
```powershell
# Create .env file with your values
@"
AZURE_OPENAI_ENDPOINT=https://your-openai-resource.openai.azure.com/
AZURE_OPENAI_KEY=your_actual_api_key_here
AZURE_OPENAI_CHATGPT_DEPLOYMENT=gpt-4
AZURE_OPENAI_API_VERSION=2024-02-15-preview
"@ | Out-File -FilePath .env -Encoding utf8
```

### Step 2: Build Docker image
```powershell
docker build -t resume-rag-app .
```

### Step 3: Run with environment variables
```powershell
# Load environment variables from .env
Get-Content .env | ForEach-Object {
    if ($_ -match '^([^#][^=]*?)=(.*)$') {
        $name = $matches[1].Trim()
        $value = $matches[2].Trim() -replace '^[''"]|[''"]$', ''
        [Environment]::SetEnvironmentVariable($name, $value, [EnvironmentVariableTarget]::Process)
    }
}

# Run container with environment variables
docker run -d --name resume-rag-test -p 5001:80 `
  -e AZURE_OPENAI_ENDPOINT=$env:AZURE_OPENAI_ENDPOINT `
  -e AZURE_OPENAI_KEY=$env:AZURE_OPENAI_KEY `
  -e AZURE_OPENAI_CHATGPT_DEPLOYMENT=$env:AZURE_OPENAI_CHATGPT_DEPLOYMENT `
  -e AZURE_OPENAI_API_VERSION=$env:AZURE_OPENAI_API_VERSION `
  resume-rag-app
```

### Step 4: Test the application
```powershell
# Wait a moment for startup, then test
Start-Sleep -Seconds 10

# Test main endpoint
Invoke-WebRequest http://localhost:5001

# Check container logs
docker logs resume-rag-test

# Check container status
docker ps --filter name=resume-rag-test
```

## 🔧 Method 2: Using Docker Compose (Recommended)

### Create docker-compose.yml
```yaml
services:
  resume-rag:
    build: .
    ports:
      - "5001:80"
    env_file:
      - .env
    environment:
      - FLASK_ENV=production
    restart: unless-stopped
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:80/"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 40s
```

### Run with Docker Compose
```powershell
# Build and run
docker-compose up --build -d

# View logs
docker-compose logs -f

# Stop
docker-compose down
```

## 🧪 Method 3: Test Without Building (Use Pre-built Image)

If you want to test the app logic without building:

```powershell
# Run your app directly with Python (not containerized)
& .\.venv\Scripts\Activate.ps1

# Set environment variables
Get-Content .env | ForEach-Object {
    if ($_ -match '^([^#][^=]*?)=(.*)$') {
        $name = $matches[1].Trim()
        $value = $matches[2].Trim() -replace '^[''"]|[''"]$', ''
        $env:$name = $value
    }
}

# Run the Flask app directly
cd common_tools/openwebui-resume-rag-admin/src
python main.py
```

## 🔍 Quick Test Commands

### Container Health Check
```powershell
# Test all endpoints
$endpoints = @("/", "/admin/collections", "/admin/query", "/api/collections")
foreach ($endpoint in $endpoints) {
    try {
        $response = Invoke-WebRequest "http://localhost:5001$endpoint" -UseBasicParsing
        Write-Host "✅ $endpoint : $($response.StatusCode)"
    } catch {
        Write-Host "❌ $endpoint : Failed"
    }
}
```

### Container Management
```powershell
# View logs
docker logs resume-rag-test --tail 50

# Restart container
docker restart resume-rag-test

# Stop and remove
docker stop resume-rag-test
docker rm resume-rag-test

# Clean up
docker system prune -f
```

## 📱 Application URLs

Once running, access:
- **Main Dashboard**: http://localhost:5001
- **Query Interface**: http://localhost:5001/admin/query
- **Collections**: http://localhost:5001/admin/collections  
- **Database Manager**: http://localhost:5001/admin/database

## ⚠️ Troubleshooting

### Build Issues
```powershell
# If build fails, try rebuilding without cache
docker build --no-cache -t resume-rag-app .

# Check Docker daemon
docker version
```

### Runtime Issues
```powershell
# Check if port is in use
netstat -an | findstr :5001

# Test with different port
docker run -d --name resume-rag-test -p 5002:80 resume-rag-app
```

### Environment Variables Not Working
```powershell
# Verify .env file format (no spaces around =)
Get-Content .env

# Test environment loading
Get-Content .env | ForEach-Object {
    if ($_ -match '^([^#][^=]*?)=(.*)$') {
        Write-Host "$($matches[1]) = $($matches[2])"
    }
}
```