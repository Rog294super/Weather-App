@echo off
echo ========================================
echo Compileren van Weather Updater
echo ========================================
echo.

REM Check of g++ beschikbaar is
where g++ >nul 2>nul
if %errorlevel% neq 0 (
    echo FOUT: g++ niet gevonden!
    echo Installeer MinGW-w64 of MSYS2 eerst.
    pause
    exit /b 1
)

echo Compileren van updater_final.cpp...
g++ -o updater.exe updater_final.cpp ^
    -municode ^
    -std=c++17 ^
    -O2 ^
    -s ^
    -static ^
    -static-libgcc ^
    -static-libstdc++ ^
    -lurlmon ^
    -lshlwapi ^
    -mwindows

if %errorlevel% equ 0 (
    echo.
    echo ========================================
    echo Compilatie GESLAAGD!
    echo ========================================
    echo.
    echo updater.exe is aangemaakt
    echo Grootte: 
    dir updater.exe | findstr updater.exe
    echo.
) else (
    echo.
    echo ========================================
    echo Compilatie MISLUKT!
    echo ========================================
    echo.
)

pause
