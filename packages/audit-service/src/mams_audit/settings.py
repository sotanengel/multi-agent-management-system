from pydantic_settings import SettingsConfigDict
from mams_core.settings import MAMSBaseSettings


class Settings(MAMSBaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    service_name: str = "mams-audit-service"
    database_url: str = "postgresql+asyncpg://mams:mams_secret@localhost:5432/mams"
    nats_url: str = "nats://localhost:4222"
    nats_stream_name: str = "AUDIT"
    nats_subject: str = "audit.events"


settings = Settings()
