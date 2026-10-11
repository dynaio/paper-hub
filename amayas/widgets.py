"""PaperCard, DropZone, FlowContainer."""
from pathlib import Path

from PyQt6.QtCore import Qt, pyqtSignal, QMimeData
from PyQt6.QtGui import QPixmap, QDrag
from PyQt6.QtWidgets import (
    QFrame, QLabel, QVBoxLayout, QHBoxLayout, QPushButton, QWidget,
    QSizePolicy,
)

from .config import CARD_W, CARD_H, COVER_H


# ------------------------------------------------------------ flow layout
class FlowContainer(QWidget):
    """Simple flow layout that grows in height inside a QVBoxLayout."""

    def __init__(self, h=18, v=18, parent=None):
        super().__init__(parent)
        self._h, self._v = h, v
        self._items = []
        self.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Fixed)
        self.setFixedHeight(0)

    def clear(self):
        for w in self._items:
            w.setParent(None); w.deleteLater()
        self._items = []
        self.setFixedHeight(0)

    def add(self, w):
        w.setParent(self); w.show()
        self._items.append(w); self._relayout()

    def resizeEvent(self, e):
        super().resizeEvent(e); self._relayout()

    def _relayout(self):
        width = self.width()
        if width <= 0:
            return
        x, y, row_h = 0, 0, 0
        for w in self._items:
            cw, ch = w.width(), w.height()
            if x + cw > width and x > 0:
                x = 0; y += row_h + self._v; row_h = 0
            w.move(x, y)
            x += cw + self._h
            row_h = max(row_h, ch)
        need = y + row_h
        if need != self.height():
            self.setFixedHeight(need)


# ------------------------------------------------------------ card
class PaperCard(QFrame):
    open_requested = pyqtSignal(int)
    drop_files = pyqtSignal(int, list)   # paper_id, list[Path]
    edit_requested = pyqtSignal(int)

    def __init__(self, paper: dict, parent=None):
        super().__init__(parent)
        self.paper = paper
        self.setObjectName("PaperCard")
        self.setFixedSize(CARD_W, CARD_H)
        self.setAcceptDrops(True)
        self.setProperty("dragover", False)
        self._build()

    def _build(self):
        v = QVBoxLayout(self)
        v.setContentsMargins(0, 0, 0, 0); v.setSpacing(0)

        # cover
        cover = QWidget(); cover.setObjectName("PaperCover")
        cover.setFixedHeight(COVER_H)
        cv = QVBoxLayout(cover); cv.setContentsMargins(0, 0, 0, 0)
        img = QLabel(); img.setAlignment(Qt.AlignmentFlag.AlignCenter)
        pix = self._cover_pixmap()
        if pix is not None:
            img.setPixmap(pix)
        else:
            img.setText((self.paper.get("title") or "?")[:2].upper())
            img.setStyleSheet("font-size:44px;font-weight:800;color:#b6bcc9;")
        cv.addWidget(img)
        v.addWidget(cover)

        # body
        body = QWidget(); bv = QVBoxLayout(body)
        bv.setContentsMargins(12, 10, 12, 12); bv.setSpacing(6)

        title = QLabel(self.paper.get("title") or "Untitled")
        title.setObjectName("CardTitle"); title.setWordWrap(True)
        title.setFixedHeight(38)
        bv.addWidget(title)

        authors = QLabel(self.paper.get("authors") or
                         self.paper.get("venue_target") or "—")
        authors.setObjectName("CardPath")
        bv.addWidget(authors)

        meta = QLabel(self._meta_line())
        meta.setObjectName("CardDesc")
        bv.addWidget(meta)

        v.addWidget(body)

        # status pill
        s = self.paper.get("status") or "drafting"
        pill = QLabel(s.replace("_", " ").upper())
        pill.setObjectName(f"Status_{s}")
        pill.setParent(self)
        pill.move(8, 8)
        pill.adjustSize()
        pill.raise_()

    def _meta_line(self):
        s = []
        if self.paper.get("year"):
            s.append(str(self.paper["year"]))
        if self.paper.get("venue_target"):
            s.append(self.paper["venue_target"])
        return " · ".join(s) or "—"

    def _cover_pixmap(self):
        cover = None
        # cover.png inside the paper folder
        from .vault import paper_folder
        try:
            folder = paper_folder(self.paper["id"], self.paper["title"])
        except Exception:
            return None
        cp = folder / "cover.png"
        if cp.exists():
            cover = cp
        if cover is None:
            return None
        pix = QPixmap(str(cover))
        if pix.isNull():
            return None
        return pix.scaled(CARD_W, COVER_H,
                          Qt.AspectRatioMode.KeepAspectRatioByExpanding,
                          Qt.TransformationMode.SmoothTransformation)

    # ---------- mouse
    def mouseReleaseEvent(self, e):
        if e.button() == Qt.MouseButton.LeftButton:
            self.open_requested.emit(self.paper["id"])

    # ---------- drag and drop
    def _set_dragover(self, on):
        self.setProperty("dragover", on)
        self.style().unpolish(self); self.style().polish(self)

    def dragEnterEvent(self, e):
        if e.mimeData().hasUrls():
            e.acceptProposedAction()
            self._set_dragover(True)

    def dragLeaveEvent(self, e):
        self._set_dragover(False)

    def dropEvent(self, e):
        self._set_dragover(False)
        paths = [Path(u.toLocalFile()) for u in e.mimeData().urls()
                 if u.isLocalFile()]
        if paths:
            self.drop_files.emit(self.paper["id"], paths)
            e.acceptProposedAction()


# ------------------------------------------------------------ drop zone
class DropZone(QFrame):
    """Full-width drop target at the top of the grid."""
    files_dropped = pyqtSignal(list)   # list[Path]

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("DropZone")
        self.setFixedHeight(70)
        self.setAcceptDrops(True)
        self.setProperty("dragover", False)
        v = QVBoxLayout(self)
        v.setContentsMargins(20, 10, 20, 10)
        lbl = QLabel("Drop a document here to add a paper  ·  "
                     "drop onto a card to add a version")
        lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        lbl.setObjectName("DropZoneLabel")
        v.addWidget(lbl)

    def _set_dragover(self, on):
        self.setProperty("dragover", on)
        self.style().unpolish(self); self.style().polish(self)

    def dragEnterEvent(self, e):
        if e.mimeData().hasUrls():
            e.acceptProposedAction()
            self._set_dragover(True)

    def dragLeaveEvent(self, e):
        self._set_dragover(False)

    def dropEvent(self, e):
        self._set_dragover(False)
        paths = [Path(u.toLocalFile()) for u in e.mimeData().urls()
                 if u.isLocalFile()]
        if paths:
            self.files_dropped.emit(paths)
            e.acceptProposedAction()
