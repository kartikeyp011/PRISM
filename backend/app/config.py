"""Application configuration from environment variables."""

from pydantic_settings import BaseSettings, SettingsConfigDict

from app.contract import get_config_keys


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    LLM_BASE_URL: str = get_config_keys()["LLM_BASE_URL"]["default"]
    LLM_MODEL: str = get_config_keys()["LLM_MODEL"]["default"]
    DATABASE_URL: str = "postgresql+asyncpg://prism:prism@postgres:5432/prism"
    REDIS_URL: str = "redis://redis:6379/0"
    CHROMA_URL: str = "http://chroma:8000"
    EMBEDDING_MODEL: str = "all-MiniLM-L6-v2"

    @property
    def llm_mode(self) -> str:
        return "mock" if not self.LLM_BASE_URL.strip() else "live"


settings = Settings()
