# Python Dependencies Installation Script - PowerShell Version
# Encoding-safe: Compatible with any system code page
# No Chinese characters in this file to avoid encoding issues

# Error handling
$ErrorActionPreference = "Continue"
$ErrorOccurred = $false

# Set console output to UTF-8
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8
$PSDefaultParameterValues['Out-File:Encoding'] = 'utf8'

# Color output function
function Write-ColorOutput {
    param(
        [string]$Message,
        [string]$Color = "White"
    )
    Write-Host $Message -ForegroundColor $Color
}

function Write-Header {
    param([string]$Title)
    Write-Host ""
    Write-ColorOutput "====================================================================================================" "Blue"
    Write-ColorOutput $Title "Cyan"
    Write-ColorOutput "====================================================================================================" "Blue"
    Write-Host ""
}

# Get script directory and navigate to project root (where requirements_win.txt is)
$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path

# Try to find requirements_win.txt in current directory or parent directory
$RequirementsFile = "requirements_win.txt"
if (Test-Path (Join-Path $ScriptDir $RequirementsFile)) {
    # Script is in project root (e.g., after install)
    Set-Location $ScriptDir
} elseif (Test-Path (Join-Path (Split-Path -Parent $ScriptDir) $RequirementsFile)) {
    # Script is in tools subdirectory (development)
    Set-Location (Split-Path -Parent $ScriptDir)
} else {
    Write-ColorOutput "ERROR: Cannot find $RequirementsFile" "Red"
    Write-ColorOutput "Please run this script from project root or tools directory" "Yellow"
    Read-Host "Press Enter to exit"
    exit 1
}

Write-Host "Working directory: $(Get-Location)"
Write-Host ""

Write-Header "Installing Python Dependencies"

# Check if Python is installed
try {
    $pythonVersion = python --version 2>&1
    if ($LASTEXITCODE -ne 0) {
        throw "Python not found"
    }
    Write-ColorOutput "Detected Python version: $pythonVersion" "Green"
    Write-Host ""
} catch {
    Write-ColorOutput "ERROR: Python not detected. Please install Python 3.8 or higher first." "Red"
    Write-Host ""
    Write-ColorOutput "You can download Python from:" "Yellow"
    Write-ColorOutput "https://www.python.org/downloads/" "Cyan"
    Write-Host ""
    $ErrorOccurred = $true
    Read-Host "Press Enter to exit"
    exit 1
}

# Check if requirements_win.txt exists
if (-not (Test-Path "requirements_win.txt")) {
    Write-ColorOutput "ERROR: requirements_win.txt not found" "Red"
    $ErrorOccurred = $true
    Read-Host "Press Enter to exit"
    exit 1
}

Write-ColorOutput "Installing dependencies..." "Yellow"
Write-Host ""

# Upgrade pip
Write-ColorOutput "Upgrading pip..." "Cyan"
python -m pip install --upgrade pip
if ($LASTEXITCODE -ne 0) {
    Write-ColorOutput "WARNING: pip upgrade failed, but will continue with dependency installation" "Yellow"
}
Write-Host ""

# Install dependencies from requirements_win.txt
Write-ColorOutput "Installing dependencies from requirements_win.txt..." "Cyan"
python -m pip install -r requirements_win.txt
if ($LASTEXITCODE -ne 0) {
    Write-ColorOutput "ERROR: Dependency installation failed" "Red"
    $ErrorOccurred = $true
    Read-Host "Press Enter to exit"
    exit 1
}
Write-Host ""

# Run pywin32 post-install script
Write-Header "Running pywin32 post-install script"

# Check administrator privileges
$isAdmin = ([Security.Principal.WindowsPrincipal][Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)

if (-not $isAdmin) {
    Write-ColorOutput "pywin32 post-install script requires administrator privileges, requesting permissions..." "Yellow"
    
    # Re-run with admin rights
    $arguments = "-NoProfile -ExecutionPolicy Bypass -File `"$PSCommandPath`""
    Start-Process PowerShell -Verb RunAs -ArgumentList $arguments -Wait
    exit
}

# Find pywin32_postinstall.py
$pythonExe = python -c "import sys; print(sys.executable)" 2>$null
$pythonDir = Split-Path -Parent $pythonExe
$postInstallScript = $null

$possiblePaths = @(
    "$pythonDir\Scripts\pywin32_postinstall.py",
    (python -c "import os, sys; print(os.path.join(sys.prefix, 'Scripts', 'pywin32_postinstall.py'))" 2>$null)
)

foreach ($path in $possiblePaths) {
    if (Test-Path $path) {
        $postInstallScript = $path
        break
    }
}

if ($postInstallScript) {
    Write-ColorOutput "Found pywin32 post-install script: $postInstallScript" "Cyan"
    Write-Host ""
    
    python $postInstallScript -install
    if ($LASTEXITCODE -ne 0) {
        Write-ColorOutput "WARNING: pywin32 post-install script execution failed" "Yellow"
        $ErrorOccurred = $true
    } else {
        Write-ColorOutput "pywin32 post-install script executed successfully" "Green"
    }
} else {
    Write-ColorOutput "WARNING: pywin32 post-install script not found, trying to verify installation..." "Yellow"
    Write-Host ""
    
    python -c "import win32api; print('pywin32 is installed correctly')" 2>$null
    if ($LASTEXITCODE -ne 0) {
        Write-ColorOutput "WARNING: pywin32 may not be installed correctly" "Yellow"
        $ErrorOccurred = $true
    } else {
        Write-ColorOutput "pywin32 verified successfully" "Green"
    }
}
Write-Host ""

# End
Write-Header ""
if (-not $ErrorOccurred) {
    Write-ColorOutput "Python dependencies installation completed!" "Green"
} else {
    Write-ColorOutput "Warnings occurred during installation, please check the output above" "Yellow"
}
Write-ColorOutput "====================================================================================================" "Blue"
Write-Host ""

Read-Host "Press Enter to exit"
