# PowerShell script to activate the virtual environment and start the FastAPI server
# Usage: .\activate.ps1

Write-Host "Activating virtual environment..." -ForegroundColor Green

# Check if virtual environment exists
if (Test-Path ".\venv\Scripts\Activate.ps1") {
    # Activate the virtual environment
    .\venv\Scripts\Activate.ps1
    
    Write-Host "Virtual environment activated successfully!" -ForegroundColor Green
    Write-Host "You can now run the FastAPI server with: python main.py" -ForegroundColor Yellow
    Write-Host "Or run it directly with: .\run_server.ps1" -ForegroundColor Yellow
} else {
    Write-Host "Virtual environment not found!" -ForegroundColor Red
    Write-Host "Please create it first with: python -m venv venv" -ForegroundColor Yellow
    Write-Host "Then install dependencies with: pip install -r requirements.txt" -ForegroundColor Yellow
}
