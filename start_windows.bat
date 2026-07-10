@echo off
echo ===================================================
echo Welcome to GetHired! 
echo We are setting everything up for you. This may take 
echo a minute or two on your first run. Please wait...
echo ===================================================
echo.

echo [1/3] Checking system requirements...
where python >nul 2>nul
if %errorlevel% neq 0 (
    echo [ERROR] Python is not installed. 
    echo Please download and install Python from https://www.python.org/downloads/
    echo Make sure to check the box "Add python.exe to PATH" during installation.
    pause
    exit /b 1
)
where npm >nul 2>nul
if %errorlevel% neq 0 (
    echo [ERROR] Node.js is not installed. 
    echo Please download and install Node.js from https://nodejs.org/
    pause
    exit /b 1
)

echo [2/3] Starting the AI Brain (Backend)...
cd backend
if not exist "venv" (
    echo - Creating a secure local environment...
    python -m venv venv
)
call venv\Scripts\activate.bat
echo - Installing required files...
pip install -r requirements.txt >nul
echo - Waking up the AI...
start /B uvicorn main:app --host 0.0.0.0 --port 8001
cd ..

echo [3/3] Starting the User Interface (Frontend)...
echo - Loading the dashboard...
call npm install >nul
echo.
echo ===================================================
echo SUCCESS! 
echo GetHired is now running. Your web browser will open 
echo automatically in a few seconds.
echo.
echo NOTE: Do not close this black window while you are 
echo using the app. Closing it will turn the app off.
echo ===================================================
echo.
start http://localhost:5173
call npm run dev -- --open

pause
