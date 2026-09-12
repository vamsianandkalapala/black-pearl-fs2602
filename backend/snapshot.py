"""Canonical, replay-ready decision snapshot helpers."""

import hashlib
import json
from typing import Any, Dict


def canonical_snapshot_bytes(snapshot: Dict[str, Any]) -> bytes:
    """Serialize a snapshot as stable UTF-8 JSON with explicit null values."""
    return (
        json.dumps(
            snapshot,
            ensure_ascii=True,
            allow_nan=False,
            sort_keys=True,
            separators=(",", ":"),
        )
        + "\n"
    ).encode("utf-8")


def snapshot_hash(snapshot: Dict[str, Any]) -> str:
    """Return a content hash excluding derived identifier and hash fields."""
    content = dict(snapshot)
    content.pop("snapshot_hash", None)
    content.pop("decision_id", None)
    return hashlib.sha256(canonical_snapshot_bytes(content)).hexdigest()


def decision_id(snapshot: Dict[str, Any]) -> str:
    """Return the deterministic identifier for a decision snapshot."""
    content = dict(snapshot)
    content.pop("decision_id", None)
    content.pop("snapshot_hash", None)
    return hashlib.sha256(canonical_snapshot_bytes(content)).hexdigest()
