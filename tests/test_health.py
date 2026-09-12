from fastapi.testclient import TestClient

from backend.api.main import app


client = TestClient(app)


def test_healthz_returns_ok() -> None:
    """The health endpoint should confirm that the API is running."""
    response = client.get("/healthz")

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_validate_endpoint_accepts_valid_applicant() -> None:
    response = client.post(
        "/validate",
        json={
            "applicant_id": "applicant-001",
            "monthly_income": 30000,
            "monthly_rent": 10000,
        },
    )

    assert response.status_code == 200
    assert response.json()["is_valid"] is True
    assert response.json()["errors"] == []


def test_validate_endpoint_does_not_make_a_decision() -> None:
    response = client.post(
        "/validate",
        json={
            "applicant_id": "applicant-001",
            "monthly_income": 30000,
            "monthly_rent": 10000,
        },
    )

    assert "decision" not in response.json()
    assert "approved" not in response.json()
    assert "declined" not in response.json()
