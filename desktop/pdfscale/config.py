from dataclasses import dataclass
from typing import Literal

PaperName = Literal["A4", "A3", "Letter"]
Orientation = Literal["Portrait", "Landscape"]
ScaleMode = Literal["Manual", "Fit printable area", "Fit width", "Actual size"]
Alignment = Literal["Left", "Centre", "Right"]

PAPER_MM = {
    "A4": (210.0, 297.0),
    "A3": (297.0, 420.0),
    "Letter": (215.9, 279.4),
}

@dataclass(frozen=True)
class LayoutSettings:
    paper: str = "A4"
    orientation: str = "Portrait"
    scale_mode: str = "Fit printable area"
    scale_percent: float = 80.0
    margin_top_mm: float = 5.0
    margin_bottom_mm: float = 5.0
    margin_left_mm: float = 5.0
    margin_right_mm: float = 5.0
    horizontal_alignment: str = "Centre"
    vertical_alignment: str = "Top"

    def paper_size_points(self) -> tuple[float, float]:
        width_mm, height_mm = PAPER_MM[self.paper]
        if self.orientation == "Landscape":
            width_mm, height_mm = height_mm, width_mm
        return width_mm * 72 / 25.4, height_mm * 72 / 25.4

    def margins_points(self) -> tuple[float, float, float, float]:
        factor = 72 / 25.4
        return (
            self.margin_top_mm * factor,
            self.margin_right_mm * factor,
            self.margin_bottom_mm * factor,
            self.margin_left_mm * factor,
        )
