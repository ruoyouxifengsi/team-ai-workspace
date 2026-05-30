from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import get_settings
from app.db import init_schema, make_engine, make_session_factory
from app.deps import set_session_factory


def create_app() -> FastAPI:
    settings = get_settings()
    engine = make_engine(settings.database_url)
    init_schema(engine)
    from app.migrate import upgrade_schema
    upgrade_schema(engine)
    from app.tools.search_public import reindex_public_kb
    reindex_public_kb(engine)
    set_session_factory(make_session_factory(engine))

    from app.bootstrap import ensure_admin_exists
    Session = make_session_factory(engine)
    with Session() as s:
        ensure_admin_exists(s, settings)

    app = FastAPI(title="Shared AI Workspace")
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    from app.auth.routes import router as auth_router
    app.include_router(auth_router)

    from app.users.routes import router as users_router
    app.include_router(users_router)

    from app.files.routes import router as files_router
    app.include_router(files_router)

    from app.chat.routes import router as chat_router
    app.include_router(chat_router)

    from app.me.routes import router as me_router
    app.include_router(me_router)

    from app.feedback.routes import router as feedback_router
    app.include_router(feedback_router)

    @app.get("/api/healthz")
    def healthz():
        return {"status": "ok"}

    return app


app = create_app()
