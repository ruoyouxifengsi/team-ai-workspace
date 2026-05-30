from fastapi import APIRouter, Depends, Response
from sqlalchemy.orm import Session as DbSession

from app.config import Settings
from app.deps import current_user, get_db, get_settings_dep
from app.me.schemas import MeSettingsOut, PersonalKeyIn
from app.models import User
from app.users.service import clear_personal_key, set_personal_key

router = APIRouter(prefix="/api/me", tags=["me"])


@router.get("/settings", response_model=MeSettingsOut)
def get_settings_me(
    user: User = Depends(current_user),  # noqa: B008
):
    return MeSettingsOut(
        has_personal_key=bool(user.personal_deepseek_key_enc),
        daily_token_used=user.daily_token_used or 0,
        daily_token_quota=user.daily_token_quota,
    )


@router.put("/settings/key", status_code=204)
def put_key(
    body: PersonalKeyIn,
    db: DbSession = Depends(get_db),  # noqa: B008
    settings: Settings = Depends(get_settings_dep),  # noqa: B008
    user: User = Depends(current_user),  # noqa: B008
):
    set_personal_key(db, user.id, body.key, settings.fernet_key.encode())
    return Response(status_code=204)


@router.delete("/settings/key", status_code=204)
def del_key(
    db: DbSession = Depends(get_db),  # noqa: B008
    user: User = Depends(current_user),  # noqa: B008
):
    clear_personal_key(db, user.id)
    return Response(status_code=204)
