from pathlib import Path

from sqlalchemy import text
from sqlalchemy.engine import Engine

from app.files.service import list_public_files
from app.tools.registry import register_tool

EXCERPT_LEN = 200


def _extract_text(path: Path, mime: str) -> str:
    """Best-effort text extraction for indexing."""
    try:
        if mime.endswith("wordprocessingml.document"):
            import docx
            d = docx.Document(str(path))
            return "\n".join(p.text for p in d.paragraphs)
        if mime == "application/pdf":
            from pypdf import PdfReader
            r = PdfReader(str(path))
            return "\n".join((p.extract_text() or "") for p in r.pages)
        if mime.endswith("spreadsheetml.sheet"):
            import openpyxl
            wb = openpyxl.load_workbook(str(path), data_only=True, read_only=True)
            chunks = []
            for sname in wb.sheetnames:
                for row in wb[sname].iter_rows(values_only=True):
                    chunks.append(" ".join("" if c is None else str(c) for c in row))
            return "\n".join(chunks)
        return path.read_text(encoding="utf-8", errors="replace")
    except Exception:
        return ""


def reindex_public_kb(engine: Engine) -> None:
    """Rebuild FTS5 index from every public FileRow on disk."""
    from sqlalchemy.orm import sessionmaker
    Session = sessionmaker(bind=engine)
    from app.config import get_settings
    settings = get_settings()
    data_dir = Path(settings.data_dir)
    with Session() as db:
        rows = list_public_files(db)
        with engine.begin() as conn:
            conn.execute(text("DELETE FROM public_kb_fts"))
            for r in rows:
                path = data_dir / r.path
                if not path.exists():
                    continue
                body = _extract_text(path, r.mime)
                conn.execute(
                    text(
                        "INSERT INTO public_kb_fts(file_id, name, content) "
                        "VALUES (:fid, :n, :c)"
                    ),
                    {"fid": r.id, "n": r.original_name, "c": body},
                )


def index_one_file(engine: Engine, file_id: int, name: str, body: str) -> None:
    with engine.begin() as conn:
        conn.execute(
            text("DELETE FROM public_kb_fts WHERE file_id = :fid"),
            {"fid": file_id},
        )
        conn.execute(
            text(
                "INSERT INTO public_kb_fts(file_id, name, content) "
                "VALUES (:fid, :n, :c)"
            ),
            {"fid": file_id, "n": name, "c": body},
        )


def remove_from_index(engine: Engine, file_id: int) -> None:
    with engine.begin() as conn:
        conn.execute(
            text("DELETE FROM public_kb_fts WHERE file_id = :fid"),
            {"fid": file_id},
        )


@register_tool(
    name="search_public",
    description=(
        "Full-text search the public knowledge base. Returns matching files "
        "with file_id, name, and an excerpt around the first match."
    ),
    parameters={
        "type": "object",
        "properties": {
            "query": {"type": "string", "description": "Search keywords"},
        },
        "required": ["query"],
    },
)
def search_public(query: str, *, db, settings, user_id: int, user_role: str) -> list[dict]:
    # Trigram FTS5 MATCH requires queries with >= 3 chars. For shorter queries
    # (common with CJK 2-char keywords), fall back to LIKE which the trigram
    # tokenizer makes efficient.
    if len(query) >= 3:
        sql = text(
            "SELECT file_id, name, "
            "  snippet(public_kb_fts, 2, '[', ']', '...', 16) AS excerpt "
            "FROM public_kb_fts WHERE public_kb_fts MATCH :q LIMIT 10"
        )
        rows = db.execute(sql, {"q": query}).all()
    else:
        like = f"%{query}%"
        sql = text(
            "SELECT file_id, name, "
            "  substr(content, 1, 200) AS excerpt "
            "FROM public_kb_fts "
            "WHERE name LIKE :q OR content LIKE :q LIMIT 10"
        )
        rows = db.execute(sql, {"q": like}).all()
    out = []
    for r in rows:
        out.append({
            "file_id": int(r.file_id),
            "name": r.name,
            "excerpt": (r.excerpt or "")[:EXCERPT_LEN],
        })
    return out
