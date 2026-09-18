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
echo [2/2] めいなGUI起動
"%MEINA_PYTHON%" meina_app.py
pause
