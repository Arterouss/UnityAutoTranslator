@echo off
title Unity Game Auto-Translator (ID)
cd /d "%~dp0"
echo Membuka Unity Game Auto-Translator...
python main.py
if errorlevel 1 (
    echo.
    echo Terjadi kesalahan saat membuka aplikasi.
    pause
)
