@echo off
setlocal
set "ROOT=%~dp0"
if "%ROOT:~-1%"=="\" set "ROOT=%ROOT:~0,-1%"
cd /d "%ROOT%"

if not exist ".venv\Scripts\activate.bat" (
  echo .venv not found — running setup first ...
  call "%ROOT%\setup.cmd"
  if errorlevel 1 exit /b 1
)

where npm >nul 2>&1
if errorlevel 1 (
  echo ERROR: npm not found on PATH. Install Node.js and try again.
  exit /b 1
)

if not exist "frontend\node_modules" (
  echo Installing frontend dependencies ...
  pushd "%ROOT%\frontend"
  call npm install
  popd
)

echo Starting JobPilot backend ^(port 8000^) and frontend ^(port 5173^) ...
echo Close each terminal window to stop that service.
echo.

REM Stop stale backends on port 8000 (avoids old code handling OAuth callbacks)
for /f "tokens=5" %%a in ('netstat -ano ^| findstr ":8000" ^| findstr "LISTENING"') do (
  taskkill /F /PID %%a >nul 2>&1
)

start "JobPilot Backend" cmd /k "cd /d ""%ROOT%"" && call .venv\Scripts\activate.bat && uvicorn backend.app.main:app --reload --host 0.0.0.0 --port 8000"

start "JobPilot Frontend" cmd /k "cd /d ""%ROOT%\frontend"" && npm run dev"

endlocal
