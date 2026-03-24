@echo off
echo Starting Claim Verification Backend...
cd /d "%~dp0"
python -m uvicorn main:app --reload
pause
