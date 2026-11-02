@echo off
cd /d "%~dp0"
powershell.exe -NoProfile -ExecutionPolicy Bypass -File "%~dp0Setup-AgentChat.ps1"
if errorlevel 1 echo Setup did not finish. Please read the message above before closing this window.
pause
