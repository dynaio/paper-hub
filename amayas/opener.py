"""Dispatch a document to the right viewer based on its extension.

  PDF                          → built-in PDF viewer (QtPdf)
  .md .txt .tex .rst code      → configured text editor (subl default)
  .docx .pptx .odt .xlsx ...   → system default (xdg-open → OnlyOffice)
  .png .jpg ...                → system default
"""
import shutil
import subprocess
from pathlib import Path

from .config import PDF_EXTS, TEXT_EXTS


def _which(cmd):
    if not cmd:
        return None
    if "/" in cmd:
        return cmd if Path(cmd).exists() else None
    return shutil.which(cmd)


def find_text_editor(settings):
    """Return a usable text editor command, preferring the configured one."""
    preferred = settings.get("editor_text", "subl")
    if preferred:
        path = _which(preferred)
        if path:
            return path
    for cand in ("subl", "code", "codium", "cursor", "zed",
                 "gnome-text-editor", "gedit", "kate", "nano", "vim"):
        path = shutil.which(cand)
        if path:
            return path
    return None


def open_document(path, settings, parent=None):
    """Open `path` in the right app. Returns a status string or None."""
    path = Path(path)
    if not path.is_file():
        return None

    ext = path.suffix.lower()

    # PDF → built-in viewer
    if ext in PDF_EXTS:
        try:
            from .pdf_viewer import PdfViewerDialog
            dlg = PdfViewerDialog(path, parent)
            dlg.exec()
            return "pdf-viewer"
        except Exception:
            pass  # fall through to xdg-open

    # Text / markdown / code → configured editor
    if ext in TEXT_EXTS:
        editor = find_text_editor(settings)
        if editor:
            try:
                subprocess.Popen(
                    [editor, str(path)],
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL,
                    start_new_session=True)
                return f"editor:{Path(editor).name}"
            except OSError:
                pass

    # Everything else → system default (routes to OnlyOffice for docx,
    # to the image viewer for png, etc.)
    try:
        subprocess.Popen(
            ["xdg-open", str(path)],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            start_new_session=True)
        return "xdg-open"
    except OSError:
        return None
