@echo off
echo ==============================================================
echo 🚀 GetHired Engine Startup
echo ==============================================================

echo [1/3] Setting up Python Backend...
cd backend
if not exist venv (
    echo Creating virtual environment...
    python -m venv venv
)
call venv\Scripts\activate.bat
echo Installing Python dependencies...
pip install -r requirements.txt > nul
echo Starting FastAPI Backend...
start /b uvicorn main:app --host 0.0.0.0 --port 8001
cd ..

echo.
echo [2/3] Setting up React Frontend...
echo Installing Node modules (this might take a minute on first run)...
call npm install > nul

echo.
echo [3/3] Launching GetHired...
echo The app will open in your default browser.
echo Leave this window open while you use the app!
echo ==============================================================
call npm run dev
