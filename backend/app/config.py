"""
Central config. Reads from environment / .env file via pydantic-settings.

Why a separate config module: keeps secrets out of code, lets us swap DBs
(SQLite -> Postgres/MySQL) without touching business logic, and gives the
LangGraph agents one canonical place to look up the LLM model name.
"""
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    groq_api_key: str = "missing"
    groq_model: str = "gemma2-9b-it"

    database_url: str = "sqlite:///./complaints.db"
    frontend_origin: str = "http://localhost:5173"


settings = Settings()
