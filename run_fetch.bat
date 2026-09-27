@echo off
rem Run fetch_trends.py inside the conda env named "trends".
rem Used by Task Scheduler and for a one-click manual fetch on Windows.
setlocal
set "SCRIPT_DIR=%~dp0"
set "ENV_NAME=trends"

where conda >nul 2>&1
if %errorlevel%==0 (
    conda run -n %ENV_NAME% --no-capture-output python "%SCRIPT_DIR%fetch_trends.py"
    exit /b %errorlevel%
)

for %%P in (
    "%USERPROFILE%\miniconda3"
    "%USERPROFILE%\Miniconda3"
    "%USERPROFILE%\anaconda3"
    "%USERPROFILE%\Anaconda3"
    "%USERPROFILE%\miniforge3"
    "%USERPROFILE%\Miniforge3"
    "%LOCALAPPDATA%\miniconda3"
    "%LOCALAPPDATA%\anaconda3"
    "C:\ProgramData\miniconda3"
    "C:\ProgramData\anaconda3"
) do (
    if exist "%%~P\Scripts\conda.exe" (
        "%%~P\Scripts\conda.exe" run -n %ENV_NAME% --no-capture-output python "%SCRIPT_DIR%fetch_trends.py"
        exit /b %errorlevel%
    )
)

echo Could not find conda. Create the env first:
echo   conda env create -f environment.yml
echo then run:
echo   conda activate %ENV_NAME%
echo   python fetch_trends.py
exit /b 1
