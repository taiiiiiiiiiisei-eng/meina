@echo off
cd /d "%~dp0"

set "MEINA_PYTHON="

if exist "%~dp0.venv_new\Scripts\python.exe" set "MEINA_PYTHON=%~dp0.venv_new\Scripts\python.exe"
if not defined MEINA_PYTHON if exist "%~dp0.venv\Scripts\python.exe" set "MEINA_PYTHON=%~dp0.venv\Scripts\python.exe"

if not defined MEINA_PYTHON (
    echo.
    echo めいなのPython環境が見つかりません。
    echo 候補: %~dp0.venv_new\Scripts\python.exe / %~dp0.venv\Scripts\python.exe
    echo.
    pause
    exit /b 1
)

"%MEINA_PYTHON%" meina_doctor.py
echo.
pause
