"""Batch 6 replay, lineage, effective-date, and contract tests."""

import copy
import json
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from backend.api.main import app
from backend.features.registry import allowed_feature_names_at
from backend.model.lineage import prepare_h8_transition, verify_model_artifact
from backend.rules.engine import evaluate_rulebook, load_rulebook
from backend.snapshot import canonical_snapshot_bytes, snapshot_hash


client = TestClient(app)


def decision_request(language="en"):
    return {
        "applicant": {
            "applicant_id": "batch6",
            "monthly_income": 2500,
            "monthly_rent": 1000,
            "bank_income": 34000,
            "bank_cashflow": 30000,
            "gig_income": 7000,
            "repayment_history": 7,
            "utility_payment_history": 9,
            "telecom_payment_history": 8,
        },
        "rulebook_version": "v1",
        "decision_date": "2026-09-12",
        "language": language,
    }


def test_snapshot_hash_changes_when_snapshot_changes():
    snapshot = client.post("/decision", json=decision_request()).json()
    original = snapshot_hash(snapshot)

    changed_score = copy.deepcopy(snapshot)
    changed_score["score"] += 1
    changed_rule = copy.deepcopy(snapshot)
    changed_rule["rulebook_version"] = "v2"
    changed_feature = copy.deepcopy(snapshot)
    changed_feature["feature_vector"]["bank_income"] += 1

    assert original == snapshot["snapshot_hash"]
    assert snapshot_hash(changed_score) != original
    assert snapshot_hash(changed_rule) != original
    assert snapshot_hash(changed_feature) != original
    assert canonical_snapshot_bytes(snapshot) == canonical_snapshot_bytes(snapshot)


def test_rule_effective_date_boundaries():
    rulebook = {
        "version": "test",
        "rules": [
            {
                "rule_id": "temporary",
                "rulebook_version": "test",
                "effective_from": "2026-09-12",
                "effective_to": "2026-09-13",
                "priority": 1,
                "description": "Temporary test rule.",
                "condition": {"field": "score", "operator": "gte", "value": 0},
                "action": "APPROVED",
                "reason": "test",
                "active": True,
            }
        ],
    }
    context = {"score": 50}
    with pytest.raises(ValueError):
        evaluate_rulebook(rulebook, context, "2026-09-11")
    assert evaluate_rulebook(rulebook, context, "2026-09-12")["action"] == "APPROVED"
    assert evaluate_rulebook(rulebook, context, "2026-09-13")["action"] == "APPROVED"
    with pytest.raises(ValueError):
        evaluate_rulebook(rulebook, context, "2026-09-14")


def test_invalid_and_unavailable_rulebooks_fail_safely():
    invalid_path = Path("rules") / "_invalid_batch6.json"
    invalid_path.write_text(
        '{"version":"_invalid_batch6","rules":[{"rule_id":"bad","effective_from":"2026-09-14","effective_to":"2026-09-13"}]}',
        encoding="utf-8",
    )
    try:
        with pytest.raises(ValueError):
            load_rulebook("_invalid_batch6", Path("rules"))
    finally:
        invalid_path.unlink()
    with pytest.raises(FileNotFoundError):
        load_rulebook("v999", Path("rules"))
    response = client.post(
        "/decision",
        json={**decision_request(), "decision_date": "not-a-date"},
    )
    assert response.status_code == 400


def test_model_lineage_and_h8_preparation_preserve_v1():
    assert verify_model_artifact("v1") is True
    transition = prepare_h8_transition("repayment_history")
    assert transition["parent_model_version"] == "v1"
    assert transition["new_model_version"] == "v2"
    assert "repayment_history" not in transition["allowed_features"]
    with pytest.raises(ValueError):
        prepare_h8_transition("bank_income")


def test_language_does_not_change_numerical_decision():
    english = client.post("/decision", json=decision_request("en")).json()
    fallback = client.post("/decision", json=decision_request("fr")).json()
    assert english["decision"] == fallback["decision"]
    assert english["score"] == fallback["score"]
    assert english["probability"] == fallback["probability"]
    assert fallback["language_used"] == "en"


def test_watchlist_contract_accepts_deterministic_statuses():
    request = decision_request()
    request["watchlist"] = {
        "status": "POSSIBLE_MATCH",
        "matched": True,
        "match_type": "name",
        "confidence": 0.5,
        "reason": "Integration component reported a possible match.",
    }
    response = client.post("/decision", json=request)
    assert response.status_code == 200
    assert response.json()["watchlist"]["status"] == "POSSIBLE_MATCH"


def test_prohibition_resolution_is_date_specific():
    assert "repayment_history" in allowed_feature_names_at("2026-09-12")


def test_replay_fixture_matches_current_snapshot_contract():
    fixture = json.loads(
        Path("fixtures/replay/decision_v1.json").read_text(encoding="utf-8")
    )
    response = client.post("/decision", json=fixture["request"])
    body = response.json()
    expected = fixture["expected"]
    assert body["snapshot_hash"] == expected["snapshot_hash"]
    assert body["decision"] == expected["decision"]
    assert body["score"] == expected["score"]
    assert body["model_version"] == expected["model_version"]
    assert body["rulebook_version"] == expected["rulebook_version"]
