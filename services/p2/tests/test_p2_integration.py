import json
from pathlib import Path

from services.p2.audit import AuditEngine
from services.p2.database import connect
from services.p2.hashing import canonical_bytes
from services.p2.replay import ReplayEngine


def snapshot():
    content = {
        "contract_version": "v1",
        "applicant_id": "p2-test",
        "decision": "APPROVED",
        "probability": 0.8,
        "score": 80,
        "model_version": "v1",
        "model_artifact_sha256": "a" * 64,
        "model_metadata_sha256": "b" * 64,
        "rulebook_version": "v1",
        "rulebook_sha256": "c" * 64,
        "feature_registry_version": "v1",
        "feature_registry_hash": "d" * 64,
        "decision_date": "2026-09-12",
        "contributing_factors": [],
        "adverse_action": [],
        "data_quality": {"signals": []},
        "watchlist": {"status": "NOT_SCREENED"},
        "normalized_input": {
            "applicant_id": "p2-test",
            "monthly_income": 2500.0,
            "monthly_rent": 1000.0,
            "bank_income": None,
            "utility_payment_history": None,
            "telecom_payment_history": None,
            "bank_cashflow": None,
            "gig_income": None,
            "repayment_history": None,
        },
        "feature_vector": {
            "income_to_rent_ratio": 2.5,
            "bank_income": None,
            "bank_cashflow": None,
            "gig_income": None,
            "repayment_history": None,
            "utility_payment_history": None,
            "telecom_payment_history": None,
        },
        "decision_serialization_version": "v1",
        "language_requested": "en",
    }
    import hashlib
    content["snapshot_hash"] = hashlib.sha256(
        canonical_bytes(content)
    ).hexdigest()
    content["decision_id"] = hashlib.sha256(
        canonical_bytes(content)
    ).hexdigest()
    return content


def test_persistent_chain_and_tamper_detection(tmp_path: Path):
    database = tmp_path / "p2.sqlite"
    engine = AuditEngine(database)
    record = engine.record_decision(snapshot())
    assert record["previous_hash"] == "0" * 64
    assert engine.verify_chain()["valid"] is True

    with connect(database) as connection:
        connection.execute(
            "UPDATE audit_records SET current_hash = ? WHERE decision_id = ?",
            ("e" * 64, record["decision_id"]),
        )
    assert engine.verify_chain()["valid"] is False


def test_replay_uses_stored_snapshot_and_real_transport(tmp_path: Path):
    database = tmp_path / "p2.sqlite"
    original = snapshot()
    AuditEngine(database).record_decision(original)
    replay = ReplayEngine(
        database,
        transport=lambda payload: original,
    )
    result = replay.replay_decision(original["decision_id"])
    assert result["replay_status"] == "MATCH"
