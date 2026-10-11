"""File hashing. SHA-256, whole file. Also a fast fingerprint for dedupe."""
import hashlib
from pathlib import Path


def file_hash(path, chunk_size=1 << 20) -> str:
    p = Path(path)
    if not p.is_file():
        return ""
    h = hashlib.sha256()
    try:
        with p.open("rb") as f:
            while True:
                block = f.read(chunk_size)
                if not block:
                    break
                h.update(block)
    except OSError:
        return ""
    return h.hexdigest()


def short(h: str, n: int = 12) -> str:
    return (h or "")[:n]


def fingerprint(path, sample=1 << 20) -> str:
    """Fast fingerprint: size + first MB + last MB. For dedupe only,
    never for verification."""
    p = Path(path)
    if not p.is_file():
        return ""
    try:
        size = p.stat().st_size
    except OSError:
        return ""
    h = hashlib.sha1()
    h.update(str(size).encode())
    with p.open("rb") as f:
        h.update(f.read(sample))
        if size > sample * 2:
            f.seek(-sample, 2)
            h.update(f.read(sample))
    return h.hexdigest()
