from __future__ import annotations
import logging
from pathlib import Path
from PySide6.QtCore import Qt, QSettings, QTimer
from PySide6.QtGui import QAction, QPixmap
from PySide6.QtWidgets import (
    QMainWindow, QWidget, QLabel, QPushButton, QFileDialog, QMessageBox,
    QVBoxLayout, QHBoxLayout, QFormLayout, QGroupBox, QComboBox,
    QDoubleSpinBox, QSpinBox, QScrollArea, QSplitter, QFrame, QInputDialog
)
from PySide6.QtPrintSupport import QPrinter, QPrintPreviewDialog
from .config import LayoutSettings
from .pdf_service import compose_pdf, compose_page
from .render_service import render_pdf_page
from .print_service import configure_printer, print_pdf_bytes

log = logging.getLogger(__name__)

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.source_path: str | None = None
        self.page_count = 0
        self.page_index = 0
        self.page_widgets: list[QLabel] = []
        self.rendered_pages: set[int] = set()
        self._building_pages = False
        self.setAcceptDrops(True)
        self.settings_store = QSettings("PDFScalePrint", "PDFScalePrint")
        self.preview_timer = QTimer(self)
        self.preview_timer.setSingleShot(True)
        self.preview_timer.setInterval(140)
        self.preview_timer.timeout.connect(self._render_preview_now)
        self.setWindowTitle("PDF Scale & Print")
        self.resize(1360, 900)
        self._build_ui()
        self._restore_settings()
        self._update_actions()

    def _build_ui(self):
        open_action = QAction("Open", self)
        open_action.setShortcut("Ctrl+O")
        open_action.triggered.connect(self.open_dialog)
        save_action = QAction("Save adjusted PDF", self)
        save_action.setShortcut("Ctrl+Shift+S")
        save_action.triggered.connect(self.save_adjusted)
        print_action = QAction("Print", self)
        print_action.setShortcut("Ctrl+P")
        print_action.triggered.connect(self.print_document)
        menu = self.menuBar().addMenu("File")
        menu.addAction(open_action)
        menu.addAction(save_action)
        menu.addSeparator()
        menu.addAction(print_action)

        root = QWidget()
        self.setCentralWidget(root)
        layout = QHBoxLayout(root)
        splitter = QSplitter(Qt.Orientation.Horizontal)
        layout.addWidget(splitter)

        panel = QWidget()
        panel_layout = QVBoxLayout(panel)

        open_btn = QPushButton("Open PDF")
        open_btn.clicked.connect(self.open_dialog)
        panel_layout.addWidget(open_btn)
        self.file_label = QLabel("No PDF opened")
        self.file_label.setWordWrap(True)
        panel_layout.addWidget(self.file_label)

        paper_box = QGroupBox("Page setup")
        form = QFormLayout(paper_box)
        self.paper = self._combo(["A4", "A3", "Letter"])
        self.orientation = self._combo(["Portrait", "Landscape"])
        form.addRow("Paper", self.paper)
        form.addRow("Orientation", self.orientation)
        panel_layout.addWidget(paper_box)

        scale_box = QGroupBox("Scaling")
        scale_form = QFormLayout(scale_box)
        self.scale_mode = self._combo([
            "Fit printable area", "Fit width", "Manual", "Actual size"
        ])
        self.scale_percent = QDoubleSpinBox()
        self.scale_percent.setRange(1, 400)
        self.scale_percent.setDecimals(1)
        self.scale_percent.setSuffix(" %")
        self.scale_percent.setValue(80)
        scale_form.addRow("Mode", self.scale_mode)
        scale_form.addRow("Manual scale", self.scale_percent)
        panel_layout.addWidget(scale_box)

        margin_box = QGroupBox("Margins (mm)")
        margin_form = QFormLayout(margin_box)
        self.margin_top = self._number()
        self.margin_bottom = self._number()
        self.margin_left = self._number()
        self.margin_right = self._number()
        margin_form.addRow("Top", self.margin_top)
        margin_form.addRow("Bottom", self.margin_bottom)
        margin_form.addRow("Left", self.margin_left)
        margin_form.addRow("Right", self.margin_right)
        panel_layout.addWidget(margin_box)

        position_box = QGroupBox("Position")
        position_form = QFormLayout(position_box)
        self.horizontal = self._combo(["Left", "Centre", "Right"])
        self.vertical = self._combo(["Top", "Centre", "Bottom"])
        position_form.addRow("Horizontal", self.horizontal)
        position_form.addRow("Vertical", self.vertical)
        panel_layout.addWidget(position_box)

        nav = QHBoxLayout()
        self.prev_btn = QPushButton("◀")
        self.next_btn = QPushButton("▶")
        self.page_spin = QSpinBox()
        self.page_spin.setMinimum(1)
        self.page_spin.setMaximum(1)
        self.page_info = QLabel("Page 0 / 0")
        self.prev_btn.clicked.connect(lambda: self._change_page(-1))
        self.next_btn.clicked.connect(lambda: self._change_page(1))
        self.page_spin.valueChanged.connect(self._page_selected)
        nav.addWidget(self.prev_btn)
        nav.addWidget(self.page_spin)
        nav.addWidget(self.next_btn)
        panel_layout.addLayout(nav)
        panel_layout.addWidget(self.page_info)

        self.status = QLabel("Open a PDF to begin.")
        self.status.setWordWrap(True)
        panel_layout.addWidget(self.status)

        preview_btn = QPushButton("Refresh preview")
        preview_btn.clicked.connect(self.refresh_preview)
        panel_layout.addWidget(preview_btn)
        save_btn = QPushButton("Save adjusted PDF")
        save_btn.clicked.connect(self.save_adjusted)
        panel_layout.addWidget(save_btn)
        print_btn = QPushButton("Print…")
        print_btn.setMinimumHeight(44)
        print_btn.clicked.connect(self.print_document)
        panel_layout.addWidget(print_btn)
        panel_layout.addStretch()

        preview_container = QWidget()
        preview_layout = QVBoxLayout(preview_container)
        self.scroll = QScrollArea()
        self.scroll.setWidgetResizable(True)
        self.scroll.setAlignment(Qt.AlignmentFlag.AlignHCenter)
        self.scroll.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        self.scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        self.pages_host = QWidget()
        self.pages_layout = QVBoxLayout(self.pages_host)
        self.pages_layout.setContentsMargins(18, 18, 18, 18)
        self.pages_layout.setSpacing(18)
        self.empty_preview = QLabel("Open a PDF or drag and drop a PDF here.")
        self.empty_preview.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.empty_preview.setMinimumSize(500, 600)
        self.empty_preview.setStyleSheet("background:#d9dde3; color:#333;")
        self.pages_layout.addWidget(self.empty_preview)
        self.scroll.setWidget(self.pages_host)
        preview_layout.addWidget(self.scroll)
        self.scroll.verticalScrollBar().valueChanged.connect(self._on_scroll)

        splitter.addWidget(panel)
        splitter.addWidget(preview_container)
        splitter.setSizes([340, 1000])

        for widget in (
            self.paper, self.orientation, self.scale_mode, self.scale_percent,
            self.margin_top, self.margin_bottom, self.margin_left,
            self.margin_right, self.horizontal, self.vertical
        ):
            if isinstance(widget, QComboBox):
                widget.currentTextChanged.connect(self.refresh_preview)
            else:
                widget.valueChanged.connect(self.refresh_preview)

    def _combo(self, values):
        combo = QComboBox()
        combo.addItems(values)
        return combo

    def _number(self):
        spin = QDoubleSpinBox()
        spin.setRange(0, 100)
        spin.setDecimals(1)
        spin.setSingleStep(1)
        spin.setSuffix(" mm")
        spin.setValue(5)
        return spin

    def _layout_settings(self) -> LayoutSettings:
        return LayoutSettings(
            paper=self.paper.currentText(),
            orientation=self.orientation.currentText(),
            scale_mode=self.scale_mode.currentText(),
            scale_percent=self.scale_percent.value(),
            margin_top_mm=self.margin_top.value(),
            margin_bottom_mm=self.margin_bottom.value(),
            margin_left_mm=self.margin_left.value(),
            margin_right_mm=self.margin_right.value(),
            horizontal_alignment=self.horizontal.currentText(),
            vertical_alignment=self.vertical.currentText(),
        )

    def open_dialog(self):
        path, _ = QFileDialog.getOpenFileName(
            self, "Open PDF", "", "PDF documents (*.pdf)"
        )
        if path:
            self.open_path(path)

    def open_path(self, path: str):
        try:
            candidate = Path(path)
            if candidate.suffix.lower() != ".pdf":
                raise ValueError("Only PDF files are supported.")
            if not candidate.is_file():
                raise FileNotFoundError(path)
            # Validate once and obtain the document page count.
            import pypdfium2 as pdfium
            doc = pdfium.PdfDocument(str(candidate))
            try:
                count = len(doc)
            finally:
                doc.close()
            if count < 1:
                raise ValueError("The PDF contains no pages.")
            self.preview_timer.stop()
            self.source_path = str(candidate)
            self.page_count = count
            self.page_index = 0
            self.rendered_pages.clear()
            self.file_label.setText(candidate.name)
            self.page_spin.blockSignals(True)
            self.page_spin.setRange(1, count)
            self.page_spin.setValue(1)
            self.page_spin.blockSignals(False)
            self._create_page_placeholders()
            self._update_page_indicator()
            self._update_actions()
            self._render_page(0)
            QTimer.singleShot(0, self._render_visible_pages)
            self.status.setText(f"Loaded {count} page(s). Scroll to view; active page follows the viewport.")
        except Exception as exc:
            log.exception("Could not open PDF: %s", path)
            QMessageBox.critical(self, "Open PDF failed", str(exc))

    def _clear_page_widgets(self):
        while self.pages_layout.count():
            item = self.pages_layout.takeAt(0)
            widget = item.widget()
            if widget is not None:
                widget.deleteLater()
        self.page_widgets.clear()
        self.rendered_pages.clear()

    def _create_page_placeholders(self):
        self._building_pages = True
        self._clear_page_widgets()
        # Output pages use the selected paper dimensions. Reserve a consistent
        # page-shaped area so the scrollbar and page tracking work before rendering.
        self.empty_preview.hide()
        for index in range(self.page_count):
            page_frame = QFrame()
            page_frame.setFrameShape(QFrame.Shape.NoFrame)
            page_frame.setStyleSheet("background:#d9dde3;")
            frame_layout = QVBoxLayout(page_frame)
            frame_layout.setContentsMargins(8, 8, 8, 8)
            page_label = QLabel(f"Page {index + 1} — loading preview…")
            page_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            page_label.setStyleSheet("background:white; color:#555; border:1px solid #aeb4bd;")
            page_label.setMinimumSize(420, 594)
            page_label.setMaximumWidth(900)
            page_label.setProperty("page_index", index)
            frame_layout.addWidget(page_label, alignment=Qt.AlignmentFlag.AlignHCenter)
            self.pages_layout.addWidget(page_frame, alignment=Qt.AlignmentFlag.AlignHCenter)
            self.page_widgets.append(page_label)
        self._building_pages = False
        self.pages_layout.addStretch(1)
        self.pages_layout.activate()
        self.scroll.verticalScrollBar().setValue(0)

    def _paper_aspect_ratio(self):
        paper = self.paper.currentText()
        if paper == "A3":
            width, height = 297, 420
        elif paper == "Letter":
            width, height = 215.9, 279.4
        else:
            width, height = 210, 297
        if self.orientation.currentText() == "Landscape":
            width, height = height, width
        return width / height

    def _on_scroll(self, *_):
        if not self.source_path or not self.page_widgets:
            return
        viewport = self.scroll.viewport().rect()
        center_y = viewport.center().y()
        best_index, best_distance = self.page_index, None
        for index, label in enumerate(self.page_widgets):
            center = label.mapTo(self.scroll.viewport(), label.rect().center())
            distance = abs(center.y() - center_y)
            if best_distance is None or distance < best_distance:
                best_index, best_distance = index, distance
        if best_index != self.page_index:
            self.page_index = best_index
            self.page_spin.blockSignals(True)
            self.page_spin.setValue(best_index + 1)
            self.page_spin.blockSignals(False)
            self._update_page_indicator()
            self._update_actions()
        self._render_visible_pages()

    def _update_page_indicator(self):
        self.page_info.setText(f"Page {self.page_index + 1} / {self.page_count}")

    def _render_visible_pages(self):
        if not self.source_path or not self.page_widgets:
            return
        viewport_rect = self.scroll.viewport().rect()
        visible = []
        for index, label in enumerate(self.page_widgets):
            top_left = label.mapTo(self.scroll.viewport(), label.rect().topLeft())
            rect = label.rect().translated(top_left)
            if rect.adjusted(0, -500, 0, 500).intersects(viewport_rect):
                visible.append(index)
        # Render only visible pages plus one page ahead/behind for smooth scrolling.
        targets = set()
        for index in visible:
            targets.update((index - 1, index, index + 1))
        for index in sorted(i for i in targets if 0 <= i < self.page_count):
            if index not in self.rendered_pages:
                self._render_page(index)

    def _render_page(self, index: int):
        try:
            page_pdf = compose_page(
                self.source_path, self._layout_settings(), index
            )
            image = render_pdf_page(page_pdf, 0, max_width=850)
            pixmap = QPixmap.fromImage(image)
            label = self.page_widgets[index]
            label.setPixmap(pixmap)
            label.setText("")
            label.setMinimumSize(pixmap.size())
            label.setMaximumWidth(max(420, pixmap.width() + 4))
            self.rendered_pages.add(index)
        except Exception as exc:
            log.exception("Preview failed for page %s", index + 1)
            self.page_widgets[index].setText(f"Page {index + 1}\nPreview error: {exc}")

    def _update_actions(self):
        enabled = bool(self.source_path)
        self.prev_btn.setEnabled(enabled and self.page_index > 0)
        self.next_btn.setEnabled(enabled and self.page_index < self.page_count - 1)

    def _change_page(self, delta: int):
        self.page_index = max(0, min(self.page_count - 1, self.page_index + delta))
        self.page_spin.blockSignals(True)
        self.page_spin.setValue(self.page_index + 1)
        self.page_spin.blockSignals(False)
        self._page_selected(self.page_index + 1)

    def _page_selected(self, value: int):
        self.page_index = value - 1
        self._update_page_indicator()
        if self.page_widgets:
            self.scroll.ensureWidgetVisible(self.page_widgets[self.page_index], 0, 20)
        self._update_actions()
        self._render_visible_pages()

    def _build_output(self) -> bytes:
        if not self.source_path:
            raise ValueError("Open a PDF first.")
        return compose_pdf(self.source_path, self._layout_settings())


    def refresh_preview(self, *_):
        """Debounce layout changes, then invalidate and refresh visible page previews."""
        if self.source_path:
            self.preview_timer.start()

    def _render_preview_now(self):
        if not self.source_path:
            return
        self.rendered_pages.clear()
        for label in self.page_widgets:
            label.clear()
            label.setText(f"Page {label.property('page_index') + 1} — preview pending")
            label.setMinimumSize(420, 594)
        self._render_visible_pages()
        self._update_page_indicator()
        self.status.setText("Continuous preview: scroll through pages; only nearby pages are rendered.")

    def resizeEvent(self, event):
        super().resizeEvent(event)
        if self.source_path:
            self.refresh_preview()

    def dragEnterEvent(self, event):
        if event.mimeData().hasUrls():
            urls = event.mimeData().urls()
            if urls and all(url.isLocalFile() and Path(url.toLocalFile()).suffix.lower() == ".pdf" for url in urls):
                event.acceptProposedAction()
                return
        event.ignore()

    def dropEvent(self, event):
        urls = event.mimeData().urls() if event.mimeData().hasUrls() else []
        pdf_paths = [
            url.toLocalFile() for url in urls
            if url.isLocalFile() and Path(url.toLocalFile()).suffix.lower() == ".pdf"
        ]
        if len(pdf_paths) == 1:
            self.open_path(pdf_paths[0])
            event.acceptProposedAction()
        else:
            event.ignore()

    def save_adjusted(self):
        if not self.source_path:
            QMessageBox.information(self, "Save", "Open a PDF first.")
            return
        path, _ = QFileDialog.getSaveFileName(
            self, "Save adjusted PDF", "adjusted.pdf", "PDF documents (*.pdf)"
        )
        if not path:
            return
        if not path.lower().endswith(".pdf"):
            path += ".pdf"
        try:
            data = self._build_output()
            Path(path).write_bytes(data)
            QMessageBox.information(self, "Saved", f"Saved PDF:\n{path}")
        except Exception as exc:
            log.exception("Save failed")
            QMessageBox.critical(self, "Save failed", str(exc))

    def print_document(self):
        if not self.source_path:
            QMessageBox.information(self, "Print", "Open a PDF first.")
            return

        # Ask for the print scope before opening the preview.
        choices = ["Current page", "All pages", "Page range"]
        choice, accepted = QInputDialog.getItem(
            self, "Print pages", "Choose which pages to print:",
            choices, 0, False
        )
        if not accepted:
            return

        if choice == "Current page":
            page_indices = [self.page_index]
        elif choice == "All pages":
            page_indices = list(range(self.page_count))
        else:
            text, accepted = QInputDialog.getText(
                self, "Print page range", "Enter pages (e.g. 1-3, 5, 8-10):"
            )
            if not accepted:
                return
            try:
                page_indices = self._parse_page_ranges(text, self.page_count)
            except ValueError as exc:
                QMessageBox.warning(self, "Invalid page range", str(exc))
                return

        try:
            # Compose only the pages requested. The preview and final print
            # therefore contain exactly the same page selection.
            output = compose_pdf(
                self.source_path, self._layout_settings(), page_indices
            )
            printer = QPrinter(QPrinter.PrinterMode.HighResolution)
            configure_printer(printer, self._layout_settings())
            if not printer.isValid():
                raise RuntimeError("No valid printer is available.")

            preview = QPrintPreviewDialog(printer, self)
            preview.setWindowTitle("Print Preview — PDF Scale & Print")

            def paint_preview(target_printer):
                # QPrintPreviewDialog asks us to paint the composed document.
                # It will refresh this view when page setup or printer options
                # change inside the preview window.
                print_pdf_bytes(output, target_printer)

            preview.paintRequested.connect(paint_preview)
            preview.exec()
        except Exception as exc:
            log.exception("Print/preview failed")
            QMessageBox.critical(self, "Print failed", str(exc))

    @staticmethod
    def _parse_page_ranges(value: str, page_count: int) -> list[int]:
        """Parse 1-based page expressions such as '1-3,5,8-10'."""
        value = value.strip()
        if not value:
            raise ValueError("Enter at least one page number or range.")
        selected = []
        try:
            for part in value.split(","):
                part = part.strip()
                if not part:
                    raise ValueError
                if "-" in part:
                    pieces = part.split("-")
                    if len(pieces) != 2:
                        raise ValueError
                    first, last = (int(piece.strip()) for piece in pieces)
                    if first > last:
                        raise ValueError
                    numbers = range(first, last + 1)
                else:
                    numbers = [int(part)]
                for number in numbers:
                    if number < 1 or number > page_count:
                        raise ValueError
                    if number - 1 not in selected:
                        selected.append(number - 1)
        except (TypeError, ValueError):
            raise ValueError(
                f"Invalid range. Use page numbers from 1 to {page_count}, "
                "for example: 1-3, 5, 8-10."
            )
        return selected

    def _restore_settings(self):
        defaults = {
            "paper": "A4", "orientation": "Portrait",
            "scale_mode": "Fit printable area", "horizontal": "Centre",
            "vertical": "Top",
        }
        combos = {
            "paper": self.paper, "orientation": self.orientation,
            "scale_mode": self.scale_mode, "horizontal": self.horizontal,
            "vertical": self.vertical,
        }
        for key, widget in combos.items():
            value = self.settings_store.value(key, defaults[key])
            index = widget.findText(str(value))
            if index >= 0:
                widget.setCurrentIndex(index)
        spins = {
            "scale_percent": self.scale_percent,
            "margin_top": self.margin_top, "margin_bottom": self.margin_bottom,
            "margin_left": self.margin_left, "margin_right": self.margin_right,
        }
        for key, widget in spins.items():
            value = self.settings_store.value(key, widget.value())
            try:
                widget.setValue(float(value))
            except (TypeError, ValueError):
                pass

    def closeEvent(self, event):
        for key, widget in {
            "paper": self.paper, "orientation": self.orientation,
            "scale_mode": self.scale_mode, "horizontal": self.horizontal,
            "vertical": self.vertical,
        }.items():
            self.settings_store.setValue(key, widget.currentText())
        for key, widget in {
            "scale_percent": self.scale_percent,
            "margin_top": self.margin_top, "margin_bottom": self.margin_bottom,
            "margin_left": self.margin_left, "margin_right": self.margin_right,
        }.items():
            self.settings_store.setValue(key, widget.value())
        self.settings_store.sync()
        event.accept()
