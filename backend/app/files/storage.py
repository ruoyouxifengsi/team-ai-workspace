import re
from pathlib import Path

MAX_NAME_LEN = 255
_BAD_CHARS = re.compile(r"[\\/\x00]+")


def sanitize_filename(name: str) -> str:
    stripped = name.strip()
    if not stripped:
        raise ValueError("filename empty")
    clean = _BAD_CHARS.sub("_", stripped).replace("..", "_")
    clean = clean.strip("_")
    if len(clean) > MAX_NAME_LEN:
        # preserve extension
        base, _, ext = clean.rpartition(".")
        if ext and len(ext) < 12:
            keep = MAX_NAME_LEN - len(ext) - 1
            clean = base[:keep] + "." + ext
        else:
            clean = clean[:MAX_NAME_LEN]
    return clean


def user_dir(data_dir: str, user_id: int) -> Path:
    p = Path(data_dir) / "users" / str(user_id)
    p.mkdir(parents=True, exist_ok=True)
    return p


def public_dir(data_dir: str) -> Path:
    p = Path(data_dir) / "public"
    p.mkdir(parents=True, exist_ok=True)
    return p
