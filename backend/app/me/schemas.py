from pydantic import BaseModel, Field


class MeSettingsOut(BaseModel):
    has_personal_key: bool
    daily_token_used: int
    daily_token_quota: int


class PersonalKeyIn(BaseModel):
    key: str = Field(min_length=1)
