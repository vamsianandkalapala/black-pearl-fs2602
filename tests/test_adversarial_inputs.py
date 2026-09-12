import math
import random
import json

from fastapi.testclient import TestClient

from backend.api.main import app


client = TestClient(app)


def applicant(**overrides):
    value = {
        "applicant_id": "adversarial-001",
        "monthly_income": 2500,
        "monthly_rent": 1000,
    }
    value.update(overrides)
    return value


def test_invalid_inputs_fail_without_server_errors():
    cases = [
        applicant(applicant_id=""),
        applicant(applicant_id="   "),
        applicant(monthly_income="2500"),
        applicant(monthly_rent=True),
        applicant(monthly_income=-1),
        applicant(monthly_rent=-1),
        applicant(monthly_income=math.inf),
        applicant(monthly_rent=math.nan),
        applicant(unknown_sensitive_field="secret"),
    ]
    for payload in cases:
        body = json.dumps(
            {"applicant": payload, "decision_date": "2026-09-12"},
            allow_nan=True,
        )
        response = client.post(
            "/decision",
            content=body,
            headers={"content-type": "application/json"},
        )
        assert response.status_code == 422
        assert "Traceback" not in response.text
        assert "secret" not in response.text


def test_unicode_and_missing_alternate_sources_are_supported():
    response = client.post(
        "/decision",
        json={
            "applicant": applicant(applicant_id="café-借款人"),
            "decision_date": "2026-09-12",
        },
    )
    assert response.status_code == 200
    assert response.json()["data_quality"]["data_preserved"] is True


def test_deterministic_fuzz_inputs_never_return_server_error():
    generator = random.Random(2602)
    for index in range(300):
        payload = applicant(
            applicant_id=f"fuzz-{index}",
            monthly_income=generator.choice([0, 1, 2500, 1_000_000, -1]),
            monthly_rent=generator.choice([0, 1, 1000, 100_000, -1]),
            bank_income=generator.choice([None, 1000, 20_000]),
            gig_income=generator.choice([None, 500, 7000]),
            repayment_history=generator.choice([None, 0, 5, 10]),
        )
        response = client.post(
            "/decision",
            json={"applicant": payload, "decision_date": "2026-09-12"},
        )
        assert response.status_code in {200, 400, 422}
        assert response.status_code < 500
        assert "Traceback" not in response.text
