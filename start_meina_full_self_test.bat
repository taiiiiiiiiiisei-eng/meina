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

echo ============================================================
echo めいな 軽量フルセルフテスト
echo ============================================================
echo.

echo [1/5] 基本静的セルフテスト
"%MEINA_PYTHON%" ci_self_test.py
if errorlevel 1 goto :failed

echo.
echo [2/5] コア・スモークテスト
"%MEINA_PYTHON%" meina_smoke_test.py
if errorlevel 1 goto :failed

echo.
echo [3/5] 音声コマンド統合テスト
"%MEINA_PYTHON%" meina_voice_command_pipeline_self_test.py
if errorlevel 1 goto :failed

echo.
echo [4/5] ルーター境界値テスト
"%MEINA_PYTHON%" command_router_edge_self_test.py
if errorlevel 1 goto :failed

echo.
echo [5/5] 音声認識補正テスト
"%MEINA_PYTHON%" meina_voice_intent_self_test.py
if errorlevel 1 goto :failed

echo.
echo ============================================================
echo ALL LIGHTWEIGHT SELF TESTS PASSED
echo ============================================================
pause
exit /b 0

:failed
echo.
echo ============================================================
echo SELF TEST FAILED
echo ============================================================
pause
exit /b 1
