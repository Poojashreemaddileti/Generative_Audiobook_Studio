@echo off
setlocal
cd /d "%~dp0"
if not exist "venv\Scripts\python.exe" (
  echo Project setup has not been completed yet.
  echo Please double-click setup.bat first.
  pause
  exit /b 1
)
call "venv\Scripts\activate.bat"
if not exist data mkdir data
if not exist data\uploads mkdir data\uploads
echo Starting Generative Audiobook Studio...
echo Keep this window open while using the app.
echo Open http://127.0.0.1:5000 in your browser.
python backend\app.py
if errorlevel 1 (
  echo.
  echo The app stopped because of an error. Read the message above.
  pause
)
