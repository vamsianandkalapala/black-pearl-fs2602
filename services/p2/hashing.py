"""Deterministic hashing for P1 snapshots and the durable audit chain."""

import hashlib
import json
from typing import Any, Dict


def canonical_bytes(data: Dict[str, Any]) -> bytes:
    return (
        json.dumps(
            data,
            ensure_ascii=True,
            allow_nan=False,
            sort_keys=True,
            separators=(",", ":"),
        )
        + "\n"
    ).encode("utf-8")


def compute_record_hash(record_data: Dict[str, Any], previous_hash: str) -> str:
    return hashlib.sha256(
        canonical_bytes(record_data) + b":" + previous_hash.encode("ascii")
    ).hexdigest()


def verify_snapshot_hash(snapshot: Dict[str, Any]) -> bool:
    expected = snapshot.get("snapshot_hash")
    content = dict(snapshot)
    content.pop("snapshot_hash", None)
    content.pop("decision_id", None)
    return expected == hashlib.sha256(canonical_bytes(content)).hexdigest()
