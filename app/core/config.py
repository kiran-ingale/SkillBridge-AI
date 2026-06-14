from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "SkillBridge AI"
    environment: str = "development"
    groq_api_key: str | None = None
    google_api_key: str | None = None
    skillbridge_model: str = "groq/llama-3.1-8b-instant"
    github_token: str | None = None
    search_api_key: str | None = None

    model_config = SettingsConfigDict(
        env_file=(".env", "skillbridge_agent/.env"),
        env_file_encoding="utf-8",
        extra="ignore",
    )


@lru_cache
def get_settings() -> Settings:
    return Settings()
