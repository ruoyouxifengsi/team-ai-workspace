from sqlalchemy.orm import Session as DbSession

from app.models import Feedback


def submit(db: DbSession, *, user_id: int, conversation_id: int | None, text: str) -> Feedback:
    f = Feedback(user_id=user_id, conversation_id=conversation_id, text=text)
    db.add(f)
    db.commit()
    db.refresh(f)
    return f


def list_all(db: DbSession) -> list[Feedback]:
    return db.query(Feedback).order_by(Feedback.created_at.desc()).all()
