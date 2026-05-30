from typing import Literal

from pydantic import BaseModel


class CreateUserRequest(BaseModel):
    username: str
    password: str
    role: Literal["admin", "member"] = "member"


class UserOut(BaseModel):
    id: int
    username: str
    role: str
    daily_token_used: int


class UpdatePasswordRequest(BaseModel):
    password: str
