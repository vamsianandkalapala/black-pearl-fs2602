from fastapi.testclient import TestClient

from gateway.main import app
import gateway.main as gateway


def test_frontend_is_served():
    response = TestClient(app).get("/")
    assert response.status_code == 200
    assert "BLACK PEARL" in response.text


def test_gateway_forwards_authoritative_decision_and_snapshot(monkeypatch):
    calls = []

    def fake_request(method, url, payload=None):
        calls.append((method, url, payload))
        if url.endswith("/decision"):
            return {
                "decision_id": "decision-1",
                "decision": "APPROVED",
                "score": 80,
            }
        return {"audit_status": "RECORDED", "current_hash": "a" * 64}

    monkeypatch.setattr(gateway, "_request", fake_request)
    response = TestClient(app).post(
        "/decision",
        json={"applicant": {"applicant_id": "demo"}},
    )
    assert response.status_code == 200
    assert response.json()["decision"] == "APPROVED"
    assert response.json()["audit"]["audit_status"] == "RECORDED"
    assert calls[0][0:2] == ("POST", f"{gateway.P1_BASE_URL}/decision")
    assert calls[1][0:2] == ("POST", f"{gateway.P2_BASE_URL}/snapshot")
