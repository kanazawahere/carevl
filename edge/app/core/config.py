import os
from pydantic_settings import BaseSettings
from pydantic import ConfigDict

class Settings(BaseSettings):
    SITE_ID: str = "TRAM_TEST_01"
    GITHUB_TOKEN: str = ""
    GITHUB_REPO: str = "owner/carevl-repo" # Expected format: "owner/repo"
    ENCRYPTION_KEY: str = "your-32-byte-encryption-key-here" # 32 bytes for AES-256
    SESSION_SECRET: str = ""  # optional; defaults to ENCRYPTION_KEY for signed session cookie

    # Custom UUIDv5 Namespace for CareVL
    # Generated a static UUID for this project: e.g., using uuid.uuid4() once
    CAREVL_NAMESPACE_UUID: str = "123e4567-e89b-12d3-a456-426614174000"

    DATABASE_URL: str = "sqlite:///./data/carevl.db"

    model_config = ConfigDict(env_file=".env")

settings = Settings()
