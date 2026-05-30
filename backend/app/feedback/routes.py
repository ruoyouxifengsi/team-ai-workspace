from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session as DbSession

from app.deps import current_user, get_db, require_admin
from app.feedback import service
from app.feedback.schemas import FeedbackIn, FeedbackOut
from app.models import User

router = APIRouter(tags=["feedback"])


@router.post("/api/feedback", response_model=FeedbackOut, status_code=201)
def submit(
    body: FeedbackIn,
    db: DbSession = Depends(get_db),  # noqa: B008
    user: User = Depends(current_user),  # noqa: B008
):
    f = service.submit(db, user_id=user.id,
                       conversation_id=body.conversation_id, text=body.text)
    return FeedbackOut(
        id=f.id, user_id=f.user_id, conversation_id=f.conversation_id,
        text=f.text, created_at=f.created_at,
    )


@router.get("/api/admin/feedback", response_model=list[FeedbackOut])
def list_admin(
    db: DbSession = Depends(get_db),  # noqa: B008
    _admin: User = Depends(require_admin),  # noqa: B008
):
    return [
        FeedbackOut(
            id=f.id, user_id=f.user_id, conversation_id=f.conversation_id,
            text=f.text, created_at=f.created_at,
        )
        for f in service.list_all(db)
    ]
