@echo off
setlocal
cd /d "%~dp0"
if not exist vendor mkdir vendor
echo Downloading required libraries. Run this on a PC with internet access.
powershell -NoProfile -ExecutionPolicy Bypass -Command "$ErrorActionPreference='Stop'; Invoke-WebRequest 'https://cdnjs.cloudflare.com/ajax/libs/pdf.js/3.11.174/pdf.min.js' -OutFile 'vendor/pdf.min.js'; Invoke-WebRequest 'https://cdnjs.cloudflare.com/ajax/libs/pdf.js/3.11.174/pdf.worker.min.js' -OutFile 'vendor/pdf.worker.min.js'; Invoke-WebRequest 'https://cdn.jsdelivr.net/npm/pdf-lib@1.17.1/dist/pdf-lib.min.js' -OutFile 'vendor/pdf-lib.min.js'"
if errorlevel 1 (echo Download failed. Check internet access and try again. & pause & exit /b 1)
echo.
echo Libraries installed. Copy this entire folder to the offline PC.
pause
