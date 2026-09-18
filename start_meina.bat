@echo off
cd /d "%~dp0"
if exist ".venv\Scripts\activate.bat" call ".venv\Scripts\activate.bat"

REM Neural TTS依存関係を自動確認・インストール
py -m pip install -r requirements.txt --disable-pip-version-check
if errorlevel 1 (
    echo ⚠️ 依存関係のインストールに失敗しました。既存の環境で起動を続けます。
)
py upgrade_meina.py
py upgrade_meina_v3.py
py upgrade_meina_twitch.py
py upgrade_meina_twitch_v2.py
py upgrade_meina_pc_status.py
py upgrade_meina_task_plan.py
py upgrade_meina_memory.py
py upgrade_meina_reminders.py
py upgrade_meina_reminders_v4.py
py upgrade_meina_reminders_v5.py
py upgrade_meina_reminders_v7.py
py meina_agent.py
pause
