from pydantic_settings import SettingsConfigDict
from mams_core.settings import MAMSBaseSettings


class Settings(MAMSBaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    service_name: str = "mams-api-gateway"
    identity_service_url: str = "http://localhost:8001"
    policy_engine_url: str = "http://localhost:8003"
    lifecycle_manager_url: str = "http://localhost:8004"
    audit_service_url: str = "http://localhost:8008"
    nats_url: str = "nats://localhost:4222"
    redis_url: str = "redis://localhost:6379"
    jwt_secret_key: str = "dev-secret-change-in-production"
    jwt_algorithm: str = "HS256"
    idempotency_ttl_seconds: int = 86400  # 24 hours


settings = Settings()
