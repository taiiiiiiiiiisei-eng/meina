@echo off
cd /d "%~dp0"

REM めいなの実際に動作確認済みのPython環境を使用
set "MEINA_PYTHON=C:\Users\taiii\OneDrive\Desktop\meina\.venv\Scripts\python.exe"

if exist "%MEINA_PYTHON%" (
    "%MEINA_PYTHON%" meina_app.py
    pause
    exit /b
)

echo.
echo Python環境が見つかりません。
echo 確認先: %MEINA_PYTHON%
echo.
pause
