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

REM 安定版ランチャー: 起動時にpipや旧アップグレードスクリプトを自動実行しない。
"%MEINA_PYTHON%" run_meina.py
pause
