from __future__ import annotations
import io
from dataclasses import dataclass
from pypdf import PdfReader, PdfWriter, Transformation
from pypdf.generic import RectangleObject
from .config import LayoutSettings

@dataclass(frozen=True)
class PageLayoutResult:
    scale: float
    x: float
    y: float
    source_width: float
    source_height: float
    target_width: float
    target_height: float
    overflow: bool

def calculate_page_layout(
    source_width: float,
    source_height: float,
    settings: LayoutSettings,
) -> PageLayoutResult:
    target_w, target_h = settings.paper_size_points()
    top, right, bottom, left = settings.margins_points()
    usable_w = target_w - left - right
    usable_h = target_h - top - bottom
    if usable_w <= 0 or usable_h <= 0:
        raise ValueError("Margins leave no printable area.")

    mode = settings.scale_mode
    if mode == "Fit printable area":
        scale = min(usable_w / source_width, usable_h / source_height)
    elif mode == "Fit width":
        scale = usable_w / source_width
    elif mode == "Actual size":
        scale = 1.0
    else:
        scale = settings.scale_percent / 100.0

    scaled_w = source_width * scale
    scaled_h = source_height * scale

    if settings.horizontal_alignment == "Left":
        x = left
    elif settings.horizontal_alignment == "Right":
        x = target_w - right - scaled_w
    else:
        x = left + (usable_w - scaled_w) / 2

    if settings.vertical_alignment == "Top":
        y = target_h - top - scaled_h
    elif settings.vertical_alignment == "Bottom":
        y = bottom
    else:
        y = bottom + (usable_h - scaled_h) / 2

    overflow = (
        scaled_w > usable_w + 0.01 or
        scaled_h > usable_h + 0.01 or
        x < left - 0.01 or y < bottom - 0.01 or
        x + scaled_w > target_w - right + 0.01 or
        y + scaled_h > target_h - top + 0.01
    )
    return PageLayoutResult(
        scale, x, y, source_width, source_height,
        target_w, target_h, overflow
    )

def compose_pdf(source_path: str, settings: LayoutSettings) -> bytes:
    reader = PdfReader(source_path, strict=False)
    if reader.is_encrypted:
        raise ValueError("This PDF is password-protected. Unlock it before processing.")

    writer = PdfWriter()
    for page_number, original in enumerate(reader.pages, start=1):
        page = original
        # pypdf normalizes /Rotate into the page content and dimensions.
        if int(page.get("/Rotate", 0)) % 360:
            page.transfer_rotation_to_content()

        source_w = float(page.mediabox.width)
        source_h = float(page.mediabox.height)
        layout = calculate_page_layout(source_w, source_h, settings)

        target = writer.add_blank_page(
            width=layout.target_width,
            height=layout.target_height,
        )
        target.merge_transformed_page(
            page,
            Transformation().scale(layout.scale).translate(
                tx=layout.x, ty=layout.y
            ),
            over=True,
            expand=False,
        )
        target.mediabox = RectangleObject(
            [0, 0, layout.target_width, layout.target_height]
        )

    output = io.BytesIO()
    writer.write(output)
    return output.getvalue()


def compose_page(source_path: str, settings: LayoutSettings, page_index: int) -> bytes:
    """Compose only one source page for fast interactive preview."""
    reader = PdfReader(source_path, strict=False)
    if reader.is_encrypted:
        raise ValueError("This PDF is password-protected. Unlock it before processing.")
    if page_index < 0 or page_index >= len(reader.pages):
        raise IndexError("Page number is outside the document.")

    page = reader.pages[page_index]
    if int(page.get("/Rotate", 0)) % 360:
        page.transfer_rotation_to_content()

    layout = calculate_page_layout(
        float(page.mediabox.width), float(page.mediabox.height), settings
    )
    writer = PdfWriter()
    target = writer.add_blank_page(
        width=layout.target_width, height=layout.target_height
    )
    target.merge_transformed_page(
        page,
        Transformation().scale(layout.scale).translate(tx=layout.x, ty=layout.y),
        over=True, expand=False,
    )
    target.mediabox = RectangleObject(
        [0, 0, layout.target_width, layout.target_height]
    )
    output = io.BytesIO()
    writer.write(output)
    return output.getvalue()
