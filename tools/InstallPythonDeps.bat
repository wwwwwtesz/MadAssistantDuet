@echo off
REM Python Dependencies Installation Script
REM Compatible with any Windows code page (CP936, CP1252, etc.)
REM Uses only ASCII characters to avoid encoding issues

setlocal enabledelayedexpansion

REM Initialize error flag
set "ErrorOccurred=0"

REM Get script directory
set "SCRIPT_DIR=%~dp0"

REM Try to find requirements_win.txt
REM Check if we are in project root (requirements_win.txt in same directory)
if exist "%SCRIPT_DIR%requirements_win.txt" (
    cd /d "%SCRIPT_DIR%"
    goto :found_requirements
)

REM Check if we are in tools subdirectory (requirements_win.txt in parent)
if exist "%SCRIPT_DIR%..\requirements_win.txt" (
    cd /d "%SCRIPT_DIR%.."
    goto :found_requirements
)

REM requirements_win.txt not found
echo ERROR: Cannot find requirements_win.txt
echo Please run this script from project root or tools directory
set "ErrorOccurred=1"
pause
exit /b 1

:found_requirements
echo Working directory: %CD%
echo.

echo.
echo ====================================================================================================
echo Installing Python Dependencies
echo ====================================================================================================
echo.

REM Check if Python is installed
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo ERROR: Python not detected. Please install Python 3.8 or higher first.
    echo.
    echo You can download Python from:
    echo https://www.python.org/downloads/
    echo.
    set "ErrorOccurred=1"
    goto :end
)

REM Display Python version
echo Detected Python version:
python --version
echo.

REM Check if requirements_win.txt exists
if not exist "requirements_win.txt" (
    echo ERROR: requirements_win.txt not found
    set "ErrorOccurred=1"
    goto :end
)

echo Installing dependencies...
echo.

REM Upgrade pip
echo Upgrading pip...
python -m pip install --upgrade pip
if %errorlevel% neq 0 (
    echo WARNING: pip upgrade failed, but will continue with dependency installation
)
echo.

REM Install dependencies from requirements_win.txt
echo Installing dependencies from requirements_win.txt...
python -m pip install -r requirements_win.txt
if %errorlevel% neq 0 (
    echo ERROR: Dependency installation failed
    set "ErrorOccurred=1"
    goto :end
)
echo.

REM Run pywin32 post-install script
echo ====================================================================================================
echo Running pywin32 post-install script
echo ====================================================================================================
echo.

REM Check for administrator privileges
openfiles >nul 2>&1
if %errorlevel% neq 0 (
    echo pywin32 post-install script requires administrator privileges
    echo Requesting elevation...
    powershell -Command "Start-Process cmd.exe -ArgumentList '/c \"%~f0\"' -Verb RunAs"
    exit /b
)

REM Find Python installation path
for /f "delims=" %%i in ('python -c "import sys; print(sys.executable)"') do set "PYTHON_EXE=%%i"
for %%i in ("%PYTHON_EXE%") do set "PYTHON_DIR=%%~dpi"

REM Try to find pywin32_postinstall.py
set "POSTINSTALL_SCRIPT="
if exist "%PYTHON_DIR%Scripts\pywin32_postinstall.py" (
    set "POSTINSTALL_SCRIPT=%PYTHON_DIR%Scripts\pywin32_postinstall.py"
) else (
    for /f "delims=" %%i in ('python -c "import os, sys; print(os.path.join(sys.prefix, 'Scripts', 'pywin32_postinstall.py'))"') do set "POSTINSTALL_SCRIPT=%%i"
)

if exist "%POSTINSTALL_SCRIPT%" (
    echo Found pywin32 post-install script: %POSTINSTALL_SCRIPT%
    echo.
    python "%POSTINSTALL_SCRIPT%" -install
    if %errorlevel% neq 0 (
        echo WARNING: pywin32 post-install script execution failed
        set "ErrorOccurred=1"
    ) else (
        echo pywin32 post-install script executed successfully
    )
) else (
    echo WARNING: pywin32 post-install script not found
    echo Trying to verify pywin32 installation...
    python -c "import win32api; print('pywin32 is installed correctly')" 2>nul
    if %errorlevel% neq 0 (
        echo WARNING: pywin32 may not be installed correctly
        set "ErrorOccurred=1"
    ) else (
        echo pywin32 verified successfully
    )
)
echo.

:end
echo ====================================================================================================
if %ErrorOccurred% equ 0 (
    echo Python dependencies installation completed!
) else (
    echo Warnings/Errors occurred during installation
    echo Please check the output above for details
)
echo ====================================================================================================
echo.

pause
