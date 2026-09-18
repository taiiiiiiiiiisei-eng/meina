@echo off
cd /d "%~dp0"

set "MEINA_PYTHON=%~dp0.venv\Scripts\python.exe"

if not exist "%MEINA_PYTHON%" (
    echo.
    echo めいなのPython環境が見つかりません。
    echo 期待する場所: %MEINA_PYTHON%
    echo.
    pause
    exit /b 1
)

echo.
echo [1/2] めいな環境チェック
"%MEINA_PYTHON%" meina_health.py
if errorlevel 1 (
    echo.
    echo 必須環境に問題があります。起動を停止しました。
    pause
    exit /b 1
)

echo.
echo [2/2] めいな起動
"%MEINA_PYTHON%" run_meina.py
pause
