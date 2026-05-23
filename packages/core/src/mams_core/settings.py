"""Base settings for all MAMS services."""
from __future__ import annotations

from pydantic_settings import BaseSettings, SettingsConfigDict


class MAMSBaseSettings(BaseSettings):
    """Shared base settings. Each service extends this."""
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    log_level: str = "INFO"
    service_name: str = "mams-service"
