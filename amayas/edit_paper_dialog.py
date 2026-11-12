"""Paper-level edit dialog. Changes apply to ALL versions of the paper,
not to a specific version's file or notes."""
from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QPlainTextEdit,
    QComboBox, QDialogButtonBox,
)


class EditPaperDialog(QDialog):
    def __init__(self, db, settings, paper, parent=None):
        super().__init__(parent)
        self.db = db
        self.settings = settings
        self.paper = paper
        self.changed = False
        title = (paper.get("title") or "Untitled")[:50]
        self.setWindowTitle(f"Edit paper - {title}")
        self.setModal(True)
        self._size_to_screen()
        self._build()

    def _size_to_screen(self):
        from PyQt6.QtWidgets import QApplication
        scr = QApplication.primaryScreen()
        if scr is None:
            self.resize(640, 660); return
        g = scr.availableGeometry()
        self.resize(min(640, g.width() - 60),
                    min(660, g.height() - 80))

    def _build(self):
        from PyQt6.QtWidgets import QFormLayout
        v = QVBoxLayout(self)
        v.setContentsMargins(20, 20, 20, 20); v.setSpacing(8)

        note = QLabel(
            "These fields apply to the paper itself, not to a single "
            "version. Editing here affects every version.")
        note.setObjectName("Muted"); note.setWordWrap(True)
        v.addWidget(note)

        form = QFormLayout(); form.setSpacing(6)

        self.title_edit = QLineEdit(self.paper.get("title", ""))
        form.addRow("Title", self.title_edit)

        authors = self.paper.get("authors") or self.settings.get(
            "default_author", "")
        self.authors_edit = QLineEdit(authors)
        form.addRow("Authors", self.authors_edit)

        self.venue_edit = QLineEdit(self.paper.get("venue_target", ""))
        form.addRow("Target venue", self.venue_edit)

        self.abstract_edit = QPlainTextEdit(self.paper.get("abstract", ""))
        self.abstract_edit.setFixedHeight(120)
        form.addRow("Abstract", self.abstract_edit)

        self.category_edit = QComboBox()
        self.category_edit.setEditable(True)
        cats = [""] + list(self.settings.categories())
        self.category_edit.addItems(cats)
        cur_cat = self.paper.get("category") or ""
        idx = self.category_edit.findText(cur_cat)
        if idx >= 0:
            self.category_edit.setCurrentIndex(idx)
        else:
            self.category_edit.setCurrentText(cur_cat)
        form.addRow("Category", self.category_edit)

        self.tags_edit = QLineEdit(self.paper.get("tags", ""))
        self.tags_edit.setPlaceholderText("comma, separated, tags")
        form.addRow("Tags", self.tags_edit)

        self.remarks_edit = QPlainTextEdit(self.paper.get("remarks", ""))
        self.remarks_edit.setFixedHeight(80)
        form.addRow("Remarks", self.remarks_edit)

        self.status_edit = QComboBox()
        self.status_edit.addItems(self.settings.statuses())
        cur_status = self.paper.get("status") or "in_work"
        if cur_status in self.settings.statuses():
            self.status_edit.setCurrentText(cur_status)
        form.addRow("Status", self.status_edit)

        v.addLayout(form)
        v.addStretch()

        bb = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Save
            | QDialogButtonBox.StandardButton.Cancel)
        bb.accepted.connect(self._save)
        bb.rejected.connect(self.reject)
        v.addWidget(bb)

    def _save(self):
        self.db.paper_update(
            self.paper["id"],
            title=self.title_edit.text().strip() or "Untitled",
            authors=self.authors_edit.text().strip(),
            venue_target=self.venue_edit.text().strip(),
            abstract=self.abstract_edit.toPlainText().strip(),
            category=self.category_edit.currentText().strip(),
            tags=self.tags_edit.text().strip(),
            remarks=self.remarks_edit.toPlainText().strip(),
            status=self.status_edit.currentText(),
        )
        self.db.event(self.paper["id"], None, "paper_edited",
                      "metadata updated")
        self.changed = True
        self.accept()
