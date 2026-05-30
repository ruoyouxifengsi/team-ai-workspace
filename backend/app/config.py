from typing import Any

from pydantic import field_validator
from pydantic_settings import (
    BaseSettings,
    DotEnvSettingsSource,
    EnvSettingsSource,
    SettingsConfigDict,
)


class CommaSeparatedListEnvSource(EnvSettingsSource):
    """Env source that skips JSON decoding for cors_origins."""

    def prepare_field_value(
        self, field_name: str, field, value: Any, value_is_complex: bool
    ) -> Any:
        if field_name == "cors_origins" and isinstance(value, str):
            return value
        return super().prepare_field_value(field_name, field, value, value_is_complex)


class CommaSeparatedListDotEnvSource(DotEnvSettingsSource):
    """Same behavior for the .env file source."""

    def prepare_field_value(
        self, field_name: str, field, value: Any, value_is_complex: bool
    ) -> Any:
        if field_name == "cors_origins" and isinstance(value, str):
            return value
        return super().prepare_field_value(field_name, field, value, value_is_complex)


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    database_url: str = "sqlite:///./sqlite.db"
    data_dir: str = "./data"
    session_ttl_hours: int = 168
    admin_username: str = "admin"
    admin_initial_password: str
    cors_origins: list[str] = ["http://localhost:5173"]
    deepseek_api_key: str
    deepseek_base_url: str = "https://api.deepseek.com"
    fernet_key: str

    @field_validator("cors_origins", mode="before")
    @classmethod
    def split_csv(cls, v):
        if isinstance(v, str):
            return [x.strip() for x in v.split(",") if x.strip()]
        return v

    @classmethod
    def settings_customise_sources(
        cls,
        settings_cls,
        init_settings,
        env_settings,
        dotenv_settings,
        file_secret_settings,
    ):
        """Use custom env source."""
        return (
            init_settings,
            CommaSeparatedListEnvSource(settings_cls),
            CommaSeparatedListDotEnvSource(settings_cls),
            file_secret_settings,
        )


def get_settings() -> Settings:
    return Settings()
