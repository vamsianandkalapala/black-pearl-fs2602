"""Canonical byte serialization for scores and decision snapshots."""

import json
from typing import Any, Dict

from backend.snapshot import canonical_snapshot_bytes

def serialize_score(result: Dict[str, Any]) -> bytes:
    """Serialize score fields with stable keys, separators, and null handling."""
    ordered = {
        "model_version": result["model_version"],
        "probability": result["probability"],
        "score": result["score"],
    }
    return (
        json.dumps(
            ordered,
            ensure_ascii=True,
            allow_nan=False,
            separators=(",", ":"),
        )
        + "\n"
    ).encode("utf-8")


def serialize_decision(result: Dict[str, Any]) -> bytes:
    """Serialize a complete decision using the authoritative snapshot format."""
    return canonical_snapshot_bytes(result)
