from pydantic_settings import SettingsConfigDict
from mams_core.settings import MAMSBaseSettings


class Settings(MAMSBaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    service_name: str = "mams-lifecycle-manager"
    database_url: str = "postgresql+asyncpg://mams:mams_secret@localhost:5432/mams"
    docker_network: str = "mams-mams-network"
    agent_runtime_image: str = "mams-agent-runtime:latest"
    policy_engine_url: str = "http://localhost:8003"


settings = Settings()
