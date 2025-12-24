@echo off
REM ======================================================
REM Project Startup Script
REM Author: Skippy the Code Slayer (with Big G)
REM ======================================================

E:
cd projects\qr_watermark_wizard
REM Create venv only if it doesn't already exist
if not exist ".venv" (
    echo Creating virtual environment...
    python -m venv .venv
)

REM Activate the virtual environment
echo Activating virtual environment...
call .\.venv\Scripts\activate

REM Install requirements
echo Installing required packages...
pip install --upgrade pip
pip install -r requirements.txt

REM Launch the app
echo Starting application...
python main_ui.py

REM Pause so the console window stays open after execution
pause
