"""LOCAL HIDDEN-EVALUATION SIMULATION; not the official sealed evaluation."""

import json
from pathlib import Path

from fastapi.testclient import TestClient

from backend.api.main import app


client = TestClient(app)


def test_local_hidden_evaluation_simulation():
    cases = [
        {
            "applicant_id": "hidden-approved",
            "monthly_income": 2500,
            "monthly_rent": 1000,
            "repayment_history": 8,
        },
        {
            "applicant_id": "hidden-thin-file",
            "monthly_income": 1500,
            "monthly_rent": 1000,
        },
        {
            "applicant_id": "hidden-unicode-café",
            "monthly_income": 2500,
            "monthly_rent": 1000,
            "utility_payment_history": 8,
        },
    ]
    results = []
    for applicant in cases:
        request = {
            "applicant": applicant,
            "rulebook_version": "v1",
            "decision_date": "2026-09-12",
        }
        first = client.post("/decision", json=request)
        second = client.post("/decision", json=json.loads(json.dumps(request)))
        assert first.status_code == second.status_code == 200
        assert first.json() == second.json()
        results.append(first.json()["decision_id"])

    assert len(set(results)) == len(results)
    assert Path("models/model_v1.joblib").exists()
