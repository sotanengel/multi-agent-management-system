from pydantic_settings import SettingsConfigDict
from mams_core.settings import MAMSBaseSettings


class Settings(MAMSBaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    service_name: str = "mams-agent-runtime"
    agent_id: str = ""  # Set by Lifecycle Manager via env var
    nats_url: str = "nats://localhost:4222"
    model_gateway_url: str = "http://localhost:8006"
    lifecycle_manager_url: str = "http://localhost:8004"
    audit_service_url: str = "http://localhost:8008"
    primary_model: str = "anthropic/claude-opus-4-7"
    max_tokens_per_call: int = 4096
    max_steps_per_task: int = 20


settings = Settings()
