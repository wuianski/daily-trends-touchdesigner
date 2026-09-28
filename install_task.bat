@echo off
rem Registers a Windows scheduled task that runs fetch_trends.py daily at 06:00.
rem Run from a terminal or double-click. No admin rights needed (per-user task).
rem To remove the task later:  schtasks /Delete /TN "TrendsFetch" /F
rem
rem Sleep: WakeToRun tries to wake the laptop at 06:00.
rem If it stayed asleep / closed, StartWhenAvailable runs the fetch on next wake.

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

rem Flags schtasks cannot set: run after a missed 06:00, run on battery, wake from sleep.
powershell -NoProfile -Command ^
  "Set-ScheduledTask -TaskName '%TASK_NAME%' -Settings (New-ScheduledTaskSettingsSet -StartWhenAvailable -AllowStartIfOnBatteries -DontStopIfGoingOnBatteries -WakeToRun)"

rem Allow this PC's power plan to honor wake timers (sleep -> 06:00).
powercfg /SETACVALUEINDEX SCHEME_CURRENT SUB_SLEEP RTCWAKE 1
powercfg /SETDCVALUEINDEX SCHEME_CURRENT SUB_SLEEP RTCWAKE 1
powercfg /SETACTIVE SCHEME_CURRENT

echo.
echo Task "%TASK_NAME%" registered.
echo Verify:  schtasks /Query /TN "%TASK_NAME%" /V /FO LIST
echo Wake from sleep also needs Power Options -^> Sleep -^> Allow wake timers = Enable.
echo If 06:00 was missed, the fetch runs as soon as the laptop is awake again.
pause
