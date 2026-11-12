"""PaperCard, DropZone, FlowContainer."""
from pathlib import Path

from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QPixmap
from PyQt6.QtWidgets import (
    QFrame, QLabel, QVBoxLayout, QHBoxLayout, QPushButton, QWidget,
    QSizePolicy,
)

from .config import CARD_W, CARD_H, COVER_H


class FlowContainer(QWidget):
    def __init__(self, h=18, v=18, parent=None):
        super().__init__(parent)
        self._h, self._v = h, v
        self._items = []
        self.setSizePolicy(QSizePolicy.Policy.Preferred,
                           QSizePolicy.Policy.Fixed)
        self.setFixedHeight(0)

    def clear(self):
        for w in self._items:
            w.setParent(None); w.deleteLater()
        self._items = []; self.setFixedHeight(0)

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


class PaperCard(QFrame):
    open_file_requested = pyqtSignal(int)     # click card body
    details_requested = pyqtSignal(int)       # click "..."
    edit_requested = pyqtSignal(int)          # click "Edit"
    add_version_requested = pyqtSignal(int)   # click "+ Version"
    delete_requested = pyqtSignal(int)        # click "x"
    drop_files = pyqtSignal(int, list)        # drop on card

    def __init__(self, paper: dict, parent=None):
        super().__init__(parent)
        self.paper = paper
        self.setObjectName("PaperCard")
        self.setFixedSize(CARD_W, CARD_H)
        self.setAcceptDrops(True)
        self.setProperty("dragover", False)
        self.setToolTip("Click to open   -   buttons below for actions")
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
            img.setStyleSheet(
                "font-size:44px;font-weight:800;color:#b6bcc9;")
        cv.addWidget(img)
        v.addWidget(cover)

        # body
        body = QWidget(); bv = QVBoxLayout(body)
        bv.setContentsMargins(12, 10, 12, 12); bv.setSpacing(4)

        title = QLabel(self.paper.get("title") or "Untitled")
        title.setObjectName("CardTitle"); title.setWordWrap(True)
        title.setFixedHeight(36)
        bv.addWidget(title)

        authors = QLabel(self.paper.get("authors") or "-")
        authors.setObjectName("CardPath")
        bv.addWidget(authors)

        ver_info = QLabel(self._version_info())
        ver_info.setObjectName("CardVersion")
        bv.addWidget(ver_info)

        row = QHBoxLayout(); row.setSpacing(4)
        b = QPushButton("+ Version")
        b.setObjectName("CardBtn")
        b.setCursor(Qt.CursorShape.PointingHandCursor)
        b.setToolTip("Add a new version of this paper")
        b.clicked.connect(
            lambda: self.add_version_requested.emit(self.paper["id"]))
        row.addWidget(b, 1)

        b2 = QPushButton("Edit")
        b2.setObjectName("CardBtn")
        b2.setCursor(Qt.CursorShape.PointingHandCursor)
        b2.setToolTip("Edit metadata (all versions)")
        b2.clicked.connect(
            lambda: self.edit_requested.emit(self.paper["id"]))
        row.addWidget(b2, 1)

        b3 = QPushButton("...")
        b3.setObjectName("CardBtn")
        b3.setFixedWidth(32)
        b3.setCursor(Qt.CursorShape.PointingHandCursor)
        b3.setToolTip("Versions, timeline, submit")
        b3.clicked.connect(
            lambda: self.details_requested.emit(self.paper["id"]))
        row.addWidget(b3, 0)

        bv.addLayout(row)
        v.addWidget(body)

        # status pill (top-left overlay)
        s = self.paper.get("status") or "drafting"
        pill = QLabel(s.replace("_", " ").upper())
        pill.setObjectName(f"Status_{s}")
        pill.setParent(self)
        pill.move(8, 8)
        pill.adjustSize()
        pill.raise_()

        # delete button (top-right overlay)
        self.del_btn = QPushButton("x")
        self.del_btn.setObjectName("DeleteCard")
        self.del_btn.setFixedSize(24, 24)
        self.del_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.del_btn.setToolTip("Delete paper from the library")
        self.del_btn.setParent(self)
        self.del_btn.move(CARD_W - 32, 8)
        self.del_btn.clicked.connect(
            lambda: self.delete_requested.emit(self.paper["id"]))
        self.del_btn.raise_()

    def _version_info(self):
        cur = self.paper.get("_current_version")
        count = self.paper.get("_versions_count", 0)
        if not cur:
            return f"no file yet  ({count} versions)" if count else "no file yet"
        parts = [cur.get("label") or "v?"]
        if cur.get("_is_final"):
            parts.append("final")
        elif cur.get("_is_locked"):
            parts.append("locked")
        pages = cur.get("page_count") or 0
        if pages:
            parts.append(f"{pages}p")
        parts.append(f"{count} versions" if count != 1 else "1 version")
        return "  -  ".join(parts)

    def _cover_pixmap(self):
        from .vault import paper_folder
        try:
            folder = paper_folder(self.paper["id"], self.paper["title"])
        except Exception:
            return None
        cp = folder / "cover.png"
        if not cp.exists():
            # try to regenerate from the current PDF version
            try:
                cur = self.paper.get("_current_version") or {}
                fp = cur.get("file_path") or ""
                if fp.endswith(".pdf") and Path(fp).exists():
                    self._generate_cover_now(Path(fp), folder)
            except Exception:
                pass
        if not cp.exists():
            return None
        pix = QPixmap(str(cp))
        if pix.isNull():
            return None
        return pix.scaled(CARD_W, COVER_H,
                          Qt.AspectRatioMode.KeepAspectRatioByExpanding,
                          Qt.TransformationMode.SmoothTransformation)

    def _generate_cover_now(self, pdf_path, folder):
        try:
            try:
                import pymupdf as fitz
            except ImportError:
                import fitz
        except ImportError:
            return
        try:
            doc = fitz.open(str(pdf_path))
            page = doc.load_page(0)
            pix = page.get_pixmap(matrix=fitz.Matrix(1.4, 1.4))
            out = folder / "cover.png"
            pix.save(str(out))
            doc.close()
        except Exception:
            pass

    def mouseReleaseEvent(self, e):
        if e.button() == Qt.MouseButton.LeftButton:
            self.open_file_requested.emit(self.paper["id"])

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


class DropZone(QFrame):
    files_dropped = pyqtSignal(list)
    clicked = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("DropZone")
        self.setFixedHeight(70)
        self.setAcceptDrops(True)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setProperty("dragover", False)
        v = QVBoxLayout(self)
        v.setContentsMargins(20, 10, 20, 10)
        lbl = QLabel(
            "Drop a document here  -  or click to choose a file\n"
            "Drop onto a card to add a version")
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

    def mouseReleaseEvent(self, e):
        if e.button() == Qt.MouseButton.LeftButton:
            self.clicked.emit()
