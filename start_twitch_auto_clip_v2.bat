@echo off
cd /d "%~dp0"
if exist "..\.venv\Scripts\activate.bat" call "..\.venv\Scripts\activate.bat"
python twitch_ffmpeg_env.py
python twitch_self_test_v2.py
python twitch_auto_clip_v2.py
pause
