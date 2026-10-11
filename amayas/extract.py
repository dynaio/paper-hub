"""Extract metadata from a document. Never raises — returns what it can."""
from pathlib import Path

from .config import (PDF_EXTS, DOC_EXTS, SLIDE_EXTS, SHEET_EXTS,
                     TEXT_EXTS, IMAGE_EXTS)


def kind_of(path) -> str:
    ext = Path(path).suffix.lower()
    if ext in PDF_EXTS:   return "pdf"
    if ext in DOC_EXTS:   return "doc"
    if ext in SLIDE_EXTS: return "slides"
    if ext in SHEET_EXTS: return "sheet"
    if ext in TEXT_EXTS:  return "text"
    if ext in IMAGE_EXTS: return "image"
    return "other"


def extract(path) -> dict:
    """Returns:
        title        : str, best guess
        authors      : str
        abstract     : str
        page_count   : int (0 if unknown)
        text_excerpt : str, first ~2000 chars of body text
        kind         : 'pdf'|'doc'|...|'other'
        errors       : list of strings
    """
    p = Path(path)
    out = {
        "title": p.stem.replace("_", " ").replace("-", " "),
        "authors": "",
        "abstract": "",
        "page_count": 0,
        "text_excerpt": "",
        "kind": kind_of(p),
        "errors": [],
    }
    if not p.is_file():
        out["errors"].append("file not found")
        return out

    k = out["kind"]
    try:
        if k == "pdf":     _pdf(p, out)
        elif k == "text":  _text(p, out)
        elif k == "image": pass
        # doc/slides/sheet: extraction comes in v0.1.5 (python-docx,
        # python-pptx, odfpy). For now we only take the filename.
    except Exception as e:
        out["errors"].append(f"{k}: {e}")
    return out


# ---------------------------------------------------------------- formats
def _pdf(p: Path, out: dict):
    try:
        import fitz  # PyMuPDF
    except ImportError:
        out["errors"].append("PyMuPDF not installed")
        return
    doc = fitz.open(str(p))
    try:
        out["page_count"] = doc.page_count
        # title from PDF metadata if present
        meta = doc.metadata or {}
        if meta.get("title", "").strip():
            out["title"] = meta["title"].strip()
        if meta.get("author", "").strip():
            out["authors"] = meta["author"].strip()

        # first 3 pages of text
        chunks = []
        for i in range(min(3, doc.page_count)):
            try:
                chunks.append(doc.load_page(i).get_text("text") or "")
            except Exception:
                pass
        text = "\n".join(chunks)
        out["text_excerpt"] = text[:2000]
        out["abstract"] = _guess_abstract(text)
        if not out["title"] or out["title"].lower() == p.stem.lower():
            # try first non-empty line as title
            lines = [l.strip() for l in text.splitlines() if l.strip()]
            if lines:
                out["title"] = lines[0][:200]
    finally:
        doc.close()


def _text(p: Path, out: dict):
    try:
        text = p.read_text(errors="replace")
    except OSError as e:
        out["errors"].append(str(e)); return
    out["text_excerpt"] = text[:2000]
    lines = [l.strip() for l in text.splitlines() if l.strip()]
    if lines:
        # use first markdown H1 or first line
        h1 = next((l for l in lines if l.startswith("# ")), None)
        out["title"] = (h1[2:] if h1 else lines[0])[:200]


def _guess_abstract(text: str) -> str:
    """Heuristic: text between 'Abstract' and 'Introduction' / 'Keywords'."""
    import re
    if not text:
        return ""
    m = re.search(
        r"\babstract\b[\s:.\-–—]*\n?(.{50,3000}?)(?=\n\s*(?:1[\.\s]|introduction|keywords|index terms|i[\.\s]+introduction)\b)",
        text, re.IGNORECASE | re.DOTALL)
    if m:
        return " ".join(m.group(1).split())[:1500]
    return ""
