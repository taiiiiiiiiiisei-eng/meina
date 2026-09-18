@echo off
rem めいな共通Python環境選択
set "MEINA_PYTHON="

if exist "%~dp0.venv_new\Scripts\python.exe" set "MEINA_PYTHON=%~dp0.venv_new\Scripts\python.exe"
if not defined MEINA_PYTHON if exist "%~dp0.venv\Scripts\python.exe" set "MEINA_PYTHON=%~dp0.venv\Scripts\python.exe"

if not defined MEINA_PYTHON (
    echo.
    echo めいなのPython環境が見つかりません。
    echo 候補: %~dp0.venv_new\Scripts\python.exe / %~dp0.venv\Scripts\python.exe
    echo.
    exit /b 1
)

echo [Python] %MEINA_PYTHON%
exit /b 0
