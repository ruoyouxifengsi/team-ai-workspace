import json
from typing import Any

from sqlalchemy.orm import Session as DbSession

from app.agent.prompts import SYSTEM_PROMPT
from app.llm.base import ToolCall
from app.models import Conversation, Message


def create_conversation(db: DbSession, user_id: int, title: str | None = None) -> Conversation:
    c = Conversation(user_id=user_id, title=title or "新会话")
    db.add(c)
    db.commit()
    db.refresh(c)
    return c


def list_conversations(db: DbSession, user_id: int) -> list[Conversation]:
    return (
        db.query(Conversation)
        .filter(Conversation.user_id == user_id)
        .order_by(Conversation.updated_at.desc())
        .all()
    )


def get_conversation(db: DbSession, conv_id: int, user_id: int) -> Conversation | None:
    c = db.get(Conversation, conv_id)
    if c is None or c.user_id != user_id:
        return None
    return c


def update_title(db: DbSession, conv_id: int, user_id: int, title: str) -> bool:
    c = get_conversation(db, conv_id, user_id)
    if c is None:
        return False
    c.title = title[:120]
    db.commit()
    return True


def delete_conversation(db: DbSession, conv_id: int, user_id: int) -> bool:
    c = db.get(Conversation, conv_id)
    if c is None:
        return False
    if c.user_id != user_id:
        raise PermissionError("cannot delete others' conversation")
    db.query(Message).filter(Message.conversation_id == conv_id).delete()
    db.delete(c)
    db.commit()
    return True


def list_messages(db: DbSession, conv_id: int, user_id: int) -> list[Message]:
    c = get_conversation(db, conv_id, user_id)
    if c is None:
        return []
    return (
        db.query(Message)
        .filter(Message.conversation_id == conv_id)
        .order_by(Message.created_at.asc(), Message.id.asc())
        .all()
    )


def persist_message(
    db: DbSession,
    conv: Conversation,
    *,
    role: str,
    content: str | None = None,
    tool_calls: list[ToolCall] | None = None,
    tool_name: str | None = None,
    tool_args: dict | None = None,
    tool_result: Any = None,
    tool_call_id: str | None = None,
    tokens_in: int = 0,
    tokens_out: int = 0,
) -> Message:
    serialized_calls = None
    if tool_calls:
        serialized_calls = json.dumps(
            [{"id": tc.id, "name": tc.name, "arguments": tc.arguments} for tc in tool_calls],
            ensure_ascii=False,
        )
    m = Message(
        conversation_id=conv.id,
        role=role,
        content=content,
        tool_name=tool_name,
        tool_args=(
            json.dumps(tool_args, ensure_ascii=False)
            if tool_args is not None
            else serialized_calls
        ),
        tool_result=(
            json.dumps(tool_result, ensure_ascii=False, default=str)
            if tool_result is not None
            else None
        ),
        tool_call_id=tool_call_id,
        tokens_in=tokens_in,
        tokens_out=tokens_out,
    )
    db.add(m)
    # Touch conversation updated_at
    from datetime import datetime
    conv.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(m)
    return m


def build_context(db: DbSession, conv: Conversation) -> list[dict]:
    """Rebuild OpenAI-format message list with system prompt + ordered history."""
    out: list[dict] = [{"role": "system", "content": SYSTEM_PROMPT}]
    rows = (
        db.query(Message)
        .filter(Message.conversation_id == conv.id)
        .order_by(Message.created_at.asc(), Message.id.asc())
        .all()
    )
    for r in rows:
        if r.role == "user":
            out.append({"role": "user", "content": r.content or ""})
        elif r.role == "assistant":
            if r.tool_args:
                calls = json.loads(r.tool_args)
                if isinstance(calls, list):
                    out.append({
                        "role": "assistant",
                        "content": r.content,
                        "tool_calls": [
                            {
                                "id": c["id"],
                                "type": "function",
                                "function": {
                                    "name": c["name"],
                                    "arguments": json.dumps(c["arguments"], ensure_ascii=False),
                                },
                            }
                            for c in calls
                        ],
                    })
                    continue
            out.append({"role": "assistant", "content": r.content or ""})
        elif r.role == "tool":
            out.append({
                "role": "tool",
                "tool_call_id": r.tool_call_id or "",
                "content": r.tool_result or "",
            })
    return out


def estimate_tokens(messages: list[dict]) -> int:
    """Rough 4-chars-per-token estimate over JSON-serialized payload."""
    return len(json.dumps(messages, ensure_ascii=False)) // 4
