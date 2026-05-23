from mams_core.settings import MAMSBaseSettings
from pydantic_settings import SettingsConfigDict


class Settings(MAMSBaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")
    service_name: str = "mams-policy-engine"


settings = Settings()
