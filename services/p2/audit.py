"""Persistent audit-chain operations."""

from pathlib import Path
from typing import Any

from .database import (
    chain_state,
    compute_chain_hash,
    connect,
    initialize_database,
    list_audit_records,
    save_snapshot,
)
from .hashing import canonical_bytes, verify_snapshot_hash


class AuditEngine:
    def __init__(self, database_path: Path | None = None):
        self.database_path = database_path
        initialize_database(database_path)

    def record_decision(
        self,
        snapshot: dict[str, Any],
        request: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        if not verify_snapshot_hash(snapshot):
            raise ValueError("P1 snapshot hash verification failed.")
        return save_snapshot(
            snapshot,
            request,
            canonical_bytes(snapshot),
            self.database_path,
        )

    def verify_chain(self) -> dict[str, Any]:
        records = list_audit_records(self.database_path)
        state = chain_state(self.database_path)
        previous = "0" * 64
        for record in records:
            snapshot_row = self._snapshot_row(record["decision_id"])
            if snapshot_row is None:
                return {"valid": False, "reason": "snapshot_missing"}
            snapshot = snapshot_row["snapshot"]
            canonical = canonical_bytes(snapshot)
            if record["previous_hash"] != previous:
                return {"valid": False, "reason": "previous_hash_mismatch"}
            expected = compute_chain_hash(snapshot, canonical, previous)
            if record["current_hash"] != expected:
                return {"valid": False, "reason": "current_hash_mismatch"}
            previous = record["current_hash"]
        valid = (
            state["record_count"] == len(records)
            and state["head_hash"] == previous
        )
        return {
            "valid": valid,
            "reason": "ok" if valid else "chain_state_mismatch",
            "total_records": len(records),
            "head_hash": previous,
        }

    def _snapshot_row(self, decision_id: str) -> dict[str, Any] | None:
        with connect(self.database_path) as connection:
            row = connection.execute(
                "SELECT snapshot_json FROM decision_snapshots WHERE decision_id = ?",
                (decision_id,),
            ).fetchone()
        if row is None:
            return None
        import json

        return {"snapshot": json.loads(row["snapshot_json"])}
