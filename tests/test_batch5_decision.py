"""Deterministic Batch 5 decision-engine tests."""

import json

from fastapi.testclient import TestClient

from backend.api.main import app
from backend.model.serialization import serialize_decision


client = TestClient(app)


def applicant_payload(**overrides):
    payload = {
        "applicant_id": "batch5-demo",
        "monthly_income": 2500,
        "monthly_rent": 1000,
        "bank_income": 34000,
        "bank_cashflow": 30000,
        "gig_income": 7000,
        "repayment_history": 7,
        "utility_payment_history": 9,
        "telecom_payment_history": 8,
    }
    payload.update(overrides)
    return payload


def decision_payload(**overrides):
    return {
        "applicant": applicant_payload(**overrides.pop("applicant", {})),
        "rulebook_version": overrides.pop("rulebook_version", "v1"),
        "decision_date": overrides.pop("decision_date", "2026-09-12"),
        "language": overrides.pop("language", "en"),
        **overrides,
    }


def test_decision_contains_versioned_contract_and_is_approved():
    response = client.post("/decision", json=decision_payload())

    assert response.status_code == 200
    body = response.json()
    assert body["decision"] == "APPROVED"
    assert body["model_version"] == "v1"
    assert body["rulebook_version"] == "v1"
    assert body["feature_registry_version"] == "v1"
    assert body["decision_id"]
    assert body["normalized_input"]["applicant_id"] == "batch5-demo"


def test_rulebook_v2_is_loaded_from_data():
    response = client.post(
        "/decision",
        json=decision_payload(rulebook_version="v2"),
    )

    assert response.status_code == 200
    assert response.json()["rulebook_version"] == "v2"


def test_declined_decision_returns_only_meaningful_factors():
    response = client.post(
        "/decision",
        json=decision_payload(
            applicant={
                "applicant_id": "low-data",
                "monthly_income": 1200,
                "monthly_rent": 1000,
                "bank_income": 18000,
                "bank_cashflow": 15000,
                "gig_income": 0,
                "repayment_history": 2,
                "utility_payment_history": 4,
                "telecom_payment_history": 3,
            }
        ),
    )

    assert response.status_code == 200
    body = response.json()
    assert body["decision"] == "DECLINED"
    assert len(body["adverse_action"]) == 4
    assert body["adverse_action"] == body["contributing_factors"]
    assert all(item["feature_name"] != "applicant_id" for item in body["adverse_action"])


def test_unknown_language_falls_back_to_english():
    response = client.post("/decision", json=decision_payload(language="xx"))

    assert response.status_code == 200
    assert response.json()["language_requested"] == "xx"
    assert response.json()["language_used"] == "en"


def test_unknown_rulebook_returns_a_client_error():
    response = client.post(
        "/decision",
        json=decision_payload(rulebook_version="v999"),
    )

    assert response.status_code == 404


def test_repeated_decision_has_identical_canonical_bytes():
    request = decision_payload()
    first = client.post("/decision", json=request).json()
    second = client.post("/decision", json=request).json()

    assert serialize_decision(first) == serialize_decision(second)
    assert first["decision_id"] == second["decision_id"]


def test_rulebook_json_has_data_driven_fields():
    for version in ("v1", "v2"):
        with open(f"rules/{version}.json", encoding="utf-8") as rule_file:
            rulebook = json.load(rule_file)
        assert rulebook["version"] == version
        assert rulebook["rules"]
        assert all(
            {"rule_id", "rulebook_version", "effective_from", "priority",
             "description", "condition", "action", "reason", "active"}
            <= set(rule)
            for rule in rulebook["rules"]
        )
