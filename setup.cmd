@echo off
setlocal
cd /d "%~dp0"

echo JobPilot setup — Python venv + dependencies
echo.

where python >nul 2>&1
if errorlevel 1 (
  echo ERROR: Python not found on PATH. Install Python 3.11+ and try again.
  exit /b 1
)

if not exist ".venv\Scripts\python.exe" (
  echo Creating virtual environment in .venv ...
  python -m venv .venv
  if errorlevel 1 (
    echo ERROR: Failed to create .venv
    exit /b 1
  )
) else (
  echo Virtual environment already exists: .venv
)

call .venv\Scripts\activate.bat
python -m pip install --upgrade pip
pip install -r requirements.txt
if errorlevel 1 (
  echo ERROR: pip install failed
  exit /b 1
)

where npm >nul 2>&1
if errorlevel 1 (
  echo WARNING: npm not found — skip frontend npm install
) else (
  if exist "frontend\package.json" (
    echo.
    echo Installing frontend dependencies ...
    pushd frontend
    call npm install
    popd
  )
)

echo.
echo Setup complete.
echo Run dev.cmd to start backend and frontend in separate terminals.
endlocal
