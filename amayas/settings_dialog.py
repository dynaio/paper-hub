"""Settings dialog: Appearance, Statuses, Categories, Behavior."""
from pathlib import Path

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QTabWidget,
    QWidget, QListWidget, QListWidgetItem, QLineEdit, QCheckBox,
    QFileDialog, QMessageBox, QComboBox, QPlainTextEdit,
)

from . import logo as logo_mod


class SettingsDialog(QDialog):
    def __init__(self, db, settings, parent=None):
        super().__init__(parent)
        self.db = db
        self.settings = settings
        self.changed = False
        self.setWindowTitle("Amayas settings")
        self.setMinimumSize(420, 380)
        self.setModal(True)
        from PyQt6.QtWidgets import QApplication
        scr = QApplication.primaryScreen()
        if scr is not None:
            g = scr.availableGeometry()
            self.resize(min(720, g.width() - 60),
                        min(720, g.height() - 80))
        else:
            self.resize(720, 660)
        self._build()

    def _build(self):
        v = QVBoxLayout(self)
        v.setContentsMargins(20, 20, 20, 20); v.setSpacing(10)
        self.tabs = QTabWidget()
        self.tabs.addTab(self._tab_appearance(), "Appearance")
        self.tabs.addTab(self._tab_statuses(), "Statuses")
        self.tabs.addTab(self._tab_categories(), "Categories")
        self.tabs.addTab(self._tab_behavior(), "Behavior")
        v.addWidget(self.tabs, 1)
        row = QHBoxLayout(); row.addStretch()
        close = QPushButton("Close"); close.clicked.connect(self.accept)
        row.addWidget(close); v.addLayout(row)

    # ------------------------------------------------------- appearance
    def _tab_appearance(self):
        w = QWidget(); v = QVBoxLayout(w)
        v.setContentsMargins(10, 10, 10, 10); v.setSpacing(10)

        v.addWidget(QLabel("Application logo"))
        v.addWidget(QLabel(
            "Shown in the window title, the system tray, and the GNOME "
            "app list. PNG recommended."))

        row = QHBoxLayout()
        self.logo_preview = QLabel()
        self.logo_preview.setFixedSize(72, 72)
        self.logo_preview.setStyleSheet(
            "border:1px solid #e3e6ec;border-radius:8px;padding:4px;")
        self.logo_preview.setAlignment(Qt.AlignmentFlag.AlignCenter)
        row.addWidget(self.logo_preview)

        info_col = QVBoxLayout()
        self.logo_path_lbl = QLabel(""); self.logo_path_lbl.setObjectName("Muted")
        self.logo_path_lbl.setWordWrap(True)
        info_col.addWidget(self.logo_path_lbl); info_col.addStretch()
        row.addLayout(info_col, 1)
        v.addLayout(row)

        row2 = QHBoxLayout()
        choose = QPushButton("Choose image…")
        choose.setObjectName("Primary")
        choose.clicked.connect(self._choose_logo)
        row2.addWidget(choose)
        reset = QPushButton("Reset to default")
        reset.clicked.connect(self._reset_logo)
        row2.addWidget(reset)
        openf = QPushButton("Open current file")
        openf.clicked.connect(self._open_current_logo)
        row2.addWidget(openf)
        row2.addStretch()
        v.addLayout(row2)

        self.show_brand = QCheckBox("Show logo next to “amayas” in the toolbar")
        self.show_brand.setChecked(self.settings.show_brand_logo())
        self.show_brand.toggled.connect(
            lambda x: (self.settings.set("show_brand_logo", x),
                       setattr(self, "changed", True)))
        v.addWidget(self.show_brand)

        v.addSpacing(8)
        v.addWidget(QLabel("Theme"))
        row3 = QHBoxLayout()
        self.theme = QComboBox()
        self.theme.addItems(["light", "dark"])
        self.theme.setCurrentText(self.settings.get("theme", "light"))
        self.theme.currentTextChanged.connect(
            lambda t: (self.settings.set("theme", t),
                       setattr(self, "changed", True)))
        row3.addWidget(self.theme); row3.addStretch()
        v.addLayout(row3)

        v.addStretch()
        self._refresh_logo_preview()
        return w

    def _refresh_logo_preview(self):
        try:
            pix = logo_mod.get_pixmap(72)
            if not pix.isNull():
                self.logo_preview.setPixmap(pix)
            p = logo_mod.current_logo_path()
            self.logo_path_lbl.setText(
                f"Source: {p}" if p else "Using built-in fallback icon.")
        except Exception as e:
            self.logo_path_lbl.setText(f"(preview failed: {e})")

    def _choose_logo(self):
        f, _ = QFileDialog.getOpenFileName(
            self, "Choose logo image", str(Path.home()),
            "Images (*.png *.jpg *.jpeg *.webp *.bmp)")
        if not f:
            return
        if logo_mod.set_logo(Path(f)):
            self.changed = True
            self._refresh_logo_preview()
        else:
            QMessageBox.warning(self, "Failed",
                                "Could not load that image. Try PNG or JPG.")

    def _reset_logo(self):
        if QMessageBox.question(
                self, "Reset logo",
                "Restore the bundled default logo?"
                ) != QMessageBox.StandardButton.Yes:
            return
        logo_mod.clear_logo()
        self.changed = True
        self._refresh_logo_preview()

    def _open_current_logo(self):
        import subprocess
        p = logo_mod.current_logo_path()
        if p is None:
            QMessageBox.information(self, "No file", "No custom logo set.")
            return
        subprocess.Popen(["xdg-open", str(p)], start_new_session=True)

    # ------------------------------------------------------- statuses
    def _tab_statuses(self):
        w = QWidget(); v = QVBoxLayout(w)
        v.setContentsMargins(10, 10, 10, 10); v.setSpacing(8)

        v.addWidget(QLabel(
            "The statuses a paper can be in. Reorder with ↑ ↓, rename, "
            "or delete. Existing papers keep whatever status they had."))

        self.status_list = QListWidget()
        self.status_list.itemSelectionChanged.connect(
            lambda: self.status_input.setText(
                self._status_current() or ""))
        v.addWidget(self.status_list, 1)

        row = QHBoxLayout()
        self.status_input = QLineEdit()
        self.status_input.setPlaceholderText("Add a status (e.g. under_review)")
        self.status_input.returnPressed.connect(self._status_add)
        row.addWidget(self.status_input, 1)
        add = QPushButton("Add"); add.setObjectName("Primary")
        add.clicked.connect(self._status_add); row.addWidget(add)
        v.addLayout(row)

        row2 = QHBoxLayout()
        row2.addWidget(self._btn("Rename", self._status_rename))
        row2.addWidget(self._btn("Move up",   lambda: self._status_move(-1)))
        row2.addWidget(self._btn("Move down", lambda: self._status_move(1)))
        row2.addStretch()
        row2.addWidget(self._btn("Reset to defaults", self._status_reset))
        d = self._btn("Delete", self._status_delete); d.setObjectName("Danger")
        row2.addWidget(d)
        v.addLayout(row2)

        self._status_reload()
        return w

    def _status_current(self):
        it = self.status_list.currentItem()
        return it.text() if it else None

    def _status_reload(self):
        self.status_list.clear()
        for s in self.settings.statuses():
            self.status_list.addItem(QListWidgetItem(s))

    def _status_add(self):
        n = self.status_input.text().strip()
        if not n: return
        cur = self.settings.statuses()
        if n in cur: return
        cur.append(n); self.settings.set_statuses(cur)
        self.status_input.clear(); self._status_reload()
        self.changed = True

    def _status_rename(self):
        it = self.status_list.currentItem()
        if not it: return
        old = it.text(); new = self.status_input.text().strip()
        if not new or new == old: return
        cur = self.settings.statuses()
        if new in cur: return
        cur[cur.index(old)] = new
        self.settings.set_statuses(cur)
        # update papers
        with self.db.conn() as c:
            c.execute("UPDATE papers SET status=? WHERE status=?", (new, old))
        self._status_reload(); self.changed = True

    def _status_move(self, delta):
        it = self.status_list.currentItem()
        if not it: return
        name = it.text()
        cur = self.settings.statuses()
        if name not in cur: return
        i = cur.index(name); j = i + delta
        if j < 0 or j >= len(cur): return
        cur[i], cur[j] = cur[j], cur[i]
        self.settings.set_statuses(cur)
        self._status_reload(); self.changed = True

    def _status_delete(self):
        it = self.status_list.currentItem()
        if not it: return
        name = it.text()
        if QMessageBox.question(
                self, "Delete status",
                f'Delete "{name}"? Papers with this status will be set to '
                f'"drafting".'
                ) != QMessageBox.StandardButton.Yes:
            return
        cur = [s for s in self.settings.statuses() if s != name]
        self.settings.set_statuses(cur)
        with self.db.conn() as c:
            c.execute("UPDATE papers SET status='drafting' WHERE status=?",
                      (name,))
        self._status_reload(); self.changed = True

    def _status_reset(self):
        if QMessageBox.question(self, "Reset statuses",
                                "Reset statuses to the built-in list?"
                                ) != QMessageBox.StandardButton.Yes:
            return
        self.settings.reset_statuses()
        self._status_reload(); self.changed = True

    # ------------------------------------------------------- categories
    def _tab_categories(self):
        w = QWidget(); v = QVBoxLayout(w)
        v.setContentsMargins(10, 10, 10, 10); v.setSpacing(8)

        v.addWidget(QLabel(
            "Categories let you group papers (AI, CV, Fire, Calibration…). "
            "Also used for grouping in the grid view. Papers can have one "
            "category each."))

        self.cat_list = QListWidget()
        v.addWidget(self.cat_list, 1)

        row = QHBoxLayout()
        self.cat_input = QLineEdit()
        self.cat_input.setPlaceholderText("Add a category")
        self.cat_input.returnPressed.connect(self._cat_add)
        row.addWidget(self.cat_input, 1)
        add = QPushButton("Add"); add.setObjectName("Primary")
        add.clicked.connect(self._cat_add); row.addWidget(add)
        v.addLayout(row)

        row2 = QHBoxLayout()
        row2.addWidget(self._btn("Rename", self._cat_rename))
        row2.addStretch()
        d = self._btn("Delete", self._cat_delete); d.setObjectName("Danger")
        row2.addWidget(d)
        v.addLayout(row2)

        self._cat_reload()
        return w

    def _cat_reload(self):
        self.cat_list.clear()
        # union of settings + in-use categories on papers
        cats = set(self.settings.categories())
        for p in self.db.papers_list(status="all"):
            if p.get("category"):
                cats.add(p["category"])
        for c in sorted(cats, key=str.lower):
            self.cat_list.addItem(QListWidgetItem(c))

    def _cat_add(self):
        n = self.cat_input.text().strip()
        if not n: return
        self.settings.add_category(n)
        self.cat_input.clear()
        self._cat_reload(); self.changed = True

    def _cat_rename(self):
        it = self.cat_list.currentItem()
        if not it: return
        from PyQt6.QtWidgets import QInputDialog
        old = it.text()
        new, ok = QInputDialog.getText(self, "Rename category",
                                       "New name:", text=old)
        if not ok or not new.strip() or new == old: return
        new = new.strip()
        cur = self.settings.categories()
        cur = [new if c == old else c for c in cur]
        self.settings.set_categories(cur)
        with self.db.conn() as c:
            c.execute("UPDATE papers SET category=? WHERE category=?",
                      (new, old))
        self._cat_reload(); self.changed = True

    def _cat_delete(self):
        it = self.cat_list.currentItem()
        if not it: return
        name = it.text()
        if QMessageBox.question(self, "Delete category",
                                f'Remove "{name}"? Papers keep the tag as text.'
                                ) != QMessageBox.StandardButton.Yes:
            return
        cur = [c for c in self.settings.categories() if c != name]
        self.settings.set_categories(cur)
        self._cat_reload(); self.changed = True

    # ------------------------------------------------------- behavior
    def _tab_behavior(self):
        w = QWidget(); v = QVBoxLayout(w)
        v.setContentsMargins(10, 10, 10, 10); v.setSpacing(10)

        self.autolock = QCheckBox(
            "Lock new versions automatically (freeze hash)")
        self.autolock.setChecked(bool(self.settings.get("autolock_on_ready", True)))
        self.autolock.toggled.connect(
            lambda x: (self.settings.set("autolock_on_ready", x),
                       setattr(self, "changed", True)))
        v.addWidget(self.autolock)

        self.verify = QCheckBox(
            "Verify hash before submission (recommended)")
        self.verify.setChecked(bool(self.settings.get("verify_on_submit", True)))
        self.verify.toggled.connect(
            lambda x: (self.settings.set("verify_on_submit", x),
                       setattr(self, "changed", True)))
        v.addWidget(self.verify)

        note = QLabel(
            "The hash verification is the core safety mechanism of Amayas. "
            "Disabling it lets you submit a version whose file has changed "
            "since you locked it — which is exactly the mistake it exists "
            "to prevent.")
        note.setObjectName("Muted"); note.setWordWrap(True)
        v.addWidget(note)

        v.addStretch()
        return w

    # ------------------------------------------------------- helpers
    def _btn(self, text, slot):
        b = QPushButton(text); b.clicked.connect(slot); return b
