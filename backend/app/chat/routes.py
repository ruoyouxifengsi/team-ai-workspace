from fastapi import APIRouter, Depends, HTTPException, Response, status
from sqlalchemy.orm import Session as DbSession

from app.chat import service
from app.chat.schemas import (
    ConversationCreate,
    ConversationOut,
    ConversationUpdate,
    MessageOut,
    SendRequest,
)
from app.deps import current_user, get_db
from app.models import User

router = APIRouter(prefix="/api/chat", tags=["chat"])


def _to_conv_out(c) -> ConversationOut:
    return ConversationOut(
        id=c.id, title=c.title, created_at=c.created_at, updated_at=c.updated_at,
    )


@router.get("/conversations", response_model=list[ConversationOut])
def list_convs(
    db: DbSession = Depends(get_db),  # noqa: B008
    user: User = Depends(current_user),  # noqa: B008
):
    return [_to_conv_out(c) for c in service.list_conversations(db, user.id)]


@router.post("/conversations", response_model=ConversationOut, status_code=201)
def create_conv(
    body: ConversationCreate,
    db: DbSession = Depends(get_db),  # noqa: B008
    user: User = Depends(current_user),  # noqa: B008
):
    c = service.create_conversation(db, user.id, body.title)
    return _to_conv_out(c)


@router.put("/conversations/{conv_id}", response_model=ConversationOut)
def rename(
    conv_id: int, body: ConversationUpdate,
    db: DbSession = Depends(get_db),  # noqa: B008
    user: User = Depends(current_user),  # noqa: B008
):
    ok = service.update_title(db, conv_id, user.id, body.title)
    if not ok:
        raise HTTPException(status.HTTP_404_NOT_FOUND)
    c = service.get_conversation(db, conv_id, user.id)
    return _to_conv_out(c)


@router.delete("/conversations/{conv_id}", status_code=204)
def delete(
    conv_id: int,
    db: DbSession = Depends(get_db),  # noqa: B008
    user: User = Depends(current_user),  # noqa: B008
):
    try:
        ok = service.delete_conversation(db, conv_id, user.id)
    except PermissionError:
        raise HTTPException(status.HTTP_404_NOT_FOUND) from None
    if not ok:
        raise HTTPException(status.HTTP_404_NOT_FOUND)
    return Response(status_code=204)


@router.get("/conversations/{conv_id}/messages", response_model=list[MessageOut])
def messages(
    conv_id: int,
    db: DbSession = Depends(get_db),  # noqa: B008
    user: User = Depends(current_user),  # noqa: B008
):
    c = service.get_conversation(db, conv_id, user.id)
    if c is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND)
    rows = service.list_messages(db, conv_id, user.id)
    return [
        MessageOut(id=m.id, role=m.role, content=m.content, created_at=m.created_at)
        for m in rows
        if m.role in ("user", "assistant") and (m.content or "").strip()
    ]


MAX_MESSAGE_CHARS = 10_000


@router.post("/conversations/{conv_id}/send")
def send(
    conv_id: int,
    body: SendRequest,
    db: DbSession = Depends(get_db),  # noqa: B008
    user: User = Depends(current_user),  # noqa: B008
):
    from app.agent.loop import (
        AgentMaxStepsExceeded,
        ContextTooLong,
        LLMCallFailed,
        run_loop,
    )
    from app.chat.schemas import SendResponse
    from app.config import get_settings
    from app.quota.exceptions import QuotaExceeded

    if len(body.content) > MAX_MESSAGE_CHARS:
        raise HTTPException(
            status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            "message too long; split into shorter messages",
        )
    conv = service.get_conversation(db, conv_id, user.id)
    if conv is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND)
    try:
        reply = run_loop(db, get_settings(), user, conv, body.content)
    except QuotaExceeded as e:
        raise HTTPException(
            status.HTTP_429_TOO_MANY_REQUESTS,
            f"daily quota exhausted ({e.used}/{e.limit}); add personal key in settings",
        ) from None
    except ContextTooLong:
        raise HTTPException(
            status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            "conversation too long; please start a new conversation",
        ) from None
    except AgentMaxStepsExceeded:
        raise HTTPException(
            status.HTTP_422_UNPROCESSABLE_ENTITY,
            "AI went off the rails; please rephrase and try again",
        ) from None
    except LLMCallFailed as e:
        raise HTTPException(
            status.HTTP_503_SERVICE_UNAVAILABLE,
            f"LLM unavailable: {e}",
        ) from None
    return SendResponse(assistant_content=reply)
