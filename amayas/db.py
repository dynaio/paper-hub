"""SQLite layer. Append-only history, mutable current state."""
import json
import sqlite3
from contextlib import contextmanager
from datetime import datetime
from pathlib import Path

from .config import DB_PATH, FILES_DIR

SCHEMA = """
CREATE TABLE IF NOT EXISTS papers (
    id             INTEGER PRIMARY KEY AUTOINCREMENT,
    title          TEXT NOT NULL,
    authors        TEXT DEFAULT '',
    abstract       TEXT DEFAULT '',
    year           TEXT DEFAULT '',
    venue_target   TEXT DEFAULT '',
    status         TEXT DEFAULT 'drafting',
    tags           TEXT DEFAULT '',
    category       TEXT DEFAULT '',
    remarks        TEXT DEFAULT '',
    canonical_id   INTEGER,
    added_at       TEXT DEFAULT CURRENT_TIMESTAMP,
    updated_at     TEXT DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS versions (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    paper_id    INTEGER NOT NULL,
    label       TEXT NOT NULL,
    file_path   TEXT NOT NULL,
    hash        TEXT DEFAULT '',
    frozen_path TEXT DEFAULT '',
    frozen_hash TEXT DEFAULT '',
    locked_at   TEXT,
    page_count  INTEGER DEFAULT 0,
    kind        TEXT DEFAULT 'pdf',
    size_bytes  INTEGER DEFAULT 0,
    notes       TEXT DEFAULT '',
    is_canonical INTEGER DEFAULT 0,
    created_at  TEXT DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY(paper_id) REFERENCES papers(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS attachments (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    paper_id    INTEGER NOT NULL,
    version_id  INTEGER,
    file_path   TEXT NOT NULL,
    kind        TEXT DEFAULT 'other',
    caption     TEXT DEFAULT '',
    size_bytes  INTEGER DEFAULT 0,
    created_at  TEXT DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY(paper_id) REFERENCES papers(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS submissions (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    paper_id    INTEGER NOT NULL,
    version_id  INTEGER NOT NULL,
    venue       TEXT NOT NULL,
    submitted_at TEXT DEFAULT CURRENT_TIMESTAMP,
    hash_at_submit TEXT DEFAULT '',
    notes       TEXT DEFAULT '',
    response    TEXT DEFAULT '',
    response_at TEXT,
    FOREIGN KEY(paper_id) REFERENCES papers(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS events (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    paper_id    INTEGER,
    version_id  INTEGER,
    kind        TEXT NOT NULL,
    detail      TEXT DEFAULT '',
    created_at  TEXT DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_versions_paper ON versions(paper_id);
CREATE INDEX IF NOT EXISTS idx_events_paper ON events(paper_id);
CREATE INDEX IF NOT EXISTS idx_events_when  ON events(created_at DESC);
"""


class Database:
    def __init__(self, path=DB_PATH):
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with self.conn() as c:
            c.executescript(SCHEMA)

    @contextmanager
    def conn(self):
        c = sqlite3.connect(self.path)
        c.row_factory = sqlite3.Row
        c.execute("PRAGMA foreign_keys = ON")
        try:
            yield c
            c.commit()
        finally:
            c.close()

    # ------------------------------------------------ papers
    def papers_list(self, status=None, query="", order="recent"):
        q = "SELECT * FROM papers"
        args = []
        if status and status != "all":
            if status == "active":
                q += " WHERE status NOT IN ('published','abandoned','rejected','withdrawn')"
            else:
                q += " WHERE status = ?"
                args.append(status)
        q += " ORDER BY updated_at DESC"
        with self.conn() as c:
            rows = [dict(r) for r in c.execute(q, args).fetchall()]
        if query:
            ql = query.lower()
            rows = [r for r in rows if ql in " ".join(
                str(r.get(k) or "") for k in
                ("title","authors","abstract","tags","venue_target","remarks")
            ).lower()]
        return rows

    def paper_get(self, pid):
        with self.conn() as c:
            r = c.execute("SELECT * FROM papers WHERE id=?", (pid,)).fetchone()
        return dict(r) if r else None

    def paper_create(self, **kw):
        with self.conn() as c:
            cur = c.execute(
                """INSERT INTO papers
                   (title, authors, abstract, year, venue_target,
                    status, tags, category, remarks)
                   VALUES (?,?,?,?,?,?,?,?,?)""",
                (kw.get("title",""), kw.get("authors",""),
                 kw.get("abstract",""), kw.get("year",""),
                 kw.get("venue_target",""), kw.get("status","drafting"),
                 kw.get("tags",""), kw.get("category",""),
                 kw.get("remarks","")))
            pid = cur.lastrowid
        self.event(pid, None, "created",
                   f"Paper created: {kw.get('title','')}")
        return pid

    def paper_update(self, pid, **kw):
        allowed = {"title","authors","abstract","year","venue_target",
                   "status","tags","category","remarks","canonical_id"}
        sets, vals = [], []
        for k, v in kw.items():
            if k in allowed:
                sets.append(f"{k}=?")
                vals.append(v)
        if not sets:
            return
        sets.append("updated_at=CURRENT_TIMESTAMP")
        vals.append(pid)
        with self.conn() as c:
            c.execute(f"UPDATE papers SET {', '.join(sets)} WHERE id=?", vals)

    def paper_delete(self, pid):
        with self.conn() as c:
            c.execute("DELETE FROM versions WHERE paper_id=?", (pid,))
            c.execute("DELETE FROM attachments WHERE paper_id=?", (pid,))
            c.execute("DELETE FROM submissions WHERE paper_id=?", (pid,))
            c.execute("DELETE FROM events WHERE paper_id=?", (pid,))
            c.execute("DELETE FROM papers WHERE id=?", (pid,))
        # NOTE: files on disk are kept.

    # ------------------------------------------------ versions
    def versions_list(self, paper_id):
        with self.conn() as c:
            rows = c.execute(
                "SELECT * FROM versions WHERE paper_id=? ORDER BY id ASC",
                (paper_id,)).fetchall()
        return [dict(r) for r in rows]

    def version_get(self, vid):
        with self.conn() as c:
            r = c.execute("SELECT * FROM versions WHERE id=?", (vid,)).fetchone()
        return dict(r) if r else None

    def version_create(self, **kw):
        with self.conn() as c:
            cur = c.execute(
                """INSERT INTO versions
                   (paper_id, label, file_path, hash, kind, size_bytes,
                    page_count, notes, is_canonical)
                   VALUES (?,?,?,?,?,?,?,?,?)""",
                (kw.get("paper_id"), kw.get("label",""),
                 kw.get("file_path",""), kw.get("hash",""),
                 kw.get("kind","pdf"), kw.get("size_bytes",0),
                 kw.get("page_count",0), kw.get("notes",""),
                 int(bool(kw.get("is_canonical", 0)))))
            vid = cur.lastrowid
        self.event(kw.get("paper_id"), vid, "version_added",
                   f"{kw.get('label','')} added ({kw.get('kind','')})")
        return vid

    def version_update(self, vid, **kw):
        allowed = {"label","file_path","hash","frozen_path","frozen_hash",
                   "locked_at","page_count","kind","size_bytes","notes",
                   "is_canonical"}
        sets, vals = [], []
        for k, v in kw.items():
            if k in allowed:
                sets.append(f"{k}=?")
                vals.append(int(bool(v)) if k == "is_canonical" else v)
        if not sets:
            return
        vals.append(vid)
        with self.conn() as c:
            c.execute(f"UPDATE versions SET {', '.join(sets)} WHERE id=?", vals)

    def version_set_canonical(self, paper_id, version_id):
        with self.conn() as c:
            c.execute("UPDATE versions SET is_canonical=0 WHERE paper_id=?",
                      (paper_id,))
            c.execute("UPDATE versions SET is_canonical=1 WHERE id=?",
                      (version_id,))
            c.execute("UPDATE papers SET canonical_id=?, "
                      "updated_at=CURRENT_TIMESTAMP WHERE id=?",
                      (version_id, paper_id))

    # ------------------------------------------------ attachments
    def attachments_list(self, paper_id, version_id=None):
        q = "SELECT * FROM attachments WHERE paper_id=?"
        args = [paper_id]
        if version_id is not None:
            q += " AND version_id=?"
            args.append(version_id)
        q += " ORDER BY id ASC"
        with self.conn() as c:
            return [dict(r) for r in c.execute(q, args).fetchall()]

    def attachment_create(self, **kw):
        with self.conn() as c:
            cur = c.execute(
                """INSERT INTO attachments
                   (paper_id, version_id, file_path, kind, caption, size_bytes)
                   VALUES (?,?,?,?,?,?)""",
                (kw.get("paper_id"), kw.get("version_id"),
                 kw.get("file_path",""), kw.get("kind","other"),
                 kw.get("caption",""), kw.get("size_bytes",0)))
            return cur.lastrowid

    # ------------------------------------------------ submissions
    def submissions_list(self, paper_id=None):
        if paper_id is not None:
            with self.conn() as c:
                return [dict(r) for r in c.execute(
                    "SELECT * FROM submissions WHERE paper_id=? "
                    "ORDER BY id DESC", (paper_id,)).fetchall()]
        with self.conn() as c:
            return [dict(r) for r in c.execute(
                "SELECT s.*, p.title AS paper_title FROM submissions s "
                "LEFT JOIN papers p ON p.id=s.paper_id "
                "ORDER BY s.id DESC").fetchall()]

    def submission_create(self, **kw):
        with self.conn() as c:
            cur = c.execute(
                """INSERT INTO submissions
                   (paper_id, version_id, venue, hash_at_submit, notes)
                   VALUES (?,?,?,?,?)""",
                (kw.get("paper_id"), kw.get("version_id"),
                 kw.get("venue",""), kw.get("hash_at_submit",""),
                 kw.get("notes","")))
            sid = cur.lastrowid
        self.event(kw.get("paper_id"), kw.get("version_id"),
                   "submitted",
                   f"submitted to {kw.get('venue','')}")
        return sid

    # ------------------------------------------------ events
    def event(self, paper_id, version_id, kind, detail=""):
        with self.conn() as c:
            c.execute(
                """INSERT INTO events (paper_id, version_id, kind, detail)
                   VALUES (?,?,?,?)""",
                (paper_id, version_id, kind, detail))

    def events_list(self, paper_id=None, limit=500):
        with self.conn() as c:
            if paper_id is not None:
                rows = c.execute(
                    "SELECT * FROM events WHERE paper_id=? "
                    "ORDER BY id DESC LIMIT ?",
                    (paper_id, limit)).fetchall()
            else:
                rows = c.execute(
                    "SELECT e.*, p.title AS paper_title FROM events e "
                    "LEFT JOIN papers p ON p.id=e.paper_id "
                    "ORDER BY e.id DESC LIMIT ?", (limit,)).fetchall()
        return [dict(r) for r in rows]

    # ------------------------------------------------ stats
    def stats(self):
        with self.conn() as c:
            by_status = {r["status"]: r["n"] for r in c.execute(
                "SELECT status, COUNT(*) AS n FROM papers GROUP BY status")}
            total = c.execute("SELECT COUNT(*) FROM papers").fetchone()[0]
            ready = by_status.get("ready", 0)
            submitted = sum(by_status.get(s, 0) for s in
                            ("submitted", "resubmitted", "in_review"))
        return {"total": total, "ready": ready, "submitted": submitted,
                "by_status": by_status}
