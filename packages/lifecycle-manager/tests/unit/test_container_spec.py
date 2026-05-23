import uuid
import pytest
from mams_lifecycle.container_spec import role_bundle_to_spec


def test_container_spec_security_hardening(sample_role_bundle, sample_agent_id):
    spec = role_bundle_to_spec(sample_agent_id, sample_role_bundle)
    assert "ALL" in spec.cap_drop
    assert any("no-new-privileges" in opt for opt in spec.security_opt)
    assert spec.read_only is True
    assert spec.detach is True


def test_container_spec_name_includes_agent_id(sample_role_bundle, sample_agent_id):
    spec = role_bundle_to_spec(sample_agent_id, sample_role_bundle)
    assert str(sample_agent_id) in spec.name


def test_container_spec_environment_has_required_vars(sample_role_bundle, sample_agent_id):
    spec = role_bundle_to_spec(sample_agent_id, sample_role_bundle)
    assert "AGENT_ID" in spec.environment
    assert spec.environment["AGENT_ID"] == str(sample_agent_id)
    assert "PRIMARY_MODEL" in spec.environment
    assert "NATS_URL" in spec.environment


def test_container_spec_labels(sample_role_bundle, sample_agent_id):
    spec = role_bundle_to_spec(sample_agent_id, sample_role_bundle)
    assert spec.labels.get("mams.managed") == "true"
    assert spec.labels.get("mams.agent_id") == str(sample_agent_id)


def test_container_spec_cpu_limit(sample_role_bundle, sample_agent_id):
    spec = role_bundle_to_spec(sample_agent_id, sample_role_bundle)
    # cpu_limit = "0.5" → cpu_quota = 50000
    assert spec.cpu_quota == 50000


def test_container_spec_memory_limit(sample_role_bundle, sample_agent_id):
    spec = role_bundle_to_spec(sample_agent_id, sample_role_bundle)
    assert spec.mem_limit == "256m"
