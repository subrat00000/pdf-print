@echo off
setlocal

echo Installing build dependencies...
python -m pip install --upgrade pip
python -m pip install PySide6 pypdf pypdfium2 pyinstaller

echo.
echo Building PDF Scale and Print...

pyinstaller ^
    --noconfirm ^
    --clean ^
    --windowed ^
    --onedir ^
    --name PDFScalePrint ^
    --collect-all pypdfium2 ^
    --collect-all PySide6 ^
    --hidden-import=pypdf ^
    main.py

if errorlevel 1 (
    echo BUILD FAILED
    pause
    exit /b 1
)

echo.
echo BUILD SUCCESSFUL
echo Output: dist\PDFScalePrint\PDFScalePrint.exe

pause