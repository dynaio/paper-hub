"""Main window. v0.1: drop files, see cards, lock versions, verify submit."""
from pathlib import Path

from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtGui import QShortcut, QKeySequence
from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QLineEdit, QScrollArea, QFrame, QApplication, QMessageBox, QStatusBar,
    QDialog, QPlainTextEdit, QComboBox, QFormLayout, QDialogButtonBox,
)

from .config import STATUSES as DEFAULT_STATUSES
from .db import Database
from .extract import extract, kind_of
from .hashing import file_hash, short
from .settings import Settings
from .styles import qss_for
from .vault import (paper_folder, copy_into_vault, freeze_version,
                    freeze_submitted, verify_against_lock,
                    next_version_label)
from .widgets import PaperCard, DropZone, FlowContainer
from .settings_dialog import SettingsDialog
from . import logo as logo_mod


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.db = Database()
        self.settings = Settings()
        self.setWindowTitle("Amayas")
        self.setMinimumSize(360, 260)
        self._fit_to_screen(1280, 860)
        try:
            logo_mod.install_bundled_logo()
            logo_mod.sync_desktop_icon()
            from PyQt6.QtWidgets import QApplication as _QApp
            _QApp.instance().setWindowIcon(logo_mod.get_icon())
            self.setWindowIcon(logo_mod.get_icon())
        except Exception:
            pass
        self._build()
        self._apply_theme(self.settings.get("theme", "light"))
        self.refresh()
        QTimer.singleShot(60, lambda: self._apply_overflow(self.width()))

    # ---------------------------------------------------------------- UI
    def _build(self):
        central = QWidget(); self.setCentralWidget(central)
        root = QVBoxLayout(central)
        root.setContentsMargins(0, 0, 0, 0); root.setSpacing(0)

        # toolbar
        bar = QWidget(); bar.setObjectName("Toolbar"); bar.setFixedHeight(60)
        h = QHBoxLayout(bar); h.setContentsMargins(20, 10, 20, 10); h.setSpacing(10)

        h.addWidget(self._brand_label())
        self.count_lbl = QLabel(""); self.count_lbl.setObjectName("Muted")
        h.addWidget(self.count_lbl); h.addSpacing(10)

        self.search = QLineEdit(); self.search.setObjectName("Search")
        self.search.setPlaceholderText("Search title, authors, abstract, tags…")
        self.search.textChanged.connect(self.refresh)
        h.addWidget(self.search, 1)

        self.theme_btn = QPushButton("Dark"); self.theme_btn.setFixedWidth(64)
        self.theme_btn.clicked.connect(self._toggle_theme)
        h.addWidget(self.theme_btn)

        self.settings_btn = QPushButton("Settings")
        self.settings_btn.clicked.connect(self._open_settings)
        h.addWidget(self.settings_btn)

        self.add_btn = QPushButton("+  Add paper")
        self.add_btn.setObjectName("Primary")
        self.add_btn.clicked.connect(self._pick_and_add)
        h.addWidget(self.add_btn)
        root.addWidget(bar)

        # filter bar
        self.filter_bar = QWidget(); self.filter_bar.setObjectName("FilterBar")
        self.filter_bar.setFixedHeight(44)
        fh = QHBoxLayout(self.filter_bar)
        fh.setContentsMargins(20, 6, 20, 6); fh.setSpacing(6)
        fh.addWidget(QLabel("Show:"))
        self._chips = {}
        self._rebuild_chips()
        fh.addStretch()
        root.addWidget(self.filter_bar)

        # drop zone
        self.drop_zone = DropZone()
        self.drop_zone.files_dropped.connect(self._add_files_as_new)
        root.addWidget(self.drop_zone)

        # grid
        self.scroll = QScrollArea(); self.scroll.setWidgetResizable(True)
        self.scroll.setFrameShape(QFrame.Shape.NoFrame)
        self.scroll.setHorizontalScrollBarPolicy(
            Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.panel = QWidget()
        self.panel_v = QVBoxLayout(self.panel)
        self.panel_v.setContentsMargins(20, 12, 20, 20)
        self.panel_v.setSpacing(8)
        self.panel_v.setAlignment(Qt.AlignmentFlag.AlignTop)
        self.scroll.setWidget(self.panel)
        root.addWidget(self.scroll, 1)

        self.setStatusBar(QStatusBar())
        QShortcut(QKeySequence("Ctrl+W"), self, activated=self.close)
        QShortcut(QKeySequence("Ctrl+Q"), self, activated=self.close)
        self.statusBar().showMessage("Ready.")

    def _rebuild_chips(self):

        """Recreate filter chips from settings.statuses()."""

        fh = self.filter_bar.layout()

        if fh is None:

            return

        # clear all chips (keep the leading label and trailing stretch)

        while fh.count() > 2:

            it = fh.takeAt(1)

            w = it.widget()

            if w:

                w.setParent(None); w.deleteLater()

        self._chips = {}

        entries = [("All", "all")] + [

            (s.replace("_", " ").title(), s)

            for s in self.settings.statuses()

        ]

        insert_at = 1

        for label, key in entries:

            c = QPushButton(label)

            c.setObjectName("Chip")

            c.setCheckable(True)

            c.setCursor(Qt.CursorShape.PointingHandCursor)

            c.toggled.connect(

                lambda checked, k=key: self._on_chip(k, checked))

            fh.insertWidget(insert_at, c)

            insert_at += 1

            self._chips[key] = c

        current = self.settings.get("filter_status", "all")

        for c in self._chips.values():

            c.blockSignals(True)

        if current in self._chips:

            self._chips[current].setChecked(True)

        else:

            self._chips["all"].setChecked(True)

            self.settings.set("filter_status", "all")

        for c in self._chips.values():

            c.blockSignals(False)

    def _fit_to_screen(self, max_w, max_h):
        """Fill the available screen without exceeding it."""
        from PyQt6.QtWidgets import QApplication
        scr = QApplication.primaryScreen()
        if scr is None:
            self.resize(max_w, max_h)
            return
        g = scr.availableGeometry()
        w = min(max_w, g.width() - 20)
        h = min(max_h, g.height() - 40)
        w = max(w, 360); h = max(h, 260)
        self.resize(w, h)
        self.move(g.x() + 10, g.y() + 20)

    def _brand_label(self):
        box = QWidget(); h = QHBoxLayout(box)
        h.setContentsMargins(0, 0, 0, 0); h.setSpacing(8)
        lbl = QLabel("amayas"); lbl.setObjectName("Brand")
        h.addWidget(lbl)
        return box

    # ---------------------------------------------------------------- theme
    def _apply_theme(self, theme):
        theme = "dark" if theme == "dark" else "light"
        app = QApplication.instance()
        if app is not None:
            app.setStyleSheet(qss_for(theme))
        self.theme_btn.setText("Light" if theme == "dark" else "Dark")

    def _toggle_theme(self):
        cur = self.settings.get("theme", "light")
        nxt = "dark" if cur == "light" else "light"
        self.settings.set("theme", nxt)
        self._apply_theme(nxt)

    # ---------------------------------------------------------------- filters
    def _on_chip(self, key, checked):
        if checked:
            for k, c in self._chips.items():
                if k != key:
                    c.blockSignals(True); c.setChecked(False)
                    c.blockSignals(False)
            self.settings.set("filter_status", key)
            self.refresh()

    # ---------------------------------------------------------------- render
    def refresh(self):
        while self.panel_v.count():
            it = self.panel_v.takeAt(0)
            w = it.widget()
            if w:
                w.setParent(None); w.deleteLater()

        status = self.settings.get("filter_status", "all")
        q = self.search.text().strip()
        papers = self.db.papers_list(status=status, query=q)

        stats = self.db.stats()
        self.count_lbl.setText(
            f"{stats['total']} papers  ·  {stats['ready']} ready  ·  "
            f"{stats['submitted']} submitted")

        if not papers:
            empty = QLabel("Nothing here yet.\n"
                           "Drop a PDF at the top, or click “+ Add paper”.")
            empty.setObjectName("Empty")
            empty.setAlignment(Qt.AlignmentFlag.AlignCenter)
            self.panel_v.addWidget(empty)
            return

        flow = FlowContainer()
        self.panel_v.addWidget(flow)
        for p in papers:
            card = PaperCard(p)
            card.open_requested.connect(self._open_paper)
            card.drop_files.connect(self._drop_on_paper)
            flow.add(card)
        self.panel.adjustSize()

    # ---------------------------------------------------------------- add
    def _pick_and_add(self):
        from PyQt6.QtWidgets import QFileDialog
        start = self.settings.get("last_dir") or str(Path.home())
        files, _ = QFileDialog.getOpenFileNames(
            self, "Choose document(s)", start, "Documents (*)")
        if not files:
            return
        self.settings.set("last_dir", str(Path(files[0]).parent))
        self._add_files_as_new([Path(f) for f in files])

    def _add_files_as_new(self, paths):
        added = 0
        for p in paths:
            try:
                self._add_one_new(Path(p))
                added += 1
            except Exception as e:
                QMessageBox.warning(self, "Add failed", f"{p}\n\n{e}")
        if added:
            self.statusBar().showMessage(f"Added {added} paper(s).", 4000)
            self.refresh()

    def _add_one_new(self, src: Path):
        if not src.is_file():
            return
        info = extract(src)
        title = info["title"] or src.stem

        pid = self.db.paper_create(
            title=title,
            authors=info["authors"],
            abstract=info["abstract"],
            status="drafting",
        )
        # copy file into vault
        label = "v1"
        dest = copy_into_vault(src, pid, title, label)
        h = file_hash(dest)
        kind = kind_of(dest)
        size = dest.stat().st_size if dest.exists() else 0
        vid = self.db.version_create(
            paper_id=pid, label=label, file_path=str(dest),
            hash=h, kind=kind, size_bytes=size,
            page_count=info["page_count"], is_canonical=1)
        self.db.version_set_canonical(pid, vid)

        # cover
        self._make_cover(dest, pid, title)

        # prompt for editing basics
        dlg = AddPaperDialog(self, title=title, authors=info["authors"],
                             abstract=info["abstract"], venue="",
                             status="drafting")
        if dlg.exec() == QDialog.DialogCode.Accepted:
            v = dlg.values()
            self.db.paper_update(pid, **v)

    def _drop_on_paper(self, pid, paths):
        paper = self.db.paper_get(pid)
        if not paper:
            return
        # every dropped file becomes either a version or an attachment
        existing = [v["label"] for v in self.db.versions_list(pid)]
        for path in paths:
            path = Path(path)
            if not path.is_file():
                continue
            k = kind_of(path)
            if k in ("pdf", "doc", "slides", "sheet", "text"):
                label = next_version_label(existing)
                self._add_version(pid, paper, path, label)
                existing.append(label)
            else:
                # attachment
                from .vault import attach_file
                dest = attach_file(path, pid, paper["title"])
                self.db.attachment_create(
                    paper_id=pid, version_id=None,
                    file_path=str(dest),
                    kind=("figure" if k == "image" else "other"),
                    caption="", size_bytes=dest.stat().st_size)
                self.db.event(pid, None, "attachment_added", dest.name)
        self.refresh()
        self.statusBar().showMessage("Drop handled.", 3000)

    def _add_version(self, pid, paper, src: Path, label: str):
        dest = copy_into_vault(src, pid, paper["title"], label)
        h = file_hash(dest)
        kind = kind_of(dest)
        size = dest.stat().st_size if dest.exists() else 0
        info = extract(dest)
        vid = self.db.version_create(
            paper_id=pid, label=label, file_path=str(dest),
            hash=h, kind=kind, size_bytes=size,
            page_count=info["page_count"], notes="", is_canonical=0)
        # ask: canonical? lock?
        dlg = VersionDialog(self, label=label,
                            autolock=self.settings.get("autolock_on_ready", True))
        if dlg.exec() == QDialog.DialogCode.Accepted:
            v = dlg.values()
            self.db.version_update(vid, notes=v["notes"])
            if v["canonical"]:
                self.db.version_set_canonical(pid, vid)
            if v["lock"]:
                frozen, fh = freeze_version(dest, label)
                self.db.version_update(vid, frozen_path=str(frozen),
                                       frozen_hash=fh)
                self.db.event(pid, vid, "version_locked",
                              f"{label} locked, hash {short(fh)}")
        # cover
        self._make_cover(dest, pid, paper["title"])

    # ---------------------------------------------------------------- cover
    def _make_cover(self, file_path: Path, pid: int, title: str):
        """Render page 1 of a PDF to cover.png. Silently skip otherwise."""
        try:
            import fitz
        except ImportError:
            return
        if file_path.suffix.lower() != ".pdf":
            return
        try:
            doc = fitz.open(str(file_path))
            page = doc.load_page(0)
            pix = page.get_pixmap(matrix=fitz.Matrix(1.4, 1.4))
            folder = paper_folder(pid, title)
            out = folder / "cover.png"
            pix.save(str(out))
            doc.close()
        except Exception:
            pass

    # ---------------------------------------------------------------- open
    def resizeEvent(self, e):
        super().resizeEvent(e)
        try:
            self._apply_overflow(e.size().width())
        except Exception:
            pass

    def _apply_overflow(self, width):
        """Hide less-critical toolbar buttons on narrow windows."""
        try:
            self.settings_btn.setVisible(width >= 900)
            self.theme_btn.setVisible(width >= 780)
            self.add_btn.setVisible(width >= 700)
        except AttributeError:
            pass

    def _open_settings(self):
        dlg = SettingsDialog(self.db, self.settings, self)
        dlg.exec()
        if dlg.changed:
            self._apply_theme(self.settings.get("theme", "light"))
            try: self._rebuild_chips()
            except Exception: pass
            try: self.setWindowIcon(logo_mod.get_icon())
            except Exception: pass
            self.refresh()

    def _open_paper(self, pid):
        dlg = PaperDetailDialog(self, pid)
        dlg.exec()
        self.refresh()




def _fit_dialog(dlg, max_w, max_h):
    """Size a dialog to fit within the available screen area."""
    from PyQt6.QtWidgets import QApplication
    scr = QApplication.primaryScreen()
    if scr is None:
        dlg.resize(max_w, max_h); return
    g = scr.availableGeometry()
    w = min(max_w, g.width() - 60)
    h = min(max_h, g.height() - 80)
    w = max(w, 500)
    h = max(h, 420)
    dlg.resize(w, h)


# =================================================================== dialogs
class AddPaperDialog(QDialog):
    def _statuses(self):
        # parent is MainWindow → use its settings
        try:
            return self.parent().settings.statuses()
        except Exception:
            from .config import STATUSES
            return list(STATUSES)


    def __init__(self, parent=None, title="", authors="", abstract="",
                 venue="", status="drafting"):
        super().__init__(parent)
        self.setWindowTitle("New paper")
        self.setModal(True); _fit_dialog(self, 560, 460)
        v = QVBoxLayout(self)
        form = QFormLayout()
        from PyQt6.QtWidgets import QLineEdit, QPlainTextEdit, QComboBox
        self.t = QLineEdit(title); form.addRow("Title", self.t)
        self.a = QLineEdit(authors); form.addRow("Authors", self.a)
        self.ab = QPlainTextEdit(abstract); self.ab.setFixedHeight(120)
        form.addRow("Abstract", self.ab)
        self.ve = QLineEdit(venue); form.addRow("Target venue", self.ve)
        self.st = QComboBox()
        self.st.addItems(self._statuses())
        self.st.setCurrentText(status); form.addRow("Status", self.st)
        v.addLayout(form)
        bb = QDialogButtonBox(QDialogButtonBox.StandardButton.Save
                              | QDialogButtonBox.StandardButton.Cancel)
        bb.accepted.connect(self.accept); bb.rejected.connect(self.reject)
        v.addWidget(bb)

    def values(self):
        return {"title": self.t.text().strip() or "Untitled",
                "authors": self.a.text().strip(),
                "abstract": self.ab.toPlainText().strip(),
                "venue_target": self.ve.text().strip(),
                "status": self.st.currentText()}


class VersionDialog(QDialog):
    def __init__(self, parent=None, label="v1", autolock=True):
        super().__init__(parent)
        self.setWindowTitle(f"New version {label}")
        self.setModal(True); _fit_dialog(self, 480, 320)
        v = QVBoxLayout(self)
        form = QFormLayout()
        from PyQt6.QtWidgets import QLineEdit, QPlainTextEdit, QCheckBox
        self.notes = QPlainTextEdit(); self.notes.setFixedHeight(100)
        form.addRow("Notes", self.notes)
        self.canon = QCheckBox("Make this the canonical (latest) version")
        self.canon.setChecked(True); form.addRow("", self.canon)
        self.lock = QCheckBox("Lock this version (freeze hash)")
        self.lock.setChecked(bool(autolock)); form.addRow("", self.lock)
        v.addLayout(form)
        bb = QDialogButtonBox(QDialogButtonBox.StandardButton.Save
                              | QDialogButtonBox.StandardButton.Cancel)
        bb.accepted.connect(self.accept); bb.rejected.connect(self.reject)
        v.addWidget(bb)

    def values(self):
        return {"notes": self.notes.toPlainText().strip(),
                "canonical": self.canon.isChecked(),
                "lock": self.lock.isChecked()}


class PaperDetailDialog(QDialog):
    def __init__(self, parent, pid):
        super().__init__(parent)
        self.parent_win = parent
        self.pid = pid
        self.setWindowTitle("Paper details")
        self.setModal(True); _fit_dialog(self, 760, 720)
        self._build()
        self._load()

    def _build(self):
        v = QVBoxLayout(self); v.setContentsMargins(20, 20, 20, 20)
        self.title_lbl = QLabel(); self.title_lbl.setObjectName("CardTitle")
        self.title_lbl.setWordWrap(True)
        v.addWidget(self.title_lbl)

        self.info_lbl = QLabel(); self.info_lbl.setObjectName("Muted")
        v.addWidget(self.info_lbl)

        v.addWidget(QLabel("Abstract"))
        self.abstract = QPlainTextEdit(); self.abstract.setReadOnly(True)
        self.abstract.setFixedHeight(120)
        v.addWidget(self.abstract)

        v.addWidget(QLabel("Remarks"))
        self.remarks = QPlainTextEdit(); self.remarks.setFixedHeight(80)
        v.addWidget(self.remarks)

        v.addWidget(QLabel("Versions"))
        self.versions_box = QVBoxLayout()
        v.addLayout(self.versions_box)

        v.addWidget(QLabel("Activity"))
        self.events = QPlainTextEdit(); self.events.setReadOnly(True)
        self.events.setFixedHeight(140)
        v.addWidget(self.events)

        from PyQt6.QtWidgets import QComboBox
        st_row = QHBoxLayout()
        st_row.addWidget(QLabel("Status"))
        self.status = QComboBox()
        self.status.addItems(self.parent_win.settings.statuses())
        self.status.currentTextChanged.connect(self._status_changed)
        st_row.addWidget(self.status); st_row.addStretch()

        submit_btn = QPushButton("Mark as submitted…")
        submit_btn.setObjectName("Primary")
        submit_btn.clicked.connect(self._mark_submitted)
        st_row.addWidget(submit_btn)

        save_btn = QPushButton("Save remarks")
        save_btn.clicked.connect(self._save_remarks)
        st_row.addWidget(save_btn)

        close_btn = QPushButton("Close"); close_btn.clicked.connect(self.accept)
        st_row.addWidget(close_btn)
        v.addLayout(st_row)

    def _load(self):
        p = self.parent_win.db.paper_get(self.pid)
        if not p:
            return
        self.title_lbl.setText(p["title"])
        bits = []
        if p.get("authors"):     bits.append(p["authors"])
        if p.get("year"):        bits.append(p["year"])
        if p.get("venue_target"):bits.append("target: " + p["venue_target"])
        self.info_lbl.setText("  ·  ".join(bits) or "—")
        self.abstract.setPlainText(p.get("abstract") or "")
        self.remarks.setPlainText(p.get("remarks") or "")
        self.status.blockSignals(True)
        self.status.setCurrentText(p.get("status") or "drafting")
        self.status.blockSignals(False)

        # versions
        while self.versions_box.count():
            it = self.versions_box.takeAt(0)
            w = it.widget()
            if w:
                w.setParent(None); w.deleteLater()
        for v in self.parent_win.db.versions_list(self.pid):
            frozen = bool(v.get("frozen_hash"))
            mark = "🔒" if frozen else "  "
            canon = " · canonical" if v.get("is_canonical") else ""
            hashes = ""
            if frozen:
                ok, cur, fh = verify_against_lock(v)
                hashes = f"  ·  hash {'✓' if ok else '✗ CHANGED'}"
            line = f"{mark} {v['label']}  ·  {v.get('kind','')}  ·  " \
                   f"{v.get('size_bytes',0)//1024} KB{canon}{hashes}"
            self.versions_box.addWidget(QLabel(line))

        # events
        evs = self.parent_win.db.events_list(self.pid, limit=80)
        lines = [f"{e['created_at']}  {e['kind']}  {e['detail']}" for e in evs]
        self.events.setPlainText("\n".join(lines))

    def _save_remarks(self):
        self.parent_win.db.paper_update(self.pid,
                                        remarks=self.remarks.toPlainText())
        self.parent_win.db.event(self.pid, None, "remark_edited", "")
        self.parent_win.refresh()

    def _status_changed(self, txt):
        p = self.parent_win.db.paper_get(self.pid)
        if not p or p.get("status") == txt:
            return
        self.parent_win.db.paper_update(self.pid, status=txt)
        self.parent_win.db.event(self.pid, None, "status_changed",
                                 f"{p.get('status')} → {txt}")
        self._load()
        self.parent_win.refresh()

    def _mark_submitted(self):
        p = self.parent_win.db.paper_get(self.pid)
        if not p:
            return
        versions = self.parent_win.db.versions_list(self.pid)
        if not versions:
            QMessageBox.warning(self, "No versions",
                                "This paper has no versions yet."); return
        canon = next((v for v in versions if v.get("is_canonical")), versions[-1])

        # submission dialog
        from PyQt6.QtWidgets import QLineEdit, QPlainTextEdit
        dlg = QDialog(self); dlg.setWindowTitle("Submit")
        dlg.resize(500, 320)
        dv = QVBoxLayout(dlg); f = QFormLayout()
        venue = QLineEdit(p.get("venue_target") or "")
        f.addRow("Venue", venue)
        notes = QPlainTextEdit(); notes.setFixedHeight(100)
        f.addRow("Notes", notes)
        dv.addLayout(f)
        bb = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok
                              | QDialogButtonBox.StandardButton.Cancel)
        bb.accepted.connect(dlg.accept); bb.rejected.connect(dlg.reject)
        dv.addWidget(bb)
        if dlg.exec() != QDialog.DialogCode.Accepted:
            return
        venue_txt = venue.text().strip() or "unknown"

        # ---- the safety check
        if self.parent_win.settings.get("verify_on_submit", True):
            ok, cur, frozen = verify_against_lock(canon)
            if frozen and not ok:
                ans = QMessageBox.critical(
                    self, "Version mismatch",
                    f"The file for {canon['label']} has changed since it was "
                    f"locked.\n\n"
                    f"Locked hash:  {short(frozen)}\n"
                    f"Current hash: {short(cur)}\n\n"
                    "Submitting a non-final version is exactly what this "
                    "check exists to prevent.\n\n"
                    "Options:\n"
                    "  • Cancel and fix the file (recommended)\n"
                    "  • Override and submit anyway",
                    QMessageBox.StandardButton.Cancel
                    | QMessageBox.StandardButton.Ignore)
                if ans != QMessageBox.StandardButton.Ignore:
                    return

        # freeze a SUBMITTED copy
        src_file = Path(canon["frozen_path"] or canon["file_path"])
        if not src_file.exists():
            QMessageBox.warning(self, "File missing", str(src_file)); return
        frozen_submit = freeze_submitted(src_file, canon["label"], venue_txt)
        self.parent_win.db.submission_create(
            paper_id=self.pid, version_id=canon["id"], venue=venue_txt,
            hash_at_submit=canon.get("frozen_hash") or canon.get("hash") or "",
            notes=notes.toPlainText())
        self.parent_win.db.paper_update(self.pid, status="submitted",
                                        venue_target=venue_txt)
        self.parent_win.db.event(self.pid, canon["id"], "submitted_copy",
                                 frozen_submit.name)
        QMessageBox.information(self, "Submitted",
                                f"Locked copy saved:\n  {frozen_submit.name}")
        self._load()
        self.parent_win.refresh()
