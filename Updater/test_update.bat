@echo off
REM Test script voor updater
REM Dit script simuleert een update scenario

echo ========================================
echo Weather Updater Test
echo ========================================
echo.

REM Check of updater.exe bestaat
if not exist "updater.exe" (
    echo FOUT: updater.exe niet gevonden!
    echo Compileer eerst met compile_updater.bat
    pause
    exit /b 1
)

REM Check of er een test URL is opgegeven
if "%1"=="" (
    echo Gebruik: test_update.bat [DOWNLOAD_URL]
    echo.
    echo Voorbeeld:
    echo test_update.bat "https://github.com/Rog294super/Weather-App/releases/tag/v1.0.0/Weather.exe"
    echo.
    pause
    exit /b 1
)

set DOWNLOAD_URL=%1
set TARGET_PATH=%CD%\..\Weather.exe

echo Download URL: %DOWNLOAD_URL%
echo Target Path:  %TARGET_PATH%
echo.
echo Druk op een toets om de update te starten...
pause >nul

echo.
echo Starten van updater...
echo.

updater.exe "%DOWNLOAD_URL%" "%TARGET_PATH%"

echo.
echo Test voltooid!
pause
