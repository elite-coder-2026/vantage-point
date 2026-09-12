from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_prefix="VP_")

    database_url: str
    session_ttl_seconds: int = 60 * 60 * 24 * 14
    avatar_storage_path: Path = Path("var/avatars")
    avatar_base_url: str = "/avatars"
    max_avatar_bytes: int = 5 * 1024 * 1024

    media_storage_path: Path = Path("var/media")
    media_base_url: str = "/media"
    max_image_bytes: int = 10 * 1024 * 1024
    max_video_bytes: int = 10 * 1024 * 1024
    max_audio_bytes: int = 10 * 1024 * 1024
    max_document_bytes: int = 10 * 1024 * 1024

    site_url: str = "http://localhost:8000"
    password_reset_ttl_seconds: int = 60 * 60

    smtp_host: str = "smtp.gmail.com"
    smtp_port: int = 587
    smtp_username: str | None = None
    smtp_password: str | None = None
    smtp_from_name: str = "Vantage Point"


settings = Settings()
