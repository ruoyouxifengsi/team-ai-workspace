from sqlalchemy import text


def test_engine_executes_select_1(tmp_path, monkeypatch):
    monkeypatch.setenv("DATABASE_URL", f"sqlite:///{tmp_path}/x.db")
    monkeypatch.setenv("ADMIN_INITIAL_PASSWORD", "x")
    from app import db as db_mod
    engine = db_mod.make_engine(f"sqlite:///{tmp_path}/x.db")
    with engine.connect() as conn:
        result = conn.execute(text("SELECT 1")).scalar_one()
        assert result == 1


def test_session_local_yields_session(tmp_path, monkeypatch):
    monkeypatch.setenv("DATABASE_URL", f"sqlite:///{tmp_path}/y.db")
    monkeypatch.setenv("ADMIN_INITIAL_PASSWORD", "x")
    from app import db as db_mod
    engine = db_mod.make_engine(f"sqlite:///{tmp_path}/y.db")
    Session = db_mod.make_session_factory(engine)
    with Session() as s:
        assert s.execute(text("SELECT 2")).scalar_one() == 2
