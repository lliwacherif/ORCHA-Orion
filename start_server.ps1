# Start ORCHA Server
Write-Host "Starting ORCHA Server on port 8000..." -ForegroundColor Cyan
Write-Host ""

# Activate virtual environment
.\venv\Scripts\Activate.ps1

# Start server
Write-Host "Server starting at http://localhost:8000" -ForegroundColor Green
Write-Host "API Docs at http://localhost:8000/docs" -ForegroundColor Cyan
Write-Host ""
Write-Host "Press Ctrl+C to stop the server" -ForegroundColor Yellow
Write-Host ""

uvicorn app.main:app --reload --host 0.0.0.0 --port 8000



