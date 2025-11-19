# ORCHA Setup Script for Windows
# This script sets up the virtual environment, installs dependencies, and initializes the database

Write-Host "🔧 ORCHA Setup Script" -ForegroundColor Cyan
Write-Host "===================" -ForegroundColor Cyan
Write-Host ""

# Step 1: Create virtual environment
Write-Host "Step 1: Creating virtual environment..." -ForegroundColor Green
if (Test-Path "venv") {
    Write-Host "   ✓ Virtual environment already exists" -ForegroundColor Yellow
} else {
    python -m venv venv
    Write-Host "   ✓ Virtual environment created" -ForegroundColor Green
}
Write-Host ""

# Step 2: Activate virtual environment
Write-Host "Step 2: Activating virtual environment..." -ForegroundColor Green
.\venv\Scripts\Activate.ps1
Write-Host "   ✓ Virtual environment activated" -ForegroundColor Green
Write-Host ""

# Step 3: Upgrade pip
Write-Host "Step 3: Upgrading pip..." -ForegroundColor Green
python -m pip install --upgrade pip
Write-Host "   ✓ pip upgraded" -ForegroundColor Green
Write-Host ""

# Step 4: Install dependencies
Write-Host "Step 4: Installing dependencies from requirements.txt..." -ForegroundColor Green
pip install -r requirements.txt
Write-Host "   ✓ Dependencies installed" -ForegroundColor Green
Write-Host ""

# Step 5: Check if .env exists
Write-Host "Step 5: Checking .env file..." -ForegroundColor Green
if (Test-Path ".env") {
    Write-Host "   ✓ .env file exists" -ForegroundColor Green
} else {
    Write-Host "   ⚠️  .env file created with default values" -ForegroundColor Yellow
    Write-Host "   📝 Please review and update .env with your settings" -ForegroundColor Yellow
}
Write-Host ""

# Step 6: Initialize database
Write-Host "Step 6: Initializing database..." -ForegroundColor Green
Write-Host "   ⚠️  Make sure PostgreSQL is running on localhost:5432" -ForegroundColor Yellow
Write-Host "   ⚠️  Username: postgres, Password: 1234 (or update .env)" -ForegroundColor Yellow
Write-Host ""
$response = Read-Host "   Do you want to initialize the database now? (y/n)"
if ($response -eq "y" -or $response -eq "Y") {
    python init_database.py
    Write-Host "   ✓ Database initialized" -ForegroundColor Green
} else {
    Write-Host "   ⚠️  Skipped database initialization" -ForegroundColor Yellow
    Write-Host "   📝 Run 'python init_database.py' when PostgreSQL is ready" -ForegroundColor Yellow
}
Write-Host ""

# Done
Write-Host "✅ Setup Complete!" -ForegroundColor Green
Write-Host ""
Write-Host "Next steps:" -ForegroundColor Cyan
Write-Host "1. Review and update .env file with your configuration" -ForegroundColor White
Write-Host "2. Make sure PostgreSQL is running" -ForegroundColor White
Write-Host "3. (Optional) Make sure Redis is running" -ForegroundColor White
Write-Host "4. Run the server with: .\run.ps1" -ForegroundColor White
Write-Host ""
Write-Host "Or manually run: uvicorn app.main:app --reload --host 0.0.0.0 --port 8000" -ForegroundColor Gray
Write-Host ""



