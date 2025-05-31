@echo off
REM Start API Gateway for GPU Cluster

echo Starting GPU Cluster API Gateway...

REM Set environment variables
set REDIS_URL=redis://localhost:6379/0
set LOG_LEVEL=INFO
set DEBUG=false

REM Activate virtual environment if it exists
if exist "venv\Scripts\activate.bat" (
    echo Activating virtual environment...
    call venv\Scripts\activate.bat
)

REM Check if .env file exists, if not copy from example
if not exist ".env" (
    echo Creating .env from example...
    copy .env.example .env
)

REM Install dependencies if needed
echo Checking dependencies...
pip install -r requirements.txt --quiet

REM Start the API Gateway
echo Starting FastAPI server...
uvicorn app.main:app --host 0.0.0.0 --port 8080 --workers 1

pause
