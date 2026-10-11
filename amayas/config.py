"""Paths, file-type tables, constants."""
import os
from pathlib import Path

HOME        = Path.home()
AMAYAS_DIR  = Path(os.environ.get("AMAYAS_HOME", HOME / "Papers"))
FILES_DIR   = AMAYAS_DIR / "files"
DB_PATH     = AMAYAS_DIR / "papers.db"
SETTINGS_PATH = AMAYAS_DIR / "settings.json"

for _d in (AMAYAS_DIR, FILES_DIR):
    _d.mkdir(parents=True, exist_ok=True)

# ---- what we accept
PDF_EXTS   = {".pdf"}
DOC_EXTS   = {".docx", ".doc", ".odt", ".rtf"}
SLIDE_EXTS = {".pptx", ".ppt", ".odp"}
SHEET_EXTS = {".xlsx", ".xls", ".ods"}
TEXT_EXTS  = {".txt", ".md", ".markdown", ".rst", ".tex", ".bib"}
IMAGE_EXTS = {".png", ".jpg", ".jpeg", ".webp", ".gif", ".bmp", ".svg"}
ALL_EXTS   = PDF_EXTS | DOC_EXTS | SLIDE_EXTS | SHEET_EXTS | TEXT_EXTS | IMAGE_EXTS

# ---- statuses for papers
STATUSES = [
    "idea",
    "drafting",
    "internal_review",
    "ready",
    "submitted",
    "in_review",
    "revision_requested",
    "resubmitted",
    "accepted",
    "camera_ready",
    "published",
    "rejected",
    "withdrawn",
    "abandoned",
]

# statuses that lock a version when set
LOCKING_STATUSES = {"ready", "submitted", "resubmitted", "accepted",
                    "camera_ready", "published"}

# statuses that mean "this went out the door"
SUBMITTED_STATUSES = {"submitted", "resubmitted"}

CARD_W, CARD_H, COVER_H = 240, 320, 130
