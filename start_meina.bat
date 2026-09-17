@echo off
cd /d "%~dp0"
if exist ".venv\Scripts\activate.bat" call ".venv\Scripts\activate.bat"
py upgrade_meina.py
py upgrade_meina_v3.py
py upgrade_meina_twitch.py
py upgrade_meina_twitch_v2.py
py upgrade_meina_pc_status.py
py upgrade_meina_task_plan.py
py meina_agent.py
pause
