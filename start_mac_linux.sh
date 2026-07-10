#!/bin/bash
echo "==================================================="
echo "Welcome to GetHired!"
echo "We are setting everything up for you. This may take"
echo "a minute or two on your first run. Please wait..."
echo "==================================================="
echo ""

echo "[0/3] Cleaning up old processes..."
curl -s -X POST http://localhost:8001/api/shutdown > /dev/null
sleep 2
if command -v lsof &> /dev/null; then
    lsof -ti:8001 | xargs kill -9 2>/dev/null
    lsof -ti:5173 | xargs kill -9 2>/dev/null
fi

echo "[1/3] Checking system requirements..."
if ! command -v python3 &> /dev/null; then
    echo "[ERROR] Python3 is not installed."
    echo "Please install Python from https://www.python.org/downloads/"
    exit 1
fi
if ! command -v npm &> /dev/null; then
    echo "[ERROR] Node.js is not installed."
    echo "Please install Node.js from https://nodejs.org/"
    exit 1
fi

echo "[2/3] Starting the AI Brain (Backend)..."
cd backend || exit
if [ ! -d "venv" ]; then
    echo "- Creating a secure local environment..."
    python3 -m venv venv
fi
source venv/bin/activate
echo "- Installing required files..."
pip install -r requirements.txt > /dev/null
echo "- Waking up the AI..."
uvicorn main:app --host 0.0.0.0 --port 8001 > /dev/null 2>&1 &
BACKEND_PID=$!
cd .. || exit

echo "[3/3] Starting the User Interface (Frontend)..."
echo "- Loading the dashboard..."
npm install > /dev/null

echo ""
echo "==================================================="
echo "SUCCESS!"
echo "GetHired is now running. Your web browser will open"
echo "automatically in a few seconds."
echo ""
echo "NOTE: Do not close this terminal window while you are"
echo "using the app. Closing it will turn the app off."
echo "==================================================="
echo ""

if command -v xdg-open &> /dev/null; then
    xdg-open http://localhost:5173 &
elif command -v open &> /dev/null; then
    open http://localhost:5173 &
fi

npm run dev

# Cleanup backend when frontend stops
kill $BACKEND_PID
