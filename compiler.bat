@echo off
echo ========================================
echo Weather v1.0.0 - Build System
echo ========================================
echo.

REM Check Python
where python >nul 2>nul
if %errorlevel% neq 0 (
    echo ERROR: Python not found!
    pause
    exit /b 1
)

REM Check PyInstaller
python -c "import PyInstaller" >nul 2>nul
if %errorlevel% neq 0 (
    echo ERROR: PyInstaller not installed!
    echo Install with: pip install pyinstaller
    pause
    exit /b 1
)

REM Menu
echo Wat wil je bouwen?
echo.
echo 1. ONEDIR 
echo 2. Installer
echo 3. Alles (1+2) - AANBEVOLEN voor distributie
echo 4. Clean build folders
echo.
set /p choice="Keuze (1-4): "

if "%choice%"=="1" (
    call :build_onedir
    goto end
)
if "%choice%"=="2" (
    call :build_installer
    goto end
)
if "%choice%"=="3" (
    call :build_all
    goto end
)
if "%choice%"=="4" (
    call :clean
    goto end
)
goto end

:build_onedir
echo.
echo [1/2] Bouwen ONEDIR versie...
echo ========================================
pyinstaller --clean weather.spec

if %errorlevel% equ 0 (
    echo [OK] ONEDIR gebouwd in: dist\weather\
    echo.
    echo Structuur:
    dir /b dist\weather | more
    echo.
    echo Test met: dist\weather\weather.exe
) else (
    echo [FAIL] ONEDIR build failed!
    exit /b 1
)

REM Maak ZIP voor distributie
echo.
echo Wil je een ZIP maken voor distributie? (y/n)
set /p zip_choice=
if /i "%zip_choice%"=="y" (
    echo.
    echo [2/2] ZIP maken...
    powershell -Command "Compress-Archive -Path 'dist\Weather' -DestinationPath 'dist\Weather.zip' -Force"
    if exist dist\Weather.zip (
        echo [OK] ZIP aangemaakt: dist\Weather.zip
        dir dist\Weather.zip | findstr "Weather"
    )
)
exit /b 0

:build_installer
echo.
echo Bouwen installer...
echo ========================================
pyinstaller --clean weather_installer.spec

if %errorlevel% equ 0 (
    echo [OK] Weather_Installer.exe gebouwd!
    if exist dist\Weather_Installer.exe dir dist\Weather_Installer.exe | findstr Weather_Installer
) else (
    echo [FAIL] Installer build failed!
    exit /b 1
)
exit /b 0

:build_all
call :build_onedir
if %errorlevel% neq 0 (
    echo Build stopped due to ONEDIR failure
    exit /b 1
)
call :build_installer
if %errorlevel% neq 0 (
    echo Build stopped due to installer failure
    exit /b 1
)
goto summary

:clean
echo.
echo Cleaning build folders...
if exist build rmdir /s /q build
if exist dist rmdir /s /q dist
if exist __pycache__ rmdir /s /q __pycache__
echo [OK] Clean completed
exit /b 0

:summary
echo.
echo ========================================
echo BUILD SUMMARY
echo ========================================

if exist dist\Weather\Weather.exe (
    echo [OK] ONEDIR - dist\Weather\Weather.exe
    echo      Startup: ⚡ INSTANT (0.3-0.5s)
) else (
    echo [  ] ONEDIR - not built
)

if exist dist\Weather.zip (
    echo [OK] ONEDIR ZIP - dist\Weather.zip
    dir dist\Weather.zip | findstr "Weather"
) else (
    echo [  ] ONEDIR ZIP - not created
)

if exist dist\Weather_Installer.exe (
    echo [OK] Installer - dist\Weather_Installer.exe
    dir dist\Weather_Installer.exe | findstr "Weather_Installer"
) else (
    echo [  ] Installer - not built
)
echo ========================================
echo.

echo.
echo Voor GitHub release upload:
echo 1. dist\Weather.zip (Voor handmatige installatie)
echo 2. dist\Weather_Installer.exe (Auto-installer)
echo.
exit /b 0

:end
echo.
echo Done!
pause
