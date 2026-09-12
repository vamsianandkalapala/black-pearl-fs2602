"""Small HTTP gateway that keeps P1 authoritative and forwards audit work to P2."""

import os
from typing import Any

import httpx
from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles


P1_BASE_URL = os.getenv("P1_BASE_URL", "http://127.0.0.1:8000").rstrip("/")
P2_BASE_URL = os.getenv("P2_BASE_URL", "http://127.0.0.1:8001").rstrip("/")
app = FastAPI(title="BLACK PEARL Gateway", version="1.0.0")


def _request(method: str, url: str, payload: dict[str, Any] | None = None) -> dict:
    try:
        response = httpx.request(method, url, json=payload, timeout=15.0)
        response.raise_for_status()
        return response.json()
    except (httpx.HTTPError, ValueError) as error:
        raise HTTPException(
            status_code=502,
            detail={"code": "upstream_unavailable", "message": "Backend service unavailable."},
        ) from error


@app.get("/healthz")
def healthz() -> dict:
    p1 = _request("GET", f"{P1_BASE_URL}/healthz")
    p2 = _request("GET", f"{P2_BASE_URL}/healthz")
    return {"status": "ok", "p1": p1, "p2": p2}


@app.get("/metrics")
def metrics() -> dict:
    return {
        "p1": _request("GET", f"{P1_BASE_URL}/metrics"),
        "gateway": {"decision_requests_total": 0},
    }


@app.post("/decision")
def decision(payload: dict[str, Any]) -> dict:
    """Obtain the authoritative P1 decision, then persist it through P2."""
    result = _request("POST", f"{P1_BASE_URL}/decision", payload)
    audit = _request(
        "POST",
        f"{P2_BASE_URL}/snapshot",
        {"snapshot": result, "request": payload},
    )
    return {**result, "audit": audit}


@app.get("/audit/verify")
def audit_verify() -> dict:
    return _request("GET", f"{P2_BASE_URL}/audit/verify")


@app.get("/audit/replay/{decision_id}")
def audit_replay(decision_id: str) -> dict:
    return _request("GET", f"{P2_BASE_URL}/audit/replay/{decision_id}")


@app.get("/rules/{version}")
def rules(version: str) -> dict:
    return _request("GET", f"{P1_BASE_URL}/rules/{version}")


app.mount(
    "/",
    StaticFiles(
        directory=os.path.join(os.path.dirname(__file__), "..", "frontend"),
        html=True,
    ),
    name="frontend",
)
