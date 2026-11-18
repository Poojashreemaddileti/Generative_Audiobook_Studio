@echo off
setlocal
cd /d "%~dp0"
echo ================================================
echo   Generative Audiobook Studio - First-time setup
echo ================================================
where py >nul 2>nul
if errorlevel 1 (
  set PYTHON=python
) else (
  set PYTHON=py -3.11
)
if not exist "venv\Scripts\python.exe" (
  echo [1/4] Creating Python virtual environment...
  %PYTHON% -m venv venv
  if errorlevel 1 goto failed
)
call "venv\Scripts\activate.bat"
echo [2/4] Updating pip...
python -m pip install --upgrade pip
if errorlevel 1 goto failed
echo [3/4] Installing CPU PyTorch (GPU is optional)...
python -m pip install torch --index-url https://download.pytorch.org/whl/cpu
if errorlevel 1 goto failed
echo [4/4] Installing project dependencies...
python -m pip install -r backend\requirements.txt
if errorlevel 1 goto failed
if not exist data mkdir data
if not exist data\uploads mkdir data\uploads
echo.
echo Setup completed successfully.
echo Run run.bat to start the studio.
pause
exit /b 0
:failed
echo.
echo Setup failed. Check your internet connection and the error above.
pause
exit /b 1
