@echo off
cd /d "%~dp0"

call "%~dp0meina_env.bat"
if errorlevel 1 (
    pause
    exit /b 1
)

echo ============================================================
echo めいな 軽量フルセルフテスト
echo ============================================================
echo.

echo [1/11] 基本静的セルフテスト
"%MEINA_PYTHON%" ci_self_test.py
if errorlevel 1 goto :failed

echo.
echo [2/11] コア・スモークテスト
"%MEINA_PYTHON%" meina_smoke_test.py
if errorlevel 1 goto :failed

echo.
echo [3/11] 音声コマンド統合テスト
"%MEINA_PYTHON%" meina_voice_command_pipeline_self_test.py
if errorlevel 1 goto :failed

echo.
echo [4/11] ルーター境界値テスト
"%MEINA_PYTHON%" command_router_edge_self_test.py
if errorlevel 1 goto :failed

echo.
echo [5/11] コマンド実行経路・フォールバックテスト
"%MEINA_PYTHON%" meina_command_dispatch_self_test.py
if errorlevel 1 goto :failed

echo.
echo [6/11] リマインダー秘書テスト
"%MEINA_PYTHON%" meina_reminders_self_test.py
if errorlevel 1 goto :failed

echo.
echo [7/11] リマインダー秘書安全配線テスト
"%MEINA_PYTHON%" meina_reminder_secretary_v8_self_test.py
if errorlevel 1 goto :failed

echo.
echo [8/11] 音声認識補正テスト
"%MEINA_PYTHON%" meina_voice_intent_self_test.py
if errorlevel 1 goto :failed

echo.
echo [9/11] Twitch自動切り抜きV2配線テスト
"%MEINA_PYTHON%" twitch_auto_clip_self_test.py
if errorlevel 1 goto :failed

echo.
echo [10/11] Twitchライブ監視テスト
"%MEINA_PYTHON%" twitch_live_monitor_self_test.py
if errorlevel 1 goto :failed

echo.
echo [11/11] Twitch投稿メタデータ・キューテスト
"%MEINA_PYTHON%" twitch_publish_metadata_self_test.py
if errorlevel 1 goto :failed
"%MEINA_PYTHON%" twitch_publish_queue_self_test.py
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
