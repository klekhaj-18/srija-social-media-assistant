from pydantic_settings import BaseSettings
from pathlib import Path


class Settings(BaseSettings):
    # Server
    host: str = "127.0.0.1"
    port: int = 8600

    # Database
    database_url: str = "sqlite+aiosqlite:///./srija_social.db"

    # Instagram OAuth
    instagram_app_id: str = ""
    instagram_app_secret: str = ""
    instagram_redirect_uri: str = "http://localhost:8600/api/auth/instagram/callback"

    # AI Provider
    anthropic_api_key: str = ""

    # Google Drive
    google_drive_credentials_file: str = ""
    google_drive_folder_id: str = ""

    # Token encryption
    token_encryption_key: str = ""

    # Paths
    upload_dir: Path = Path("backend/static/images")

    model_config = {"env_file": ".env", "env_file_encoding": "utf-8"}


settings = Settings()
