"""Generate Docker container run specs from RoleBundle."""
from __future__ import annotations

import uuid
from dataclasses import dataclass, field

from mams_core.schemas.agent import RoleBundle
from mams_lifecycle.settings import settings


@dataclass
class DockerRunSpec:
    """Parameters for docker.containers.run()."""
    image: str
    name: str
    environment: dict[str, str] = field(default_factory=dict)
    network: str = ""
    cpu_period: int = 100000
    cpu_quota: int = 100000  # 1.0 CPU = 100000/100000
    mem_limit: str = "512m"
    cap_drop: list[str] = field(default_factory=lambda: ["ALL"])
    security_opt: list[str] = field(default_factory=lambda: ["no-new-privileges:true"])
    read_only: bool = True
    tmpfs: dict[str, str] = field(default_factory=lambda: {"/tmp": "rw,noexec,nosuid,size=64m"})
    labels: dict[str, str] = field(default_factory=dict)
    detach: bool = True


def role_bundle_to_spec(agent_id: uuid.UUID, role_bundle: RoleBundle) -> DockerRunSpec:
    """Convert a RoleBundle to a Docker run spec with security hardening."""
    limits = role_bundle.computation.limits

    # Parse CPU limit string e.g. "1.0" -> quota
    try:
        cpu_float = float(limits.cpu_limit)
    except (ValueError, AttributeError):
        cpu_float = 1.0
    cpu_quota = int(cpu_float * 100000)

    return DockerRunSpec(
        image=settings.agent_runtime_image,
        name=f"mams-agent-{agent_id}",
        environment={
            "AGENT_ID": str(agent_id),
            "ROLE_BUNDLE_NAME": role_bundle.name,
            "PRIMARY_MODEL": role_bundle.computation.primary_model,
            "MAX_TOKENS_PER_CALL": str(limits.max_tokens_per_call),
            "MAX_STEPS_PER_TASK": str(limits.max_steps_per_task),
            "NATS_URL": "nats://nats:4222",
            "MODEL_GATEWAY_URL": "http://model-gateway:8000",
            "LIFECYCLE_MANAGER_URL": "http://lifecycle-manager:8000",
            "AUDIT_SERVICE_URL": "http://audit-service:8000",
        },
        network=settings.docker_network,
        cpu_period=100000,
        cpu_quota=cpu_quota,
        mem_limit=limits.memory_limit,
        cap_drop=["ALL"],
        security_opt=["no-new-privileges:true"],
        read_only=True,
        tmpfs={"/tmp": "rw,noexec,nosuid,size=64m"},
        labels={
            "mams.agent_id": str(agent_id),
            "mams.role_bundle": role_bundle.name,
            "mams.managed": "true",
        },
        detach=True,
    )
