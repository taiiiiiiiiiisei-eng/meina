@echo off
cd /d "%~dp0"

REM .venv_newを優先して使用
if exist ".venv_new\Scripts\python.exe" (
    ".venv_new\Scripts\python.exe" meina_app.py
    pause
    exit /b
)

REM .venvが使える場合
if exist ".venv\Scripts\python.exe" (
    ".venv\Scripts\python.exe" meina_app.py
    pause
    exit /b
)

echo.
echo ❌ Python環境が見つかりません。
echo .venv_new または .venv が必要です。
echo.
pause
