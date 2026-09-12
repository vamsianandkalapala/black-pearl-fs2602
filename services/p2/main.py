from typing import Any, List

from fastapi import FastAPI, HTTPException

from .audit import AuditEngine
from .database import DATABASE_PATH, get_snapshot
from .fairness import FairnessAuditor
from .proxy import ProxyAnalyzer
from .replay import ReplayEngine
from .schemas import DecisionSnapshot, SnapshotSubmission


app = FastAPI(title="BLACK PEARL P2 Compliance Engine", version="1.0.0")
audit_engine = AuditEngine(DATABASE_PATH)
replay_engine = ReplayEngine(DATABASE_PATH)
fairness_auditor = FairnessAuditor()
proxy_analyzer = ProxyAnalyzer()


@app.get("/healthz")
def health_check():
    return {"status": "ok", "service": "P2 Compliance Engine", "database": "sqlite"}


@app.post("/snapshot")
def record_snapshot(payload: dict[str, Any]):
    if "snapshot" in payload:
        submission = SnapshotSubmission.model_validate(payload)
        snapshot = submission.snapshot.model_dump()
        original_request = submission.request
    else:
        snapshot = DecisionSnapshot.model_validate(payload).model_dump()
        original_request = None
    audit = audit_engine.record_decision(snapshot, original_request)
    return {
        "status": "success",
        "decision_id": snapshot["decision_id"],
        "current_hash": audit["current_hash"],
        "previous_hash": audit["previous_hash"],
        "audit_status": "RECORDED",
        "fairness_check": fairness_auditor.check_prohibited_attributes(
            snapshot["normalized_input"]
        ),
    }


@app.get("/audit/verify")
def verify_audit_chain():
    result = audit_engine.verify_chain()
    return {
        "status": "VALID" if result["valid"] else "INVALID",
        **result,
    }


@app.get("/audit/replay/{decision_id}")
def replay_decision(decision_id: str):
    if get_snapshot(decision_id, DATABASE_PATH) is None:
        raise HTTPException(status_code=404, detail="Decision snapshot not found")
    return replay_engine.replay_decision(decision_id)


@app.post("/compliance/proxy-check")
def test_proxy_leakage(features: List[str]):
    return proxy_analyzer.analyze_feature_proxies(features)
