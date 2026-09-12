from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_prefix="VP_")

    database_url: str
    session_ttl_seconds: int = 60 * 60 * 24 * 14
    avatar_storage_path: Path = Path("var/avatars")
    avatar_base_url: str = "/avatars"

    site_url: str = "http://localhost:8000"
    password_reset_ttl_seconds: int = 60 * 60

    smtp_host: str = "smtp.gmail.com"
    smtp_port: int = 587
    smtp_username: str | None = None
    smtp_password: str | None = None
    smtp_from_name: str = "Vantage Point"


settings = Settings()
