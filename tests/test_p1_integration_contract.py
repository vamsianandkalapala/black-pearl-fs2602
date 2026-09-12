"""P1/P2 handoff contract tests."""

import hashlib
import json
from collections import OrderedDict
from pathlib import Path

from fastapi.testclient import TestClient

from backend.api.main import app
from backend.model.serialization import serialize_decision
from backend.snapshot import snapshot_hash


client = TestClient(app)
FIXTURE_PATH = Path("fixtures/replay/decision_v1.json")


def test_fixture_contains_required_integration_identity_fields():
    fixture = json.loads(FIXTURE_PATH.read_text(encoding="utf-8"))
    expected = fixture["expected"]
    required = {
        "decision", "score", "probability", "model_version",
        "model_artifact_sha256", "rulebook_version", "rulebook_sha256",
        "feature_registry_version", "feature_registry_hash",
        "snapshot_hash", "canonical_decision_sha256",
    }
    assert required <= set(expected)


def test_fixture_produces_the_same_canonical_decision():
    fixture = json.loads(FIXTURE_PATH.read_text(encoding="utf-8"))
    body = client.post("/decision", json=fixture["request"]).json()
    expected = fixture["expected"]
    for field in (
        "decision", "score", "probability", "model_version",
        "model_artifact_sha256", "rulebook_version", "rulebook_sha256",
        "feature_registry_version", "feature_registry_hash", "snapshot_hash",
    ):
        assert body[field] == expected[field]
    assert body["snapshot_hash"] == snapshot_hash(body)
    assert hashlib.sha256(serialize_decision(body)).hexdigest() == expected[
        "canonical_decision_sha256"
    ]


def test_json_key_order_does_not_change_contract_identity():
    fixture = json.loads(FIXTURE_PATH.read_text(encoding="utf-8"))
    request = fixture["request"]
    reordered = OrderedDict(
        [
            ("language", request["language"]),
            ("decision_date", request["decision_date"]),
            ("rulebook_version", request["rulebook_version"]),
            ("applicant", OrderedDict(reversed(list(request["applicant"].items())))),
        ]
    )
    first = client.post("/decision", json=request).json()
    second = client.post("/decision", json=reordered).json()
    assert serialize_decision(first) == serialize_decision(second)
    assert first["decision_id"] == second["decision_id"]
    assert first["snapshot_hash"] == second["snapshot_hash"]


def test_unknown_sensitive_input_and_malformed_request_are_safe():
    fixture = json.loads(FIXTURE_PATH.read_text(encoding="utf-8"))
    request = json.loads(json.dumps(fixture["request"]))
    request["applicant"]["date_of_birth"] = "1990-01-01"
    response = client.post("/decision", json=request)
    assert response.status_code == 422
    assert "date_of_birth" not in response.text

    malformed = client.post(
        "/decision",
        content='{"applicant":',
        headers={"content-type": "application/json"},
    )
    assert malformed.status_code == 422
    assert malformed.json()["error"]["code"] == "invalid_request"
    assert "C:\\" not in malformed.text
