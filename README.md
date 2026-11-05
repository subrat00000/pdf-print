# PDF Scale & Print

A modular Windows desktop PDF viewer and print-layout utility.

## Features
- Open PDF files from the UI or by passing a PDF path on the command line.
- Render page previews using PDFium.
- Configure A4, A3, Letter, portrait/landscape.
- Configure independent top, bottom, left and right margins in millimetres.
- Manual scale, Fit printable area, Fit width and Actual size.
- Top/centre/bottom and left/centre/right alignment.
- Save a newly composed PDF without modifying the source.
- Print through the native Qt printer dialog.
- Persist user settings using QSettings.
- Basic logging and separation of UI, PDF transformation, rendering and printing.

## Requirements
- Windows 10/11 (also expected to run on other desktop platforms supported by Qt).
- Python 3.10 or newer. Use a Python version supported by the selected PySide6 and pypdfium2 wheels.
- A printer driver installed in Windows for physical printing.

## Setup (Windows CMD)
```bat
py -m venv .venv
.venv\Scripts\activate
python -m pip install --upgrade pip
pip install -r requirements.txt
python main.py
```

Open a PDF directly:
```bat
python main.py "C:\Documents\sample.pdf"
```

## Build an application folder
```bat
pip install pyinstaller
pyinstaller --noconfirm --clean --windowed --onedir ^
  --name PDFScalePrint ^
  --collect-all pypdfium2 ^
  main.py
```

Test the generated `dist\PDFScalePrint\PDFScalePrint.exe` on a clean Windows machine before release.
Do not assume a successful build on a developer PC proves the application is portable.

## Default PDF application
Windows owns the default-app choice. Register the application as a PDF-capable app in the installer/registry with an open command that passes the selected file path, then direct users to:
Settings > Apps > Default apps > .pdf > PDF Scale & Print.

Do not silently overwrite the user's default application or attempt to bypass Windows' UserChoice protection.

## Project layout
```text
pdf_scale_print/
  main.py
  pdfscale/
    __init__.py
    config.py
    logging_config.py
    pdf_service.py
    render_service.py
    print_service.py
    main_window.py
  tests/
    test_layout.py
  requirements.txt
  README.md
```

## Release checklist
- Run automated tests and manual print tests with each supported printer driver.
- Test password-protected, rotated, mixed-size, large and malformed PDFs.
- Test printer non-printable areas, paper-size mismatch and landscape output.
- Verify page count, page range, copies, duplex and colour behaviour with real drivers.
- Include third-party licence notices and the exact PDFium build licence bundle in the installer.
- Code-sign the installer and executable for public distribution.
- Publish version number, changelog, support contact, privacy policy and a reproducible build procedure.
- Do a legal review of all bundled dependencies and their licences before selling.

## Licensing note
This project code is provided as a starting point; choose and add your own application licence before distribution.
PySide6 is available under LGPLv3/GPLv3 and commercial terms. If distributing under LGPL, comply with the applicable LGPL obligations (including notices and relinking requirements). pypdf is BSD-3-Clause. pypdfium2 is Apache-2.0/BSD-3-Clause, and its bundled PDFium binary and dependencies have additional notices that must accompany binary distributions. Check the exact wheel/build you ship. This is not legal advice.


## Performance design
- Interactive preview composes only the currently selected page.
- Preview changes are debounced by 140 ms to reduce redundant work.
- Full-document composition is deferred until Save or Print.
- Background worker integration and large-document stress tests remain release tasks.


## Continuous page viewing and drag-and-drop

- The preview is now a vertically scrolling document view. Use the mouse wheel
  or scrollbar to move through all pages.
- The page counter and page selector follow the page nearest the centre of the
  visible preview. Entering a page number scrolls directly to that page.
- Preview rendering is lazy: visible pages and their immediate neighbours are
  rendered on demand rather than rendering the entire PDF at open time.
- Drag one local `.pdf` file from File Explorer onto the application window to
  open it. Non-PDF files and multi-file drops are rejected. The Open dialog and
  command-line open path also enforce the `.pdf` extension.

Performance note: lazy rendering reduces initial work for long PDFs, but page
composition and rendering are still performed on the GUI thread in this
iteration. Extremely large or complex PDFs can briefly pause while a newly
visible page is rendered. A worker-thread renderer is the next performance step.
