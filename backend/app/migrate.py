from sqlalchemy import text
from sqlalchemy.engine import Engine


def upgrade_schema(engine: Engine) -> None:
    """Idempotent startup migration: add new columns + create FTS5 table."""
    with engine.begin() as conn:
        cols = {r[1] for r in conn.execute(text("PRAGMA table_info(users)"))}
        if "personal_deepseek_key_enc" not in cols:
            conn.execute(text(
                "ALTER TABLE users ADD COLUMN personal_deepseek_key_enc TEXT"
            ))
        if "daily_token_quota" not in cols:
            conn.execute(text(
                "ALTER TABLE users ADD COLUMN daily_token_quota INTEGER "
                "NOT NULL DEFAULT 1000000"
            ))

        conn.execute(text("""
            CREATE VIRTUAL TABLE IF NOT EXISTS public_kb_fts USING fts5(
                file_id UNINDEXED, name, content,
                tokenize='trigram'
            )
        """))
