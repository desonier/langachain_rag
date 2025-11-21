# Build Docker container using .env file values
# Usage: .\build_container.ps1

Write-Host "🐳 Building Resume RAG Docker Container with .env Configuration" -ForegroundColor Green
Write-Host "=" * 60

# Function to load .env file
function Load-EnvFile {
    param([string]$Path)
    
    if (-not (Test-Path $Path)) {
        Write-Host "❌ .env file not found at: $Path" -ForegroundColor Red
        Write-Host "📝 Please copy .env.example to .env and fill in your values:" -ForegroundColor Yellow
        Write-Host "   cp .env.example .env" -ForegroundColor Cyan
        exit 1
    }
    
    Write-Host "📁 Loading environment variables from: $Path" -ForegroundColor Blue
    
    # Read and parse .env file
    Get-Content $Path | ForEach-Object {
        if ($_ -match '^([^#][^=]*?)=(.*)$') {
            $name = $matches[1].Trim()
            $value = $matches[2].Trim()
            # Remove quotes if present
            $value = $value -replace '^[''"]|[''"]$', ''
            
            # Set environment variable for current session
            [Environment]::SetEnvironmentVariable($name, $value, [EnvironmentVariableTarget]::Process)
            Write-Host "  ✅ Loaded: $name" -ForegroundColor Green
        }
    }
}

# Check if Docker is running
try {
    docker --version | Out-Null
    if ($LASTEXITCODE -ne 0) { throw }
    Write-Host "✅ Docker is available" -ForegroundColor Green
} catch {
    Write-Host "❌ Docker is not available. Please install and start Docker Desktop." -ForegroundColor Red
    exit 1
}

# Load environment variables from .env file
$envFile = ".\.env"
Load-EnvFile -Path $envFile

# Validate required environment variables
$requiredVars = @(
    "AZURE_OPENAI_ENDPOINT",
    "AZURE_OPENAI_KEY", 
    "AZURE_OPENAI_CHATGPT_DEPLOYMENT"
)

$missingVars = @()
foreach ($var in $requiredVars) {
    $value = [Environment]::GetEnvironmentVariable($var, [EnvironmentVariableTarget]::Process)
    if (-not $value -or $value -eq "your_value_here" -or $value -eq "YOUR_AZURE_OPENAI_ENDPOINT") {
        $missingVars += $var
    }
}

if ($missingVars.Count -gt 0) {
    Write-Host "❌ Missing or placeholder values for required environment variables:" -ForegroundColor Red
    foreach ($var in $missingVars) {
        Write-Host "   - $var" -ForegroundColor Yellow
    }
    Write-Host "📝 Please update your .env file with actual values" -ForegroundColor Yellow
    exit 1
}

# Display configuration (masked for security)
Write-Host "`n🔧 Configuration Summary:" -ForegroundColor Blue
$endpoint = [Environment]::GetEnvironmentVariable("AZURE_OPENAI_ENDPOINT", [EnvironmentVariableTarget]::Process)
$key = [Environment]::GetEnvironmentVariable("AZURE_OPENAI_KEY", [EnvironmentVariableTarget]::Process)
$deployment = [Environment]::GetEnvironmentVariable("AZURE_OPENAI_CHATGPT_DEPLOYMENT", [EnvironmentVariableTarget]::Process)
$apiVersion = [Environment]::GetEnvironmentVariable("AZURE_OPENAI_API_VERSION", [EnvironmentVariableTarget]::Process)

Write-Host "  📡 Endpoint: $endpoint" -ForegroundColor Cyan
Write-Host "  🔑 API Key: $($key.Substring(0, [Math]::Min(8, $key.Length)))..." -ForegroundColor Cyan
Write-Host "  🚀 Deployment: $deployment" -ForegroundColor Cyan
Write-Host "  📅 API Version: $($apiVersion ?? '2024-02-15-preview')" -ForegroundColor Cyan

# Set container and image names
$imageName = "resume-rag-app"
$containerName = "resume-rag-local"
$port = 5001

Write-Host "`n🏗️ Building Docker image..." -ForegroundColor Blue
try {
    docker build -t $imageName . 2>&1 | Tee-Object -Variable buildOutput
    if ($LASTEXITCODE -ne 0) {
        throw "Docker build failed"
    }
    Write-Host "✅ Docker image '$imageName' built successfully" -ForegroundColor Green
} catch {
    Write-Host "❌ Failed to build Docker image" -ForegroundColor Red
    Write-Host $buildOutput -ForegroundColor Red
    exit 1
}

# Stop and remove existing container if it exists
Write-Host "`n🧹 Cleaning up existing containers..." -ForegroundColor Blue
docker stop $containerName 2>$null | Out-Null
docker rm $containerName 2>$null | Out-Null

# Prepare environment variables for container
$envVars = @()
foreach ($var in $requiredVars) {
    $value = [Environment]::GetEnvironmentVariable($var, [EnvironmentVariableTarget]::Process)
    if ($value) {
        $envVars += "-e"
        $envVars += "$var=$value"
    }
}

# Add API version if set
$apiVersion = [Environment]::GetEnvironmentVariable("AZURE_OPENAI_API_VERSION", [EnvironmentVariableTarget]::Process)
if ($apiVersion) {
    $envVars += "-e"
    $envVars += "AZURE_OPENAI_API_VERSION=$apiVersion"
}

# Run the container
Write-Host "🚀 Starting container '$containerName'..." -ForegroundColor Blue
Write-Host "📡 Port mapping: localhost:$port -> container:80" -ForegroundColor Cyan

try {
    $dockerArgs = @("run", "-d", "--name", $containerName, "-p", "${port}:80") + $envVars + @($imageName)
    & docker $dockerArgs
    
    if ($LASTEXITCODE -ne 0) {
        throw "Failed to start container"
    }
    
    Write-Host "✅ Container started successfully" -ForegroundColor Green
    
    # Wait for container to be ready
    Write-Host "`n⏳ Waiting for application to start..." -ForegroundColor Blue
    $maxAttempts = 30
    $attempt = 0
    $ready = $false
    
    do {
        $attempt++
        Start-Sleep -Seconds 2
        try {
            $response = Invoke-WebRequest -Uri "http://localhost:$port" -UseBasicParsing -TimeoutSec 5 -ErrorAction SilentlyContinue
            if ($response.StatusCode -eq 200) {
                $ready = $true
                break
            }
        } catch {
            # Continue waiting
        }
        Write-Host "  ⏳ Attempt $attempt/$maxAttempts - waiting for application..." -ForegroundColor Yellow
    } while ($attempt -lt $maxAttempts -and -not $ready)
    
    if ($ready) {
        Write-Host "✅ Application is ready!" -ForegroundColor Green
        Write-Host "`n🌐 Application URLs:" -ForegroundColor Blue
        Write-Host "  📊 Main Dashboard: http://localhost:$port" -ForegroundColor Cyan
        Write-Host "  🔍 Query Interface: http://localhost:$port/admin/query" -ForegroundColor Cyan
        Write-Host "  📁 Collections: http://localhost:$port/admin/collections" -ForegroundColor Cyan
        Write-Host "  🔧 Database Manager: http://localhost:$port/admin/database" -ForegroundColor Cyan
        
        Write-Host "`n📋 Container Management:" -ForegroundColor Blue
        Write-Host "  🔍 View logs: docker logs $containerName" -ForegroundColor Yellow
        Write-Host "  🛑 Stop: docker stop $containerName" -ForegroundColor Yellow
        Write-Host "  🗑️ Remove: docker rm $containerName" -ForegroundColor Yellow
        Write-Host "  📊 Stats: docker stats $containerName" -ForegroundColor Yellow
        
    } else {
        Write-Host "❌ Application failed to start within $($maxAttempts * 2) seconds" -ForegroundColor Red
        Write-Host "📋 Container logs:" -ForegroundColor Yellow
        docker logs $containerName
    }
    
} catch {
    Write-Host "❌ Failed to start container: $_" -ForegroundColor Red
    exit 1
}

Write-Host "`n🎉 Container build and deployment completed!" -ForegroundColor Green
Write-Host "🔗 Open http://localhost:$port in your browser to access the application" -ForegroundColor Cyan