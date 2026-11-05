# PDF Scale & Print — Browser Extension v1.2.0

A local-first Chrome / Microsoft Edge extension for adjusting PDF page scale, paper size, margins and alignment before printing or downloading an adjusted PDF.

## Install / update

1. Extract this ZIP to a permanent folder.
2. Open `chrome://extensions` (Chrome) or `edge://extensions` (Edge).
3. Run `download-libraries.bat` once from the extracted folder on an internet-connected computer. This fills the `vendor` folder with the PDF libraries. (You only need to do this once.)
4. Remove the older PDF Scale & Print unpacked extension, or use **Reload** if updating the same folder.
5. Enable **Developer mode**.
6. Select **Load unpacked** and choose this extracted folder.
7. Open the extension's **Details** page and set **Site access** to **On all sites**.
8. For local PDFs, also enable **Allow access to file URLs**.

## Local PDF detection

When a local PDF such as `file:///C:/Documents/sample.pdf` is opened in a normal browser tab, the extension listens for the top-level navigation and redirects that tab to the editor.

**Required browser permission:** open the extension's Details page and enable **Allow access to file URLs**. Without this permission the browser may not expose local-file navigation to the extension.

Some browser versions or PDF-viewer paths do not expose local-file navigation consistently. If the editor opens but cannot read the file, use **Open PDF** in the editor or drag the PDF into the drop area. The browser deliberately restricts extensions from reading arbitrary local files without user permission.

The extension cannot modify the built-in Chrome / Edge PDF viewer itself. It opens its own editor page instead.

## Remembered layout

The extension automatically saves the last-used:
- Paper size and orientation
- Scale percentage and scale mode
- Horizontal and vertical alignment
- Top, bottom, left and right margins
- Print selection and page range

Settings are stored with `chrome.storage.local` in the browser profile and restored the next time the editor opens. They remain on that computer/browser profile until the extension's data is cleared or the extension is removed.

## Features

- Continuous PDF page preview and page navigation
- PDF-only file picker and drag-and-drop
- A4, A3, Letter and Legal paper sizes
- Portrait / landscape
- Manual scale, fit to printable area and actual size
- Independent four-side margins
- Horizontal and vertical positioning
- Current page, all pages or custom page range
- Browser print preview
- Download adjusted PDF
- PDF processing is performed locally in the browser

## Troubleshooting

- Confirm **Site access** is set to **On all sites**.
- Confirm **Allow access to file URLs** is enabled for local PDFs.
- After changing permissions, close and reopen the PDF tab.
- Go to `chrome://extensions` / `edge://extensions`, find this extension and inspect **Service worker** errors.
- If a local PDF still does not auto-open, open the extension editor and select the file using **Open PDF**. This is a browser security limitation rather than a PDF processing issue.
- Some online sites use `blob:` URLs, embedded PDF viewers or authentication flows that cannot be intercepted reliably.

## Offline use

Run `download-libraries.bat` once while connected to the internet. The required PDF.js and pdf-lib files are stored in `vendor/`. After that, the extension processes PDFs locally and does not need a network connection for its PDF editing features.

## Privacy

The extension does not upload PDF contents. Layout preferences are saved in the browser's extension storage on this device.
