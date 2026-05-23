"""Docker SDK wrapper for agent container management."""
from __future__ import annotations

import logging
import uuid

import docker
import docker.errors

from mams_core.errors import ContainerError
from mams_core.schemas.agent import RoleBundle
from mams_lifecycle.container_spec import DockerRunSpec, role_bundle_to_spec

logger = logging.getLogger(__name__)

_docker_client: docker.DockerClient | None = None


def get_docker_client() -> docker.DockerClient:
    global _docker_client
    if _docker_client is None:
        _docker_client = docker.from_env()
    return _docker_client


def create_agent_container(agent_id: uuid.UUID, role_bundle: RoleBundle) -> str:
    """Create and start a Docker container for an agent. Returns container_id."""
    spec = role_bundle_to_spec(agent_id, role_bundle)
    try:
        client = get_docker_client()
        container = client.containers.run(
            spec.image,
            name=spec.name,
            environment=spec.environment,
            network=spec.network,
            cpu_period=spec.cpu_period,
            cpu_quota=spec.cpu_quota,
            mem_limit=spec.mem_limit,
            cap_drop=spec.cap_drop,
            security_opt=spec.security_opt,
            read_only=spec.read_only,
            tmpfs=spec.tmpfs,
            labels=spec.labels,
            detach=spec.detach,
            remove=False,
        )
        return container.id
    except docker.errors.ImageNotFound as e:
        raise ContainerError(f"Agent runtime image not found: {e}") from e
    except docker.errors.DockerException as e:
        raise ContainerError(f"Failed to create container: {e}") from e


def stop_agent_container(container_id: str) -> None:
    """Stop and remove a container by ID."""
    try:
        client = get_docker_client()
        container = client.containers.get(container_id)
        container.stop(timeout=10)
        container.remove()
    except docker.errors.NotFound:
        logger.warning("Container %s not found (already removed?)", container_id)
    except docker.errors.DockerException as e:
        raise ContainerError(f"Failed to stop container: {e}") from e
