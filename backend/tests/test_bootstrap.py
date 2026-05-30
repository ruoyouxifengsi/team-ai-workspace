def test_bootstrap_creates_admin_when_none(env):
    from app import db as db_mod
    from app.bootstrap import ensure_admin_exists
    from app.config import get_settings
    from app.models import User

    settings = get_settings()
    engine = db_mod.make_engine(settings.database_url)
    db_mod.init_schema(engine)
    Session = db_mod.make_session_factory(engine)

    with Session() as s:
        ensure_admin_exists(s, settings)
        admin = s.query(User).filter_by(username="admin").one()
        assert admin.role == "admin"


def test_bootstrap_idempotent(env):
    from app import db as db_mod
    from app.bootstrap import ensure_admin_exists
    from app.config import get_settings
    from app.models import User

    settings = get_settings()
    engine = db_mod.make_engine(settings.database_url)
    db_mod.init_schema(engine)
    Session = db_mod.make_session_factory(engine)

    with Session() as s:
        ensure_admin_exists(s, settings)
        ensure_admin_exists(s, settings)
        count = s.query(User).filter_by(username="admin").count()
        assert count == 1
