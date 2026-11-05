@echo off
setlocal

cd /d "%~dp0"

if not exist vendor mkdir vendor
if not exist temp mkdir temp

echo Downloading PDF.js...
curl.exe -L --fail "https://registry.npmjs.org/pdfjs-dist/-/pdfjs-dist-3.11.174.tgz" -o "temp\pdfjs.tgz"
if errorlevel 1 goto error

echo Downloading pdf-lib...
curl.exe -L --fail "https://registry.npmjs.org/pdf-lib/-/pdf-lib-1.17.1.tgz" -o "temp\pdf-lib.tgz"
if errorlevel 1 goto error

echo Extracting libraries...
tar.exe -xzf "temp\pdfjs.tgz" -C temp
if errorlevel 1 goto error

move /Y "temp\package\build\pdf.min.js" "vendor\pdf.min.js"
move /Y "temp\package\build\pdf.worker.min.js" "vendor\pdf.worker.min.js"

rmdir /S /Q temp\package

tar.exe -xzf "temp\pdf-lib.tgz" -C temp
if errorlevel 1 goto error

move /Y "temp\package\dist\pdf-lib.min.js" "vendor\pdf-lib.min.js"

rmdir /S /Q temp
echo.
echo Libraries downloaded successfully.
pause
exit /b 0

:error
echo.
echo ERROR: Download or extraction failed.
echo Check your internet connection and try again.
pause
exit /b 1