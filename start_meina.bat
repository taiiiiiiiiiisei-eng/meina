@echo off
cd /d "%~dp0"
if exist ".venv\Scripts\activate.bat" call ".venv\Scripts\activate.bat"
python upgrade_meina.py
python upgrade_meina_v3.py
python upgrade_meina_v4.py
python upgrade_meina_twitch.py
python run_meina.py
pause
