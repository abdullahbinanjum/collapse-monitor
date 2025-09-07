@echo off

REM Navigate to the project directory
cd /d "D:\AI Class\collapse-monitor"

REM Activate the virtual environment
call .\venv\Scripts\activate.bat

REM Run the FastAPI server in the background
start /B uvicorn main:app --host 127.0.0.1 --port 8000

REM Wait for the server to start up (adjust as needed)
timeout /t 10

REM Call the daily report endpoint to trigger the report and email
curl http://127.0.0.1:8000/daily-report

REM Shut down the server (optional, but good practice if not running 24/7)
REM This requires finding the process ID and killing it. A simpler approach is to use a separate script.
REM For simplicity, we'll assume the server stays running. If you need it to shut down, a more robust solution is required.

echo Daily report script finished.