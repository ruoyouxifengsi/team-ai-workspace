from datetime import datetime

from pydantic import BaseModel, Field


class FeedbackIn(BaseModel):
    text: str = Field(min_length=1, max_length=5000)
    conversation_id: int | None = None


class FeedbackOut(BaseModel):
    id: int
    user_id: int
    conversation_id: int | None
    text: str
    created_at: datetime
