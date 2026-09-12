"""Replay frozen P1 decisions through the real P1 HTTP/JSON contract."""

import json
import os
from typing import Any, Callable, Dict
from urllib import request as url_request

from .database import get_snapshot
from .hashing import canonical_bytes


class ReplayEngine:
    def __init__(
        self,
        database_path=None,
        p1_url: str | None = None,
        transport: Callable[[dict[str, Any]], dict[str, Any]] | None = None,
    ):
        self.database_path = database_path
        self.p1_url = p1_url or os.getenv("P1_BASE_URL", "http://127.0.0.1:8000")
        self.transport = transport

    def replay_decision(self, decision_id: str) -> Dict[str, Any]:
        stored = get_snapshot(decision_id, self.database_path)
        if stored is None:
            return {"replay_status": "FAILED", "reason": "Decision snapshot not found"}
        snapshot = stored["snapshot"]
        original_request = stored["request"] or self._request_from_snapshot(snapshot)
        if snapshot["model_version"] != "v1":
            return {
                "replay_status": "FAILED",
                "reason": "Required historical model version is unavailable.",
            }
        try:
            replayed = self._call_p1(original_request)
        except Exception as error:
            return {"replay_status": "FAILED", "reason": "P1 replay unavailable."}
        differences = []
        for field in (
            "decision",
            "score",
            "probability",
            "model_version",
            "rulebook_version",
            "snapshot_hash",
            "decision_id",
        ):
            if replayed.get(field) != snapshot.get(field):
                differences.append(field)
        return {
            "replay_status": "MATCH" if not differences else "MISMATCH",
            "matches_original": not differences,
            "differences": differences,
            "replayed_result": replayed,
        }

    def _call_p1(self, payload: dict[str, Any]) -> dict[str, Any]:
        if self.transport:
            return self.transport(payload)
        body = json.dumps(payload).encode("utf-8")
        request = url_request.Request(
            f"{self.p1_url.rstrip('/')}/decision",
            data=body,
            headers={"content-type": "application/json"},
            method="POST",
        )
        with url_request.urlopen(request, timeout=10) as response:
            return json.loads(response.read().decode("utf-8"))

    @staticmethod
    def _request_from_snapshot(snapshot: dict[str, Any]) -> dict[str, Any]:
        return {
            "applicant": snapshot["normalized_input"],
            "rulebook_version": snapshot["rulebook_version"],
            "decision_date": snapshot["decision_date"],
            "language": snapshot.get("language_requested", "en"),
        }
