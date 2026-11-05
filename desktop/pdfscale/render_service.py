from __future__ import annotations
import pypdfium2 as pdfium
from PySide6.QtGui import QImage

def render_pdf_page(pdf_bytes: bytes, page_index: int, max_width: int = 1100) -> QImage:
    doc = pdfium.PdfDocument(pdf_bytes)
    try:
        if page_index < 0 or page_index >= len(doc):
            raise IndexError("Page number is outside the document.")
        page = doc[page_index]
        width_pt, height_pt = page.get_size()
        scale = min(max_width / max(width_pt, 1), 2.2)
        bitmap = page.render(scale=scale)
        pil_image = bitmap.to_pil().convert("RGBA")
        image = QImage(
            pil_image.tobytes(),
            pil_image.width,
            pil_image.height,
            pil_image.width * 4,
            QImage.Format.Format_RGBA8888,
        )
        return image.copy()
    finally:
        doc.close()
