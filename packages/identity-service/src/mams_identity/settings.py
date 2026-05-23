from pydantic_settings import SettingsConfigDict

from mams_core.settings import MAMSBaseSettings


class Settings(MAMSBaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    service_name: str = "mams-identity-service"
    database_url: str = "postgresql+asyncpg://mams:mams_secret@localhost:5432/mams"
    jwt_secret_key: str = "dev-secret-change-in-production"
    jwt_algorithm: str = "HS256"
    jwt_expire_minutes: int = 60


settings = Settings()
