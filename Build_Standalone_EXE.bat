@echo off
title Membangun Standalone UnityAutoTranslator.exe
cd /d "%~dp0"
echo ========================================================
echo   Membangun Standalone EXE untuk Unity Auto-Translator
echo ========================================================
echo.
echo Sedang mengompilasi dengan PyInstaller (proses ini memakan waktu sekitar 1-2 menit)...
pyinstaller --noconsole --onefile --icon=app_icon.ico --add-data "app_icon.ico;." --name "UnityAutoTranslator" --collect-all customtkinter --collect-all UnityPy --collect-all deep_translator main.py

if errorlevel 1 (
    echo.
    echo Gagal membangun EXE! Periksa pesan error di atas.
    pause
    exit /b 1
)

copy /y dist\UnityAutoTranslator.exe UnityAutoTranslator.exe >nul

echo.
echo ========================================================
echo  SUKSES! File EXE mandiri telah dibuat:
echo  %~dp0UnityAutoTranslator.exe
echo ========================================================
echo.
pause
