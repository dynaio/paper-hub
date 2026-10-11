"""JSON-backed settings."""
import json
from pathlib import Path

from .config import SETTINGS_PATH


class Settings:
    DEFAULTS = {
        "theme": "light",
        "last_dir": "",
        "sort": "recent",
        "filter_status": "all",
        "show_cover": True,
        "autolock_on_ready": True,      # when marking ready, lock the file
        "verify_on_submit": True,       # check hash before submission
        "use_libreoffice": True,        # try to convert docx/pptx for covers
    }

    def __init__(self, path=SETTINGS_PATH):
        self.path = Path(path)
        self.data = dict(self.DEFAULTS)
        self._load()

    def _load(self):
        if self.path.exists():
            try:
                raw = json.loads(self.path.read_text())
                if isinstance(raw, dict):
                    for k, v in raw.items():
                        if k in self.DEFAULTS:
                            self.data[k] = v
            except (OSError, json.JSONDecodeError):
                pass

    def save(self):
        try:
            tmp = self.path.with_suffix(".tmp")
            tmp.write_text(json.dumps(self.data, indent=2))
            tmp.replace(self.path)
        except OSError:
            pass

    def get(self, k, default=None):
        return self.data.get(k, default)

    def set(self, k, v):
        self.data[k] = v
        self.save()


    # -------- statuses (user-editable, defaults to config.STATUSES)
    def statuses(self):
        from .config import STATUSES as DEFAULTS
        v = self.data.get("statuses")
        if not isinstance(v, list) or not v:
            return list(DEFAULTS)
        return [str(s).strip() for s in v if str(s).strip()]

    def set_statuses(self, lst):
        self.data["statuses"] = [str(s).strip() for s in (lst or [])
                                 if str(s).strip()]
        self.save()

    def reset_statuses(self):
        self.data.pop("statuses", None)
        self.save()

    # -------- categories (groups)
    def categories(self):
        v = self.data.get("categories")
        return list(v) if isinstance(v, list) else []

    def set_categories(self, lst):
        self.data["categories"] = sorted(set(
            str(c).strip() for c in (lst or []) if str(c).strip()))
        self.save()

    def add_category(self, name):
        name = (name or "").strip()
        if not name:
            return
        cur = self.categories()
        if name not in cur:
            cur.append(name)
            self.set_categories(cur)

    # -------- appearance
    def show_brand_logo(self):
        return bool(self.data.get("show_brand_logo", True))
