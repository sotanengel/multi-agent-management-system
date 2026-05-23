import uuid
from mams_core.idempotency import operation_key


def test_operation_key_format():
    uid = uuid.uuid4()
    key = operation_key(uid)
    assert key == f"op:{uid}"
