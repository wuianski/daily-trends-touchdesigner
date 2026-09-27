@echo off
rem Registers a Windows scheduled task that runs fetch_trends.py daily at 06:00.
rem Run from a terminal or double-click. No admin rights needed (per-user task).
rem To remove the task later:  schtasks /Delete /TN "TrendsFetch" /F

set "SCRIPT_DIR=%~dp0"
set "TASK_NAME=TrendsFetch"

rem Create (or overwrite) the daily 06:00 task.
rem run_fetch.bat locates conda and runs fetch_trends.py inside the "trends" env.
schtasks /Create /TN "%TASK_NAME%" /TR "\"%SCRIPT_DIR%run_fetch.bat\"" /SC DAILY /ST 06:00 /F
if errorlevel 1 (
    echo Failed to create the scheduled task.
    pause
    exit /b 1
)

rem Enable "run as soon as possible after a missed start" and allow running
rem on battery, which schtasks alone cannot configure.
powershell -NoProfile -Command ^
  "Set-ScheduledTask -TaskName '%TASK_NAME%' -Settings (New-ScheduledTaskSettingsSet -StartWhenAvailable -AllowStartIfOnBatteries -DontStopIfGoingOnBatteries)"

echo.
echo Task "%TASK_NAME%" registered. Verify with:
echo   schtasks /Query /TN "%TASK_NAME%"
pause
