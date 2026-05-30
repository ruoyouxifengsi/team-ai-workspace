from sqlalchemy import create_engine, text

from app.migrate import upgrade_schema


def test_upgrade_schema_adds_user_columns_to_legacy_users_table(tmp_path):
    db_url = f"sqlite:///{tmp_path}/legacy.db"
    engine = create_engine(db_url)
    with engine.begin() as conn:
        conn.execute(text("""
            CREATE TABLE users (
                id INTEGER PRIMARY KEY,
                username TEXT NOT NULL,
                password_hash TEXT NOT NULL,
                role TEXT NOT NULL
            )
        """))

    upgrade_schema(engine)

    with engine.connect() as conn:
        cols = {r[1] for r in conn.execute(text("PRAGMA table_info(users)"))}
    assert "personal_deepseek_key_enc" in cols
    assert "daily_token_quota" in cols


def test_upgrade_schema_creates_fts5_table(tmp_path):
    db_url = f"sqlite:///{tmp_path}/legacy.db"
    engine = create_engine(db_url)
    with engine.begin() as conn:
        conn.execute(text("CREATE TABLE users (id INTEGER PRIMARY KEY)"))

    upgrade_schema(engine)

    with engine.connect() as conn:
        rows = list(conn.execute(text(
            "SELECT name FROM sqlite_master WHERE type='table' AND name='public_kb_fts'"
        )))
    assert len(rows) == 1


def test_upgrade_schema_idempotent(tmp_path):
    db_url = f"sqlite:///{tmp_path}/legacy.db"
    engine = create_engine(db_url)
    with engine.begin() as conn:
        conn.execute(text("""
            CREATE TABLE users (
                id INTEGER PRIMARY KEY,
                username TEXT NOT NULL,
                password_hash TEXT NOT NULL,
                role TEXT NOT NULL
            )
        """))
    upgrade_schema(engine)
    upgrade_schema(engine)
