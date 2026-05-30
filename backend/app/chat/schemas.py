from datetime import datetime

from pydantic import BaseModel


class ConversationOut(BaseModel):
    id: int
    title: str
    created_at: datetime
    updated_at: datetime


class ConversationCreate(BaseModel):
    title: str | None = None


class ConversationUpdate(BaseModel):
    title: str


class MessageOut(BaseModel):
    id: int
    role: str  # 'user' | 'assistant' (tool messages hidden from UI)
    content: str | None
    created_at: datetime


class SendRequest(BaseModel):
    content: str


class SendResponse(BaseModel):
    assistant_content: str
