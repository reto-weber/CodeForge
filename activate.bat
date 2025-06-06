@echo off
echo Activating virtual environment...

if exist "venv\Scripts\activate.bat" (
    call venv\Scripts\activate.bat
    echo Virtual environment activated successfully!
    echo You can now run the FastAPI server with: python main.py
) else (
    echo Virtual environment not found!
    echo Please create it first with: python -m venv venv
    echo Then install dependencies with: pip install -r requirements.txt
)
