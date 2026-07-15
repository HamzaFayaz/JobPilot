@echo off
setlocal
cd /d "%~dp0"

if not exist ".venv\Scripts\python.exe" (
  echo Creating worker venv...
  python -m venv .venv
)

echo Installing build dependencies...
".venv\Scripts\python.exe" -m pip install -q -r requirements-build.txt

echo Building JobPilot-SearchHelper.exe ...
".venv\Scripts\pyinstaller.exe" --noconfirm build.spec
set BUILD_EXIT=%ERRORLEVEL%

if not "%BUILD_EXIT%"=="0" (
  echo.
  echo Build failed ^(exit %BUILD_EXIT%^). If you see "Access is denied", close JobPilot-SearchHelper from the tray first.
  exit /b %BUILD_EXIT%
)

if exist "dist\JobPilot-SearchHelper.exe" (
  echo.
  echo Build OK: %cd%\dist\JobPilot-SearchHelper.exe
) else (
  echo Build failed — exe not found.
  exit /b 1
)
