import sys
from pathlib import Path
from PySide6.QtWidgets import QApplication
from pdfscale.logging_config import configure_logging
from pdfscale.main_window import MainWindow

def main() -> int:
    configure_logging()
    app = QApplication(sys.argv)
    app.setApplicationName("PDF Scale & Print")
    app.setOrganizationName("PDFScalePrint")
    window = MainWindow()
    window.show()
    if len(sys.argv) > 1:
        candidate = Path(sys.argv[1]).expanduser()
        if candidate.is_file() and candidate.suffix.lower() == ".pdf":
            window.open_path(str(candidate))
    return app.exec()

if __name__ == "__main__":
    raise SystemExit(main())
