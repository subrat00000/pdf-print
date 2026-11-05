from pdfscale.config import LayoutSettings
from pdfscale.pdf_service import calculate_page_layout

def test_fit_printable_area_respects_margins():
    settings = LayoutSettings(
        paper="A4", orientation="Portrait",
        scale_mode="Fit printable area",
        margin_top_mm=10, margin_bottom_mm=10,
        margin_left_mm=10, margin_right_mm=10,
    )
    result = calculate_page_layout(612, 792, settings)
    assert result.scale > 0
    assert result.overflow is False
    assert result.x >= 10 * 72 / 25.4 - 0.01
    assert result.y >= 10 * 72 / 25.4 - 0.01

def test_manual_scale_detects_overflow():
    settings = LayoutSettings(
        scale_mode="Manual", scale_percent=200,
        margin_top_mm=5, margin_bottom_mm=5,
        margin_left_mm=5, margin_right_mm=5,
    )
    result = calculate_page_layout(612, 792, settings)
    assert result.overflow is True

def test_landscape_paper_dimensions():
    settings = LayoutSettings(paper="A4", orientation="Landscape")
    width, height = settings.paper_size_points()
    assert width > height
