@echo off
cd /d "%~dp0"

call "%~dp0meina_env.bat"
if errorlevel 1 (
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
