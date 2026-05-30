import time

import httpx
from sqlalchemy.orm import Session as DbSession

from app.chat.service import build_context, estimate_tokens, persist_message
from app.config import Settings
from app.llm.base import LLMResponse
from app.llm.factory import make_client_for_user
from app.models import Conversation, User
from app.quota.exceptions import QuotaExceeded
from app.quota.service import charge, check_and_reset
from app.tools import registry

MAX_STEPS = 20
MAX_RETRIES = 2
CONTEXT_TOKEN_LIMIT = 60_000


class AgentMaxStepsExceeded(Exception):
    pass


class ContextTooLong(Exception):
    pass


class LLMCallFailed(Exception):
    pass


def call_with_retry(client, messages, tools) -> LLMResponse:
    last: Exception | None = None
    for i in range(MAX_RETRIES + 1):
        try:
            return client.chat(messages, tools=tools)
        except httpx.HTTPStatusError as e:
            if 400 <= e.response.status_code < 500:
                raise
            last = e
        except (httpx.TimeoutException, httpx.NetworkError) as e:
            last = e
        time.sleep(2 ** i)
    raise LLMCallFailed(str(last))


def _import_all_tools() -> None:
    """Trigger @register_tool side effects."""
    from app.tools import (  # noqa: F401
        list_files,
        read_docx,
        read_pdf,
        read_text,
        read_xlsx,
        search_public,
        write_docx,
        write_text,
        write_xlsx,
    )


def run_loop(
    db: DbSession,
    settings: Settings,
    user: User,
    conv: Conversation,
    user_message: str,
) -> str:
    _import_all_tools()
    llm, is_personal = make_client_for_user(user, settings)
    if not is_personal:
        check_and_reset(db, user)
        if user.daily_token_used >= user.daily_token_quota:
            raise QuotaExceeded(user.daily_token_used, user.daily_token_quota)

    persist_message(db, conv, role="user", content=user_message)
    messages = build_context(db, conv)
    if estimate_tokens(messages) > CONTEXT_TOKEN_LIMIT:
        raise ContextTooLong(
            f"context > {CONTEXT_TOKEN_LIMIT} tokens; please start a new conversation"
        )

    schemas = registry.all_schemas()
    total_in = total_out = 0

    try:
        for _ in range(MAX_STEPS):
            resp = call_with_retry(llm, messages, schemas)
            total_in += resp.tokens_in
            total_out += resp.tokens_out

            if resp.tool_calls:
                persist_message(
                    db, conv, role="assistant",
                    content=resp.content,
                    tool_calls=resp.tool_calls,
                    tokens_in=resp.tokens_in, tokens_out=resp.tokens_out,
                )
                messages.append({
                    "role": "assistant",
                    "content": resp.content,
                    "tool_calls": [
                        {
                            "id": tc.id, "type": "function",
                            "function": {
                                "name": tc.name,
                                "arguments": _json_dumps(tc.arguments),
                            },
                        }
                        for tc in resp.tool_calls
                    ],
                })
                for tc in resp.tool_calls:
                    result = registry.execute(
                        tc.name, tc.arguments,
                        db=db, settings=settings,
                        user_id=user.id, user_role=user.role,
                    )
                    persist_message(
                        db, conv, role="tool",
                        tool_name=tc.name, tool_call_id=tc.id,
                        tool_result=result,
                    )
                    messages.append({
                        "role": "tool", "tool_call_id": tc.id,
                        "content": _json_dumps(result),
                    })
            else:
                persist_message(
                    db, conv, role="assistant",
                    content=resp.content or "",
                    tokens_in=resp.tokens_in, tokens_out=resp.tokens_out,
                )
                return resp.content or ""

        raise AgentMaxStepsExceeded()
    finally:
        if not is_personal and (total_in + total_out) > 0:
            try:
                charge(db, user, total_in + total_out)
            except Exception:
                pass  # don't mask the original exception
        getattr(llm, "close", lambda: None)()


def _json_dumps(obj) -> str:
    import json
    return json.dumps(obj, ensure_ascii=False, default=str)
