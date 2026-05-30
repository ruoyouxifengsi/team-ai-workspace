from datetime import datetime

from pydantic import BaseModel


class FileOut(BaseModel):
    id: int
    name: str
    size: int
    mime: str
    uploaded_at: datetime
    is_public: bool


class FileListResponse(BaseModel):
    personal: list[FileOut]
    public: list[FileOut]
