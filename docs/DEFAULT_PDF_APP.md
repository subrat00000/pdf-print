# Register PDF Scale & Print as the default PDF viewer

Register the application as a PDF handler during installation, but let the user choose
it as the default. Never silently overwrite another application's default association.

## Windows 11

The installer should register a ProgID and an application open command. Example
Inno Setup entries (adapt paths and add the application's capabilities registration):

```ini
[Registry]
Root: HKCU; Subkey: "Software\Classes\Applications\PDFScalePrint.exe\SupportedTypes"; ValueType: string; ValueName: ".pdf"; ValueData: ""
Root: HKCU; Subkey: "Software\Classes\Applications\PDFScalePrint.exe\shell\open\command"; ValueType: string; ValueName: ""; ValueData: """{app}\PDFScalePrint.exe"" ""%1"""; Flags: uninsdeletekey
Root: HKCU; Subkey: "Software\Classes\PDFScalePrint.Document"; ValueType: string; ValueName: ""; ValueData: "PDF Scale & Print document"; Flags: uninsdeletekey
Root: HKCU; Subkey: "Software\Classes\PDFScalePrint.Document\shell\open\command"; ValueType: string; ValueName: ""; ValueData: """{app}\PDFScalePrint.exe"" ""%1"""
```

For a production installer, also register `Software\PDFScalePrint\Capabilities` with
`ApplicationName`, `ApplicationDescription`, and
`FileAssociations` (`.pdf` = `PDFScalePrint.Document`), then register that capability
under `Software\RegisteredApplications`.

Windows 10/11 protects the user's default choice using the `UserChoice` mechanism.
Do not attempt to write/spoof `UserChoice`. After installation, instruct the user:

1. Settings → Apps → Default apps.
2. Search for `.pdf`.
3. Select PDF Scale & Print and confirm the choice.

The user must make the final default-app choice.

## macOS

Package and sign a `.app` bundle. Add this document type to `Info.plist`:

```xml
<key>CFBundleDocumentTypes</key>
<array>
  <dict>
    <key>CFBundleTypeName</key>
    <string>PDF document</string>
    <key>CFBundleTypeRole</key>
    <string>Viewer</string>
    <key>LSHandlerRank</key>
    <string>Alternate</string>
    <key>LSItemContentTypes</key>
    <array>
      <string>com.adobe.pdf</string>
    </array>
  </dict>
</array>
```

User procedure: Finder → select a PDF → Get Info → Open with → PDF Scale & Print →
Change All.

## Linux

Install a desktop entry named `pdfscaleprint.desktop`:

```ini
[Desktop Entry]
Type=Application
Name=PDF Scale & Print
Exec=/opt/pdfscaleprint/PDFScalePrint %f
Terminal=false
Categories=Office;Viewer;
MimeType=application/pdf;
```

Install it in `/usr/share/applications` or `~/.local/share/applications`, then run:

```bash
update-desktop-database ~/.local/share/applications
xdg-mime default pdfscaleprint.desktop application/pdf
```

Alternatively choose it in the desktop environment's Default Applications settings.

## Cross-platform acceptance tests

Test double-click, Open With, drag-and-drop, filenames containing spaces, multiple
PDF launch requests, uninstall cleanup, and preserving existing user defaults.
