from pydantic_settings import SettingsConfigDict
from mams_core.settings import MAMSBaseSettings


class Settings(MAMSBaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    service_name: str = "mams-model-gateway"
    database_url: str = "postgresql+asyncpg://mams:mams_secret@localhost:5432/mams"
    anthropic_api_key: str = ""
    ollama_base_url: str = "http://localhost:11434"
    request_timeout_seconds: int = 120


settings = Settings()
