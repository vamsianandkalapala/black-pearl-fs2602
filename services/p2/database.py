"""Small persistent SQLite database used by the P2 compliance service."""

import json
import os
import sqlite3
from pathlib import Path
from typing import Any, Iterable


DATABASE_PATH = Path(os.getenv("P2_DATABASE_PATH", "p2_compliance.db"))


def connect(database_path: Path | None = None) -> sqlite3.Connection:
    connection = sqlite3.connect(database_path or DATABASE_PATH)
    connection.row_factory = sqlite3.Row
    connection.execute("PRAGMA foreign_keys = ON")
    return connection


def initialize_database(database_path: Path | None = None) -> None:
    with connect(database_path) as connection:
        connection.executescript(
            """
            CREATE TABLE IF NOT EXISTS decision_snapshots (
                decision_id TEXT PRIMARY KEY,
                applicant_id TEXT NOT NULL,
                decision_date TEXT NOT NULL,
                snapshot_json TEXT NOT NULL,
                request_json TEXT,
                canonical_bytes BLOB NOT NULL,
                snapshot_hash TEXT NOT NULL,
                model_version TEXT NOT NULL,
                rulebook_version TEXT NOT NULL,
                decision TEXT NOT NULL,
                score INTEGER NOT NULL,
                probability REAL NOT NULL,
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
            );
            CREATE INDEX IF NOT EXISTS idx_snapshots_applicant
                ON decision_snapshots(applicant_id);
            CREATE TABLE IF NOT EXISTS audit_records (
                sequence INTEGER PRIMARY KEY AUTOINCREMENT,
                decision_id TEXT NOT NULL UNIQUE,
                snapshot_hash TEXT NOT NULL,
                previous_hash TEXT NOT NULL,
                current_hash TEXT NOT NULL,
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY(decision_id) REFERENCES decision_snapshots(decision_id)
            );
            CREATE TABLE IF NOT EXISTS chain_state (
                id INTEGER PRIMARY KEY CHECK (id = 1),
                record_count INTEGER NOT NULL,
                head_hash TEXT NOT NULL
            );
            INSERT OR IGNORE INTO chain_state(id, record_count, head_hash)
                VALUES (1, 0, '0000000000000000000000000000000000000000000000000000000000000000');
            """
        )


def save_snapshot(
    snapshot: dict[str, Any],
    request: dict[str, Any] | None,
    canonical_bytes: bytes,
    database_path: Path | None = None,
) -> dict[str, Any]:
    initialize_database(database_path)
    decision_id = snapshot["decision_id"]
    with connect(database_path) as connection:
        existing = connection.execute(
            "SELECT decision_id, snapshot_hash FROM decision_snapshots WHERE decision_id = ?",
            (decision_id,),
        ).fetchone()
        if existing:
            if existing["snapshot_hash"] != snapshot["snapshot_hash"]:
                raise ValueError("Decision ID already exists with a different snapshot.")
            audit = connection.execute(
                "SELECT * FROM audit_records WHERE decision_id = ?",
                (decision_id,),
            ).fetchone()
            return dict(audit)

        state = connection.execute(
            "SELECT record_count, head_hash FROM chain_state WHERE id = 1"
        ).fetchone()
        previous_hash = state["head_hash"]
        current_hash = compute_chain_hash(snapshot, canonical_bytes, previous_hash)
        connection.execute(
            """
            INSERT INTO decision_snapshots (
                decision_id, applicant_id, decision_date, snapshot_json,
                request_json, canonical_bytes, snapshot_hash, model_version,
                rulebook_version, decision, score, probability
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                decision_id,
                snapshot["applicant_id"],
                snapshot["decision_date"],
                json.dumps(snapshot, sort_keys=True, separators=(",", ":")),
                json.dumps(request, sort_keys=True, separators=(",", ":"))
                if request is not None
                else None,
                canonical_bytes,
                snapshot["snapshot_hash"],
                snapshot["model_version"],
                snapshot["rulebook_version"],
                snapshot["decision"],
                snapshot["score"],
                snapshot["probability"],
            ),
        )
        cursor = connection.execute(
            """
            INSERT INTO audit_records
                (decision_id, snapshot_hash, previous_hash, current_hash)
            VALUES (?, ?, ?, ?)
            """,
            (decision_id, snapshot["snapshot_hash"], previous_hash, current_hash),
        )
        sequence = cursor.lastrowid
        connection.execute(
            "UPDATE chain_state SET record_count = ?, head_hash = ? WHERE id = 1",
            (state["record_count"] + 1, current_hash),
        )
        return {
            "sequence": sequence,
            "decision_id": decision_id,
            "previous_hash": previous_hash,
            "current_hash": current_hash,
        }


def get_snapshot(decision_id: str, database_path: Path | None = None) -> dict[str, Any] | None:
    initialize_database(database_path)
    with connect(database_path) as connection:
        row = connection.execute(
            "SELECT * FROM decision_snapshots WHERE decision_id = ?",
            (decision_id,),
        ).fetchone()
    if row is None:
        return None
    result = dict(row)
    result["snapshot"] = json.loads(result.pop("snapshot_json"))
    result["request"] = (
        json.loads(result.pop("request_json"))
        if result.get("request_json")
        else None
    )
    return result


def list_audit_records(database_path: Path | None = None) -> list[dict[str, Any]]:
    initialize_database(database_path)
    with connect(database_path) as connection:
        return [
            dict(row)
            for row in connection.execute(
                "SELECT * FROM audit_records ORDER BY sequence"
            ).fetchall()
        ]


def chain_state(database_path: Path | None = None) -> dict[str, Any]:
    initialize_database(database_path)
    with connect(database_path) as connection:
        return dict(
            connection.execute("SELECT * FROM chain_state WHERE id = 1").fetchone()
        )


def compute_chain_hash(snapshot: dict[str, Any], canonical_bytes: bytes, previous_hash: str) -> str:
    import hashlib

    payload = (
        canonical_bytes
        + b":"
        + previous_hash.encode("ascii")
    )
    return hashlib.sha256(payload).hexdigest()
