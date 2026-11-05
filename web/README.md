# PDF Scale & Print — Offline-ready browser app

## Important: prepare the folder once while online

The app itself runs locally and does not upload your PDF. The three JavaScript libraries are distributed separately from this project, so this folder includes a one-time downloader.

1. On any Windows PC with internet access, extract this folder.
2. Double-click `download-libraries.bat`.
3. Confirm these three files now exist in `vendor`:
   - `pdf.min.js`
   - `pdf.worker.min.js`
   - `pdf-lib.min.js`
4. Copy the **entire** `PDFScalePrint_Offline_Fixed` folder to the offline Windows PC (USB drive is fine).
5. On the offline PC, double-click `start.bat`. Open `http://127.0.0.1:8765` if the browser does not open automatically.

After step 3, the application has no CDN references and does not need internet access at runtime. Keep the `vendor` folder beside `index.html`.

## Features

- Continuous PDF page viewer with independent scrolling
- Fixed top header, sidebar and viewer toolbar
- Page count and active-page navigation
- Scale, paper size, orientation, margins and alignment
- Print current page, all pages or a selected range
- Download adjusted PDF
- PDF processing takes place locally in the browser

## Notes

- Python 3 is used only as a local static-file server; it does not process PDF contents.
- Browser print preview and printer settings are controlled by the browser and Windows.
- PDF.js and pdf-lib are third-party libraries. See `LICENSE-NOTICES.txt`.
- The PDF.js font warning `TT: undefined function` may appear for unusual embedded fonts; it is separate from the fixed PDF output buffer issue.
