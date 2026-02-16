# EventFlow Windows Setup Script
# Run this in PowerShell to set up everything automatically

Write-Host "╔═══════════════════════════════════════════════════════════╗" -ForegroundColor Cyan
Write-Host "║                                                           ║" -ForegroundColor Cyan
Write-Host "║              EventFlow Windows Setup                      ║" -ForegroundColor Cyan
Write-Host "║                                                           ║" -ForegroundColor Cyan
Write-Host "╚═══════════════════════════════════════════════════════════╝" -ForegroundColor Cyan
Write-Host ""

# Function to check if command exists
function Test-Command {
    param($Command)
    try {
        if (Get-Command $Command -ErrorAction Stop) {
            return $true
        }
    }
    catch {
        return $false
    }
}

# Check Docker
Write-Host "🔍 Checking prerequisites..." -ForegroundColor Yellow
Write-Host ""

$dockerInstalled = Test-Command "docker"
$pythonInstalled = Test-Command "python"

if (-not $dockerInstalled) {
    Write-Host "❌ Docker is not installed" -ForegroundColor Red
    Write-Host ""
    Write-Host "Please install Docker Desktop:" -ForegroundColor Yellow
    Write-Host "1. Go to: https://www.docker.com/products/docker-desktop/" -ForegroundColor White
    Write-Host "2. Download Docker Desktop for Windows" -ForegroundColor White
    Write-Host "3. Run the installer" -ForegroundColor White
    Write-Host "4. Restart your computer" -ForegroundColor White
    Write-Host "5. Run this script again" -ForegroundColor White
    Write-Host ""
    Write-Host "Press any key to open Docker download page..."
    $null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")
    Start-Process "https://www.docker.com/products/docker-desktop/"
    exit 1
}

Write-Host "✅ Docker is installed" -ForegroundColor Green
docker --version

if (-not $pythonInstalled) {
    Write-Host "⚠️  Python is not installed (optional)" -ForegroundColor Yellow
    Write-Host ""
    Write-Host "Python is optional. You can:" -ForegroundColor White
    Write-Host "  A) Continue without Python (use API docs to send events)" -ForegroundColor White
    Write-Host "  B) Install Python to use test scripts" -ForegroundColor White
    Write-Host ""
    $choice = Read-Host "Continue without Python? (Y/N)"
    
    if ($choice -ne "Y" -and $choice -ne "y") {
        Write-Host ""
        Write-Host "Please install Python:" -ForegroundColor Yellow
        Write-Host "1. Go to: https://www.python.org/downloads/" -ForegroundColor White
        Write-Host "2. Download Python 3.11 or newer" -ForegroundColor White
        Write-Host "3. Run installer and CHECK 'Add Python to PATH'" -ForegroundColor White
        Write-Host "4. Run this script again" -ForegroundColor White
        Write-Host ""
        Write-Host "Press any key to open Python download page..."
        $null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")
        Start-Process "https://www.python.org/downloads/"
        exit 1
    }
} else {
    Write-Host "✅ Python is installed" -ForegroundColor Green
    python --version
    
    # Install Python dependencies (minimal for scripts)
    Write-Host ""
    Write-Host "📦 Installing Python dependencies for scripts..." -ForegroundColor Yellow
    try {
        # Only install httpx for scripts - everything else runs in Docker
        pip install httpx --quiet
        Write-Host "✅ Python dependencies installed (httpx for scripts)" -ForegroundColor Green
    }
    catch {
        Write-Host "⚠️  Could not install Python dependencies" -ForegroundColor Yellow
        Write-Host "You can still use the system via API docs or PowerShell scripts" -ForegroundColor White
    }
}

Write-Host ""
Write-Host "🚀 Starting EventFlow services..." -ForegroundColor Yellow
Write-Host ""

# Check if Docker Desktop is running
try {
    docker ps | Out-Null
}
catch {
    Write-Host "❌ Docker Desktop is not running" -ForegroundColor Red
    Write-Host ""
    Write-Host "Please start Docker Desktop and run this script again" -ForegroundColor Yellow
    Write-Host "Look for Docker icon in system tray" -ForegroundColor White
    exit 1
}

# Start services
Write-Host "Starting containers..." -ForegroundColor White
docker-compose up -d

if ($LASTEXITCODE -ne 0) {
    Write-Host ""
    Write-Host "❌ Failed to start services" -ForegroundColor Red
    Write-Host ""
    Write-Host "Troubleshooting:" -ForegroundColor Yellow
    Write-Host "1. Make sure Docker Desktop is running" -ForegroundColor White
    Write-Host "2. Try: docker-compose down" -ForegroundColor White
    Write-Host "3. Then: docker-compose up -d" -ForegroundColor White
    exit 1
}

Write-Host ""
Write-Host "⏳ Waiting for services to start (30 seconds)..." -ForegroundColor Yellow
Start-Sleep -Seconds 30

# Check service health
Write-Host ""
Write-Host "🔍 Checking service health..." -ForegroundColor Yellow

try {
    $response = Invoke-RestMethod -Uri "http://localhost:8000/health" -TimeoutSec 10
    if ($response.status -eq "healthy") {
        Write-Host "✅ API is healthy" -ForegroundColor Green
    } else {
        Write-Host "⚠️  API is running but not fully healthy" -ForegroundColor Yellow
    }
}
catch {
    Write-Host "⚠️  Could not connect to API yet" -ForegroundColor Yellow
    Write-Host "Services may still be starting. Wait a minute and try:" -ForegroundColor White
    Write-Host "  curl http://localhost:8000/health" -ForegroundColor White
}

# Success message
Write-Host ""
Write-Host "╔═══════════════════════════════════════════════════════════╗" -ForegroundColor Green
Write-Host "║                                                           ║" -ForegroundColor Green
Write-Host "║              🎉 EventFlow is Ready! 🎉                    ║" -ForegroundColor Green
Write-Host "║                                                           ║" -ForegroundColor Green
Write-Host "╚═══════════════════════════════════════════════════════════╝" -ForegroundColor Green
Write-Host ""

Write-Host "📊 Access Points:" -ForegroundColor Cyan
Write-Host "  • API Docs:   http://localhost:8000/docs" -ForegroundColor White
Write-Host "  • Health:     http://localhost:8000/health" -ForegroundColor White
Write-Host "  • Prometheus: http://localhost:9090" -ForegroundColor White
Write-Host "  • Grafana:    http://localhost:3000 (admin/admin)" -ForegroundColor White
Write-Host ""

if ($pythonInstalled) {
    Write-Host "🧪 Try it out:" -ForegroundColor Cyan
    Write-Host "  python scripts/producer.py --count 100" -ForegroundColor White
    Write-Host "  python scripts/monitor.py" -ForegroundColor White
    Write-Host ""
}

Write-Host "📚 Next Steps:" -ForegroundColor Cyan
Write-Host "  1. Open http://localhost:8000/docs in your browser" -ForegroundColor White
Write-Host "  2. Try the POST /events endpoint" -ForegroundColor White
Write-Host "  3. Read GET_STARTED.md" -ForegroundColor White
Write-Host "  4. Read INTERVIEW_GUIDE.md for interview prep" -ForegroundColor White
Write-Host ""

Write-Host "🔧 Useful Commands:" -ForegroundColor Cyan
Write-Host "  docker-compose ps              # Check status" -ForegroundColor White
Write-Host "  docker-compose logs -f         # View logs" -ForegroundColor White
Write-Host "  docker-compose down            # Stop services" -ForegroundColor White
Write-Host "  docker-compose up -d           # Start services" -ForegroundColor White
Write-Host ""

Write-Host "Press any key to open API documentation in browser..."
$null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")
Start-Process "http://localhost:8000/docs"
