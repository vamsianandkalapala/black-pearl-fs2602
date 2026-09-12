# BLACK PEARL Integration Report

## Scope

This integration connects the available P1 decision engine with the available
P2 Compliance Engine. No frontend, gateway, Docker, or deployment repository
was present in the attached folders, so those layers were not invented.

## Implemented flow

1. A caller submits an applicant request to P1 `POST /decision`.
2. P1 returns the authoritative decision, score, probability, factors,
   version identities, hashes, normalized input, feature vector, data quality,
   watchlist status, decision ID, and snapshot hash.
3. The caller submits that complete response to P2 `POST /snapshot`.
4. P2 persists the snapshot and original request in SQLite.
5. P2 appends a durable SHA-256 audit-chain record.
6. P2 verifies the persisted chain through `GET /audit/verify`.
7. P2 replays the historical request through P1 using
   `GET /audit/replay/{decision_id}` and reports `MATCH` or `MISMATCH`.

## P2 persistence

P2 now uses SQLite with an idempotent schema initialized by
`database.initialize_database`. The database path is controlled by
`P2_DATABASE_PATH`; it is not an in-memory list. The stored snapshot retains
the complete P1 JSON response, canonical bytes, request, model/rule/feature
identities, score, probability, decision, and snapshot hash.

## Audit integrity

P2 stores `previous_hash`, `current_hash`, an append sequence, a persisted
record count, and a persisted chain head. Verification detects payload
modification, broken links, reordering, missing snapshots, and chain-state
changes. The implementation does not claim protection against compromise of
the database and its chain anchor by the same attacker.

## Replay

Replay calls the real P1 `/decision` HTTP/JSON contract. It does not use the
old P2 income-threshold formula. It compares decision, score, probability,
versions, snapshot hash, and decision ID. It fails explicitly when a required
historical model version is unavailable.

## Verification performed

- P2 tests: `2 passed`
- P1 tests: `72 passed, 2 warnings`
- P1→P2 contract: P1 HTTP response persisted by P2
- Audit verification: `VALID`
- Historical replay: `MATCH`
- P1 and P2 compile checks: passed

## Not implemented or not verifiable

- No frontend or gateway folder was attached.
- No Docker or compose configuration was attached.
- No public deployment was performed.
- P2 fairness remains limited to prohibited-input presence; approval-rate and
  error-rate parity require labeled group data.
- Proxy analysis explicitly reports that feature names alone cannot produce a
  reconstruction test.
- Watchlist screening remains an integration-layer responsibility; P2
  preserves and audits P1's typed watchlist result.
