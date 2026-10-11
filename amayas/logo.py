"""Icon resolution and desktop cache handling.

  ~/.amayas/amayas-icon.png         canonical user icon
  ~/.amayas/icons/amayas-<hash>.png hashed copies for GNOME cache bypass
  <repo>/logo.png                   bundled fallback
"""
import hashlib
import subprocess
from pathlib import Path

from PyQt6.QtCore import Qt
from PyQt6.QtGui import QIcon, QPixmap, QPainter, QColor, QLinearGradient, QFont

from .config import AMAYAS_DIR

ICON_PATH     = AMAYAS_DIR / "amayas-icon.png"
ICON_DIR      = AMAYAS_DIR / "icons"
USER_SET_FLAG = AMAYAS_DIR / ".icon-user-set"
DESKTOP_FILE  = Path.home() / ".local/share/applications/amayas.desktop"

_REPO_ROOT   = Path(__file__).resolve().parent.parent
BUNDLED_LOGO = _REPO_ROOT / "logo.png"


def current_logo_path():
    if ICON_PATH.exists():
        return ICON_PATH
    if BUNDLED_LOGO.exists():
        return BUNDLED_LOGO
    return None


def _fallback_icon(size: int = 256) -> QIcon:
    pix = QPixmap(size, size)
    pix.fill(Qt.GlobalColor.transparent)
    p = QPainter(pix)
    p.setRenderHint(QPainter.RenderHint.Antialiasing)
    grad = QLinearGradient(0, 0, size, size)
    grad.setColorAt(0.0, QColor("#8b5cf6"))
    grad.setColorAt(1.0, QColor("#c4b5fd"))
    p.setBrush(grad)
    p.setPen(Qt.PenStyle.NoPen)
    r = size // 4
    p.drawRoundedRect(0, 0, size, size, r, r)
    p.setPen(QColor("#ffffff"))
    p.setFont(QFont("Ubuntu Sans", int(size * 0.34), QFont.Weight.Bold))
    p.drawText(pix.rect(), Qt.AlignmentFlag.AlignCenter, "a")
    p.end()
    return QIcon(pix)


def get_icon() -> QIcon:
    p = current_logo_path()
    if p is not None:
        pix = QPixmap(str(p))
        if not pix.isNull():
            return QIcon(pix.scaled(256, 256,
                                    Qt.AspectRatioMode.KeepAspectRatio,
                                    Qt.TransformationMode.SmoothTransformation))
    return _fallback_icon()


def get_pixmap(size: int = 64) -> QPixmap:
    p = current_logo_path()
    if p is not None:
        pix = QPixmap(str(p))
        if not pix.isNull():
            return pix.scaled(size, size,
                              Qt.AspectRatioMode.KeepAspectRatio,
                              Qt.TransformationMode.SmoothTransformation)
    return _fallback_icon(size).pixmap(size, size)


def set_logo(src) -> bool:
    src = Path(src)
    if not src.is_file():
        return False
    pix = QPixmap(str(src))
    if pix.isNull():
        return False
    try:
        ICON_PATH.parent.mkdir(parents=True, exist_ok=True)
        if pix.width() > 512 or pix.height() > 512:
            pix = pix.scaled(512, 512,
                             Qt.AspectRatioMode.KeepAspectRatio,
                             Qt.TransformationMode.SmoothTransformation)
        pix.save(str(ICON_PATH), "PNG")
        USER_SET_FLAG.write_text("1")
    except Exception:
        return False
    sync_desktop_icon()
    return True


def clear_logo():
    try:
        if ICON_PATH.exists():
            ICON_PATH.unlink()
        if USER_SET_FLAG.exists():
            USER_SET_FLAG.unlink()
    except OSError:
        pass
    sync_desktop_icon()


def install_bundled_logo(force: bool = False):
    if not BUNDLED_LOGO.exists():
        return False
    if USER_SET_FLAG.exists() and not force:
        return False
    if not force and ICON_PATH.exists():
        try:
            if ICON_PATH.stat().st_mtime >= BUNDLED_LOGO.stat().st_mtime:
                return False
        except OSError:
            pass
    try:
        ICON_PATH.parent.mkdir(parents=True, exist_ok=True)
        ICON_PATH.write_bytes(BUNDLED_LOGO.read_bytes())
    except OSError:
        return False
    sync_desktop_icon()
    return True


def sync_desktop_icon() -> bool:
    src = current_logo_path()
    if src is None:
        return False
    try:
        raw = src.read_bytes()
    except OSError:
        return False
    digest = hashlib.sha1(raw).hexdigest()[:10]
    ICON_DIR.mkdir(parents=True, exist_ok=True)
    hashed = ICON_DIR / f"amayas-{digest}.png"
    if not hashed.exists():
        try:
            hashed.write_bytes(raw)
        except OSError:
            return False
    for old in ICON_DIR.glob("amayas-*.png"):
        if old != hashed:
            try:
                old.unlink()
            except OSError:
                pass
    _write_desktop_entry(hashed)
    _nudge_gnome()
    return True


def _write_desktop_entry(icon_path: Path):
    launcher = Path.home() / ".amayas/amayas"
    entry = (
        "[Desktop Entry]\n"
        "Type=Application\n"
        "Version=1.0\n"
        "Name=Amayas\n"
        "GenericName=Paper Companion\n"
        "Comment=Research paper vault with hash-locked versions\n"
        f"Exec={launcher}\n"
        f"Icon={icon_path}\n"
        "Terminal=false\n"
        "Categories=Office;Education;Utility;\n"
        "StartupNotify=true\n"
        "StartupWMClass=amayas\n"
        "Keywords=papers;research;pdf;documents;vault;\n"
    )
    try:
        DESKTOP_FILE.parent.mkdir(parents=True, exist_ok=True)
        DESKTOP_FILE.write_text(entry)
    except OSError:
        pass


def _nudge_gnome():
    try:
        subprocess.run(
            ["update-desktop-database", str(DESKTOP_FILE.parent)],
            stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, timeout=10)
    except (FileNotFoundError, subprocess.TimeoutExpired, OSError):
        pass
    try:
        hicolor = Path.home() / ".local/share/icons/hicolor"
        if hicolor.is_dir():
            subprocess.run(["gtk-update-icon-cache", "-f", "-t", str(hicolor)],
                           stdout=subprocess.DEVNULL,
                           stderr=subprocess.DEVNULL, timeout=10)
    except (FileNotFoundError, subprocess.TimeoutExpired, OSError):
        pass
    try:
        DESKTOP_FILE.touch()
    except OSError:
        pass
