"""Embedded PDF viewer using QtPdf (ships with PyQt6, no extra deps)."""
from pathlib import Path

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QSpinBox,
)

try:
    from PyQt6.QtPdf import QPdfDocument
    from PyQt6.QtPdfWidgets import QPdfView
    HAVE_QTPDF = True
except ImportError:
    HAVE_QTPDF = False


class PdfViewerDialog(QDialog):
    def __init__(self, path, parent=None):
        super().__init__(parent)
        self.path = Path(path)
        self.setWindowTitle(self.path.name)
        self.setModal(False)
        self._size_to_screen()
        if not HAVE_QTPDF:
            self._build_fallback()
            return
        self._build()

    def _size_to_screen(self):
        from PyQt6.QtWidgets import QApplication
        scr = QApplication.primaryScreen()
        if scr is None:
            self.resize(1000, 800); return
        g = scr.availableGeometry()
        self.resize(min(1100, g.width() - 60),
                    min(900, g.height() - 80))

    def _build(self):
        v = QVBoxLayout(self)
        v.setContentsMargins(0, 0, 0, 0); v.setSpacing(0)

        bar = QHBoxLayout()
        bar.setContentsMargins(10, 8, 10, 8); bar.setSpacing(6)

        bar.addWidget(QLabel("Page"))
        self.page_spin = QSpinBox()
        self.page_spin.setMinimum(1); self.page_spin.setMaximum(1)
        self.page_spin.valueChanged.connect(self._jump_to)
        bar.addWidget(self.page_spin)
        self.total_lbl = QLabel("/ ?")
        bar.addWidget(self.total_lbl)

        bar.addSpacing(10)

        prev_btn = QPushButton("◀")
        prev_btn.setFixedWidth(32)
        prev_btn.clicked.connect(self._prev)
        bar.addWidget(prev_btn)
        next_btn = QPushButton("▶")
        next_btn.setFixedWidth(32)
        next_btn.clicked.connect(self._next)
        bar.addWidget(next_btn)

        bar.addSpacing(10)

        zoom_out = QPushButton("−")
        zoom_out.setFixedWidth(32)
        zoom_out.clicked.connect(self._zoom_out)
        bar.addWidget(zoom_out)
        zoom_in = QPushButton("+")
        zoom_in.setFixedWidth(32)
        zoom_in.clicked.connect(self._zoom_in)
        bar.addWidget(zoom_in)
        fit_btn = QPushButton("Fit width")
        fit_btn.clicked.connect(self._fit_width)
        bar.addWidget(fit_btn)

        bar.addStretch()

        bar.addWidget(QLabel(self.path.name))

        bar.addSpacing(10)
        close_btn = QPushButton("Close")
        close_btn.clicked.connect(self.accept)
        bar.addWidget(close_btn)

        v.addLayout(bar)

        self.doc = QPdfDocument(self)
        self.doc.load(str(self.path))
        self.doc.statusChanged.connect(self._on_status)

        self.view = QPdfView(self)
        self.view.setDocument(self.doc)
        self.view.setPageMode(QPdfView.PageMode.MultiPage)
        self.view.setZoomMode(QPdfView.ZoomMode.FitToWidth)
        v.addWidget(self.view, 1)

        nav = self.view.pageNavigator()
        if nav is not None:
            nav.currentPageChanged.connect(self._on_page_changed)

        self._on_status(self.doc.status())

    def _on_status(self, status):
        try:
            if status == QPdfDocument.Status.Ready:
                total = self.doc.pageCount()
                self.page_spin.setMaximum(max(1, total))
                self.total_lbl.setText(f"/ {total}")
        except Exception:
            pass

    def _on_page_changed(self, page_index):
        self.page_spin.blockSignals(True)
        self.page_spin.setValue(page_index + 1)
        self.page_spin.blockSignals(False)

    def _jump_to(self, n):
        nav = self.view.pageNavigator()
        if nav is not None:
            nav.jump(n - 1, nav.currentLocation())

    def _prev(self):
        self.page_spin.setValue(max(1, self.page_spin.value() - 1))

    def _next(self):
        self.page_spin.setValue(self.page_spin.value() + 1)

    def _zoom_in(self):
        self.view.setZoomMode(QPdfView.ZoomMode.Custom)
        self.view.setZoomFactor(min(5.0, self.view.zoomFactor() * 1.2))

    def _zoom_out(self):
        self.view.setZoomMode(QPdfView.ZoomMode.Custom)
        self.view.setZoomFactor(max(0.2, self.view.zoomFactor() / 1.2))

    def _fit_width(self):
        self.view.setZoomMode(QPdfView.ZoomMode.FitToWidth)

    def _build_fallback(self):
        v = QVBoxLayout(self)
        v.setContentsMargins(20, 20, 20, 20)
        v.addWidget(QLabel(
            "QtPdf is not available in this PyQt6 build.\n"
            "File: " + str(self.path)))
        row = QHBoxLayout(); row.addStretch()
        b1 = QPushButton("Open in system viewer")
        b1.clicked.connect(self._open_system)
        row.addWidget(b1)
        b2 = QPushButton("Close"); b2.clicked.connect(self.accept)
        row.addWidget(b2)
        v.addLayout(row)

    def _open_system(self):
        import subprocess
        try:
            subprocess.Popen(["xdg-open", str(self.path)],
                             start_new_session=True)
        except OSError:
            pass
