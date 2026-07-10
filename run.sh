#!/bin/bash
echo "🚀 Starting GetHired Local Environment..."

# Function to handle cleanup on exit
cleanup() {
    echo ""
    echo "🛑 Shutting down GetHired..."
    kill $BACKEND_PID
    kill $FRONTEND_PID
    exit 0
}

# Trap CTRL+C (SIGINT)
trap cleanup SIGINT

# 1. Start the Backend API
echo "1️⃣ Starting Python Backend (AI & Scrapers)..."
cd backend
source venv/bin/activate
uvicorn main:app --host 0.0.0.0 --port 8001 &
BACKEND_PID=$!
cd ..

# 2. Start the Frontend App
echo "2️⃣ Starting React Frontend..."
npm run dev &
FRONTEND_PID=$!

echo ""
echo "✅ App is running!"
echo "🌐 Open your browser to: http://localhost:5173"
echo "Press CTRL+C to stop the application."

# Keep script running
wait
