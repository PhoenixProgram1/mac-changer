@echo off
cd /d "%~dp0"

net session >nul 2>&1
if %ERRORLEVEL% NEQ 0 (
    echo Requesting admin privileges...
    powershell -Command "Start-Process '%~f0' -Verb RunAs"
    exit /b
)

title MAC Changer - Setup
color 0A

echo.
echo  +----------------------------------+
echo  |      MAC Changer  v1.0.0         |
echo  |       Installing deps...         |
echo  +----------------------------------+
echo.

py --version >nul 2>&1
if %ERRORLEVEL% EQU 0 (
    set PYTHON=py
    goto :install
)

python --version >nul 2>&1
if %ERRORLEVEL% EQU 0 (
    set PYTHON=python
    goto :install
)

echo  [ERROR] Python not found in PATH.
echo  Install from https://python.org and check "Add to PATH".
pause
exit /b 1

:install
echo  [*] Python found. Using: %PYTHON%
echo  [*] Installing requirements...
%PYTHON% -m pip install --upgrade pip --quiet
%PYTHON% -m pip install -r requirements.txt

if %ERRORLEVEL% EQU 0 (
    echo.
    echo  [OK] All dependencies installed!
    echo.
    echo  Usage (run as Administrator):
    echo    python mac_changer.py list
    echo    python mac_changer.py change 0
    echo    python mac_changer.py change 0 -m AA:BB:CC:DD:EE:FF
    echo    python mac_changer.py restore 0
    echo.
) else (
    echo.
    echo  [ERROR] pip install failed. See output above.
    echo.
)

pause
