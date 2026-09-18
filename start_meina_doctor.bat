@echo off
cd /d "%~dp0"

call "%~dp0meina_env.bat"
if errorlevel 1 (
    pause
    exit /b 1
)

"%MEINA_PYTHON%" meina_doctor.py
echo.
pause
