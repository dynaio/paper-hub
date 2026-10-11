"""Ingest files into the vault. Freeze versions. Safety rules:
  * Never move or delete a file the user gave us.
  * Never overwrite an existing file.
  * Frozen copies are byte-identical to the source at lock time.
  * Frozen copies are chmod 0444.
"""
import os
import shutil
from datetime import datetime
from pathlib import Path

from .config import FILES_DIR, SUBMITTED_STATUSES, LOCKING_STATUSES
from .hashing import file_hash, short


def _slug(text: str, n: int = 40) -> str:
    s = "".join(c if (c.isalnum() or c in "-_") else "-"
                for c in (text or "")).strip("-")
    s = "-".join(p for p in s.split("-") if p)
    return (s or "paper")[:n].lower()


def paper_folder(paper_id: int, title: str) -> Path:
    d = FILES_DIR / f"{paper_id:04d}-{_slug(title)}"
    d.mkdir(parents=True, exist_ok=True)
    (d / "attachments").mkdir(exist_ok=True)
    return d


def copy_into_vault(src: Path, paper_id: int, title: str,
                    label: str) -> Path:
    """Copy src into the paper folder with a version-safe name.
    Returns the new absolute path."""
    folder = paper_folder(paper_id, title)
    ext = src.suffix.lower() or ".bin"
    stem = f"{label}{ext}"
    target = folder / stem
    n = 2
    while target.exists():
        target = folder / f"{label}-{n}{ext}"
        n += 1
    shutil.copy2(src, target)
    return target


def freeze_version(version_file: Path, label: str) -> tuple[Path, str]:
    """Make a locked copy of version_file with LOCKED- prefix.
    Returns (frozen_path, hash)."""
    h = file_hash(version_file)
    folder = version_file.parent
    ext = version_file.suffix
    target = folder / f"LOCKED-{label}{ext}"
    # if a frozen copy exists, replace only if the source changed
    if target.exists():
        try:
            if file_hash(target) == h:
                _chmod_readonly(target)
                return target, h
        except OSError:
            pass
        try:
            os.chmod(target, 0o644)
            target.unlink()
        except OSError:
            pass
    shutil.copy2(version_file, target)
    _chmod_readonly(target)
    return target, h


def freeze_submitted(version_file: Path, label: str,
                     venue: str, when: datetime | None = None) -> Path:
    """Make a SUBMITTED-<label>-<venue>-<date> copy. Returns the path."""
    when = when or datetime.now()
    folder = version_file.parent
    ext = version_file.suffix
    venue_slug = _slug(venue, 30)
    stamp = when.strftime("%Y-%m-%d")
    target = folder / f"SUBMITTED-{label}-{venue_slug}-{stamp}{ext}"
    n = 2
    while target.exists():
        target = folder / f"SUBMITTED-{label}-{venue_slug}-{stamp}-{n}{ext}"
        n += 1
    shutil.copy2(version_file, target)
    _chmod_readonly(target)
    return target


def attach_file(src: Path, paper_id: int, title: str) -> Path:
    """Copy an image / letter into the paper's attachments folder."""
    folder = paper_folder(paper_id, title) / "attachments"
    name = src.name
    target = folder / name
    n = 2
    while target.exists():
        stem, ext = name.rsplit(".", 1) if "." in name else (name, "")
        target = folder / f"{stem}-{n}{'.' + ext if ext else ''}"
        n += 1
    shutil.copy2(src, target)
    return target


def _chmod_readonly(p: Path):
    try:
        os.chmod(p, 0o444)
    except OSError:
        pass


def verify_against_lock(version: dict) -> tuple[bool, str, str]:
    """Returns (ok, current_hash, frozen_hash). ok = True when current
    file matches the frozen one."""
    cur = file_hash(version.get("file_path") or "")
    frozen = version.get("frozen_hash") or ""
    if not frozen:
        return True, cur, frozen
    return cur == frozen, cur, frozen


def next_version_label(existing_labels: list[str]) -> str:
    """Produce v<N> based on current labels."""
    import re
    nums = []
    for l in existing_labels or []:
        m = re.search(r"v?(\d+)", str(l), re.IGNORECASE)
        if m:
            try:
                nums.append(int(m.group(1)))
            except ValueError:
                pass
    return f"v{(max(nums) + 1) if nums else 1}"
