# ORCHA Server Startup Script
# Run this script to start the server on port 8000

Write-Host "🚀 Starting ORCHA Server on port 8000..." -ForegroundColor Cyan
Write-Host ""

# Check if virtual environment exists
if (-Not (Test-Path "venv")) {
    Write-Host "⚠️  Virtual environment not found. Please run setup.ps1 first!" -ForegroundColor Yellow
    exit 1
}

# Activate virtual environment
Write-Host "📦 Activating virtual environment..." -ForegroundColor Green
.\venv\Scripts\Activate.ps1

# Start server on port 8000
Write-Host "🌐 Starting server at http://localhost:8000" -ForegroundColor Green
Write-Host "📚 API Documentation will be available at http://localhost:8000/docs" -ForegroundColor Cyan
Write-Host ""

uvicorn app.main:app --reload --host 0.0.0.0 --port 8000



