@echo off
setlocal
cd /d "%~dp0"

if not exist vendor\pdf.min.js (
  echo Missing vendor\pdf.min.js
  echo First run download-libraries.bat on a PC with internet.
  pause
  exit /b 1
)
if not exist vendor\pdf.worker.min.js (
  echo Missing vendor\pdf.worker.min.js
  pause
  exit /b 1
)
if not exist vendor\pdf-lib.min.js (
  echo Missing vendor\pdf-lib.min.js
  pause
  exit /b 1
)

where python >nul 2>nul
if errorlevel 1 (
  echo Python is required on this BUILD computer only.
  echo It will be bundled into the final EXE.
  pause
  exit /b 1
)

echo Installing PyInstaller...
python -m pip install --upgrade pyinstaller
if errorlevel 1 (
  echo Could not install PyInstaller.
  pause
  exit /b 1
)

echo Building portable single-file EXE...
python -m PyInstaller --noconfirm --clean --onefile --windowed --name PDFScalePrint --add-data "index.html;." --add-data "vendor;vendor" launcher.py
if errorlevel 1 (
  echo Build failed.
  pause
  exit /b 1
)

echo.
echo BUILD COMPLETE:
echo dist\PDFScalePrint.exe
echo Copy this EXE to the offline Windows PC.
pause
