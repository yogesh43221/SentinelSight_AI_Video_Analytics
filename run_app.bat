@echo off
echo ===================================
echo Starting SentinelSight AI Platform
echo ===================================

echo 1. Starting Backend Server...
start "SentinelSight Backend" cmd /k "venv\Scripts\activate && python -m uvicorn backend.api.main:app --reload --host 0.0.0.0 --port 8000"

echo 2. Starting Frontend Dashboard...
cd frontend
start "SentinelSight Frontend" cmd /k "npm run dev"

echo ===================================
echo System is starting up!
echo Access the dashboard at: http://localhost:3000
echo ===================================
pause
