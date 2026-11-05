from __future__ import annotations

import pypdfium2 as pdfium
from PySide6.QtCore import QRectF, QMarginsF
from PySide6.QtGui import QPainter, QImage, QPageSize, QPageLayout
from PySide6.QtPrintSupport import QPrinter

PAPER_IDS = {
    "A4": QPageSize.PageSizeId.A4,
    "A3": QPageSize.PageSizeId.A3,
    "Letter": QPageSize.PageSizeId.Letter,
}

def configure_printer(printer: QPrinter, settings) -> None:
    page_size = QPageSize(PAPER_IDS[settings.paper])
    orientation = (
        QPageLayout.Orientation.Landscape
        if settings.orientation == "Landscape"
        else QPageLayout.Orientation.Portrait
    )
    layout = QPageLayout(
        page_size,
        orientation,
        QMarginsF(0, 0, 0, 0),
        QPageLayout.Unit.Millimeter,
    )
    printer.setPageLayout(layout)
    # The composed PDF already contains the requested margins. Full-page
    # coordinates are therefore required to preserve its physical placement.
    printer.setFullPage(True)

def print_pdf_bytes(pdf_bytes: bytes, printer: QPrinter) -> None:
    doc = pdfium.PdfDocument(pdf_bytes)
    painter = QPainter()
    try:
        if not painter.begin(printer):
            raise RuntimeError("Unable to start the printer painter.")

        dpi = printer.resolution()
        paper_rect = printer.paperRect(QPrinter.Unit.DevicePixel)
        for index in range(len(doc)):
            if index and not printer.newPage():
                raise RuntimeError("The printer could not start the next page.")

            page = doc[index]
            bitmap = page.render(scale=dpi / 72.0)
            pil = bitmap.to_pil().convert("RGB")
            image = QImage(
                pil.tobytes(),
                pil.width,
                pil.height,
                pil.width * 3,
                QImage.Format.Format_RGB888,
            ).copy()

            # Preserve aspect ratio if the user changes paper size in the
            # native print dialog or the driver reports a slightly different
            # physical page rectangle.
            source_ratio = image.width() / max(image.height(), 1)
            target_ratio = paper_rect.width() / max(paper_rect.height(), 1)
            if source_ratio > target_ratio:
                target_w = paper_rect.width()
                target_h = target_w / source_ratio
            else:
                target_h = paper_rect.height()
                target_w = target_h * source_ratio

            target = QRectF(
                paper_rect.x() + (paper_rect.width() - target_w) / 2,
                paper_rect.y() + (paper_rect.height() - target_h) / 2,
                target_w,
                target_h,
            )
            painter.drawImage(target, image)
    finally:
        if painter.isActive():
            painter.end()
        doc.close()
