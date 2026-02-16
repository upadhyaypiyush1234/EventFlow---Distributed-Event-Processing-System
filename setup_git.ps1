# Git Setup Script for EventFlow

Write-Host "╔═══════════════════════════════════════════════════════════╗" -ForegroundColor Cyan
Write-Host "║                                                           ║" -ForegroundColor Cyan
Write-Host "║              EventFlow Git Setup                          ║" -ForegroundColor Cyan
Write-Host "║                                                           ║" -ForegroundColor Cyan
Write-Host "╚═══════════════════════════════════════════════════════════╝" -ForegroundColor Cyan
Write-Host ""

# Check if Git is installed
try {
    $gitVersion = git --version
    Write-Host "✅ Git is installed: $gitVersion" -ForegroundColor Green
}
catch {
    Write-Host "❌ Git is not installed" -ForegroundColor Red
    Write-Host ""
    Write-Host "Please install Git:" -ForegroundColor Yellow
    Write-Host "1. Go to: https://git-scm.com/download/win" -ForegroundColor White
    Write-Host "2. Download and install Git for Windows" -ForegroundColor White
    Write-Host "3. Restart PowerShell" -ForegroundColor White
    Write-Host "4. Run this script again" -ForegroundColor White
    Write-Host ""
    Write-Host "Press any key to open Git download page..."
    $null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")
    Start-Process "https://git-scm.com/download/win"
    exit 1
}

Write-Host ""

# Check if Git is configured
$userName = git config --global user.name
$userEmail = git config --global user.email

if (-not $userName -or -not $userEmail) {
    Write-Host "⚙️  Git needs to be configured" -ForegroundColor Yellow
    Write-Host ""
    
    if (-not $userName) {
        $userName = Read-Host "Enter your name (for Git commits)"
        git config --global user.name "$userName"
    }
    
    if (-not $userEmail) {
        $userEmail = Read-Host "Enter your email (for Git commits)"
        git config --global user.email "$userEmail"
    }
    
    Write-Host ""
    Write-Host "✅ Git configured:" -ForegroundColor Green
    Write-Host "   Name:  $userName" -ForegroundColor White
    Write-Host "   Email: $userEmail" -ForegroundColor White
}
else {
    Write-Host "✅ Git is already configured:" -ForegroundColor Green
    Write-Host "   Name:  $userName" -ForegroundColor White
    Write-Host "   Email: $userEmail" -ForegroundColor White
}

Write-Host ""

# Check if already a Git repository
if (Test-Path ".git") {
    Write-Host "ℹ️  This is already a Git repository" -ForegroundColor Yellow
    Write-Host ""
    
    $choice = Read-Host "Do you want to see the status? (Y/N)"
    if ($choice -eq "Y" -or $choice -eq "y") {
        git status
    }
}
else {
    Write-Host "📦 Initializing Git repository..." -ForegroundColor Yellow
    git init
    
    if ($LASTEXITCODE -eq 0) {
        Write-Host "✅ Git repository initialized" -ForegroundColor Green
    }
    else {
        Write-Host "❌ Failed to initialize Git repository" -ForegroundColor Red
        exit 1
    }
    
    Write-Host ""
    Write-Host "📝 Adding files to Git..." -ForegroundColor Yellow
    git add .
    
    Write-Host ""
    Write-Host "💾 Creating initial commit..." -ForegroundColor Yellow
    git commit -m "Initial commit: EventFlow distributed event processing system"
    
    if ($LASTEXITCODE -eq 0) {
        Write-Host "✅ Initial commit created" -ForegroundColor Green
    }
    else {
        Write-Host "❌ Failed to create commit" -ForegroundColor Red
        exit 1
    }
}

Write-Host ""
Write-Host "╔═══════════════════════════════════════════════════════════╗" -ForegroundColor Green
Write-Host "║                                                           ║" -ForegroundColor Green
Write-Host "║              ✅ Git Setup Complete! ✅                     ║" -ForegroundColor Green
Write-Host "║                                                           ║" -ForegroundColor Green
Write-Host "╚═══════════════════════════════════════════════════════════╝" -ForegroundColor Green
Write-Host ""

Write-Host "📊 Repository Status:" -ForegroundColor Cyan
git log --oneline -n 5

Write-Host ""
Write-Host "🌐 Next Steps - Push to GitHub:" -ForegroundColor Cyan
Write-Host ""
Write-Host "1. Create a new repository on GitHub:" -ForegroundColor White
Write-Host "   https://github.com/new" -ForegroundColor White
Write-Host ""
Write-Host "2. Link your local repository:" -ForegroundColor White
Write-Host "   git remote add origin https://github.com/YOUR_USERNAME/eventflow.git" -ForegroundColor Yellow
Write-Host "   git branch -M main" -ForegroundColor Yellow
Write-Host "   git push -u origin main" -ForegroundColor Yellow
Write-Host ""
Write-Host "📚 Useful Commands:" -ForegroundColor Cyan
Write-Host "   git status          - Check repository status" -ForegroundColor White
Write-Host "   git add .           - Stage all changes" -ForegroundColor White
Write-Host "   git commit -m 'msg' - Commit changes" -ForegroundColor White
Write-Host "   git push            - Push to GitHub" -ForegroundColor White
Write-Host "   git log --oneline   - View commit history" -ForegroundColor White
Write-Host ""
Write-Host "📖 For more details, see: SETUP_GIT.md" -ForegroundColor Cyan
Write-Host ""
