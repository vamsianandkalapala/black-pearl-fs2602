"""Adversarial input and reproducibility regression tests."""

import json
import math
from collections import OrderedDict

from fastapi.testclient import TestClient

from backend.api.main import app
from backend.model.predict import predict_score
from backend.model.serialization import serialize_score


client = TestClient(app)


def applicant():
    return {
        "applicant_id": "安全-001",
        "monthly_income": 2500,
        "monthly_rent": 1000,
        "bank_income": 34000,
        "bank_cashflow": 30000,
        "gig_income": 7000,
        "repayment_history": 7,
        "utility_payment_history": 9,
        "telecom_payment_history": 8,
    }


def request_body():
    return {
        "applicant": applicant(),
        "rulebook_version": "v1",
        "decision_date": "2026-09-12",
        "language": "en",
    }


def test_unknown_applicant_fields_are_rejected():
    payload = request_body()
    payload["applicant"]["unexpected"] = "ignored must not happen"
    assert client.post("/decision", json=payload).status_code == 422


def test_invalid_applicant_values_are_rejected():
    for field, value in (
        ("applicant_id", "   "),
        ("monthly_income", True),
        ("monthly_income", math.nan),
        ("monthly_income", math.inf),
        ("monthly_income", -1),
    ):
        payload = request_body()
        payload["applicant"][field] = value
        if isinstance(value, float) and not math.isfinite(value):
            response = client.post(
                "/decision",
                content=json.dumps(payload, allow_nan=True),
                headers={"content-type": "application/json"},
            )
        else:
            response = client.post("/decision", json=payload)
        assert response.status_code == 422


def test_unicode_id_and_json_key_order_have_stable_decision():
    first = client.post("/decision", json=request_body()).json()
    reordered = OrderedDict(
        (
            ("language", "en"),
            ("decision_date", "2026-09-12"),
            ("rulebook_version", "v1"),
            ("applicant", OrderedDict(reversed(list(applicant().items())))),
        )
    )
    second = client.post("/decision", json=reordered).json()
    assert first["decision_id"] == second["decision_id"]
    assert first["snapshot_hash"] == second["snapshot_hash"]


def test_repeated_score_serialization_is_identical():
    features = {
        "income_to_rent_ratio": 2.5,
        "bank_income": 34000.0,
        "bank_cashflow": 30000.0,
        "gig_income": 7000.0,
        "repayment_history": 7.0,
        "utility_payment_history": 9.0,
        "telecom_payment_history": 8.0,
    }
    outputs = [
        serialize_score(predict_score(features))
        for _ in range(100)
    ]
    assert len(set(outputs)) == 1


def test_nonfinite_features_fail_before_model_prediction():
    features = {
        "income_to_rent_ratio": 2.5,
        "bank_income": float("inf"),
        "bank_cashflow": 30000.0,
        "gig_income": 7000.0,
        "repayment_history": 7.0,
        "utility_payment_history": 9.0,
        "telecom_payment_history": 8.0,
    }
    try:
        predict_score(features)
    except ValueError as error:
        assert "finite numeric" in str(error)
    else:
        raise AssertionError("Non-finite feature was accepted.")


def test_watchlist_confirmed_and_unavailable_fail_closed():
    for status in ("CONFIRMED_MATCH", "UNAVAILABLE"):
        payload = request_body()
        payload["watchlist"] = {
            "status": status,
            "matched": status == "CONFIRMED_MATCH",
            "match_type": "name",
            "confidence": 1.0 if status == "CONFIRMED_MATCH" else None,
            "reason": "screening result",
        }
        response = client.post("/decision", json=payload)
        assert response.status_code == 400


def test_invalid_watchlist_status_is_rejected():
    payload = request_body()
    payload["watchlist"] = {
        "status": "UNKNOWN",
        "matched": False,
        "match_type": None,
        "confidence": None,
        "reason": "invalid",
    }
    assert client.post("/decision", json=payload).status_code == 422


def test_malformed_json_is_rejected_without_server_error():
    response = client.post(
        "/decision",
        content='{"applicant":',
        headers={"content-type": "application/json"},
    )
    assert response.status_code == 422
