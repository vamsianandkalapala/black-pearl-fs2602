# P1/P2 Integration Contract

## A. Purpose

This document defines the current P1 handoff for a future P2 consumer. P1
returns a complete deterministic decision record over HTTP/JSON. P2's actual
repository and endpoint are unavailable in this workspace; any P2 endpoint is
**TBD by P2**.

## B. P1 responsibilities

P1 owns applicant validation, normalization, registered feature engineering,
deterministic model scoring, versioned rules, policy decisions, factors,
adverse-action output, snapshot identity, and this JSON contract.

## C. P2 responsibilities

P2 is expected to persist immutable decision snapshots, implement historical
replay/storage, and integrate audit records/hash chains. P1 does not implement
P2 storage or audit-chain behavior.

## D. Request schema

`POST /decision` accepts:

```json
{
  "applicant": {
    "applicant_id": "fixture-001",
    "monthly_income": 2500,
    "monthly_rent": 1000,
    "bank_income": 34000,
    "bank_cashflow": 30000,
    "gig_income": 7000,
    "repayment_history": 7,
    "utility_payment_history": 9,
    "telecom_payment_history": 8
  },
  "rulebook_version": "v1",
  "decision_date": "2026-09-12",
  "language": "en"
}
```

Applicant fields are validated strictly. Unknown fields and prohibited
sensitive fields are rejected. `decision_date` is an ISO `YYYY-MM-DD` date.

## E. Decision response schema

The response contains `contract_version`, `decision_id`, `snapshot_hash`,
`applicant_id`, `decision`, `score`, `probability`, `decision_date`,
`decision_timestamp`, `model_version`, `model_artifact_sha256`,
`model_metadata_sha256`, `rulebook_version`, `rulebook_sha256`, `rule_id`,
`feature_registry_version`, `feature_registry_hash`, `normalized_input`,
`feature_vector`, `contributing_factors`, `adverse_action`, `data_quality`,
`watchlist`, `language_requested`, `language_used`, and
`decision_serialization_version`.

## F. Reproducibility-critical fields

P2 must persist the request, normalized input, feature vector, exact decision
date, all version/hash fields, score/probability, policy result, factors,
quality signals, watchlist object, `decision_id`, `snapshot_hash`, and the
canonical serialized response bytes or an exact UTF-8 equivalent.

## G. Artifact identity fields

- `model_version` identifies the model lineage version.
- `model_artifact_sha256` identifies the exact model artifact.
- `model_metadata_sha256` identifies the metadata content.
- `rulebook_version` identifies the rule version.
- `rulebook_sha256` identifies the exact rulebook file.
- `feature_registry_version` and `feature_registry_hash` identify the feature set.

These identities are independent and must not be conflated.

## H. Snapshot/hash requirements

`snapshot_hash` is SHA-256 over the snapshot content excluding derived
`decision_id` and `snapshot_hash` fields. Canonical bytes are UTF-8 JSON with
sorted keys, compact separators, explicit `null`, finite JSON numbers, and a
final newline. This is not a hash chain.

## I. Error behavior

- HTTP 422 with `error.code = invalid_request`: malformed JSON or schema input.
- HTTP 400 with `error.code = invalid_decision_request`: invalid dates,
  rule configuration, watchlist fail-closed state, or other request-level
  decision errors.
- HTTP 404: requested rulebook version is unavailable.
- HTTP 500 with `error.code = model_unavailable`: model artifact is missing,
  corrupt, or incompatible.

Responses must not expose local paths or stack traces.

## J. Determinism guarantees

For the same applicant input, model version, rulebook version, feature registry,
decision date, and runtime-compatible artifact, P1 produces the same score,
decision, factors, snapshot hash, decision ID, and canonical bytes. Request JSON
key order does not affect the result. Language fallback does not affect the
numerical decision.

## K. Replay handoff requirements

P1 provides the deterministic fixture at
`fixtures/replay/decision_v1.json`. It demonstrates the exact expected
identities without implementing a replay database or replay endpoint.

## L. Fields P2 must persist

Persist every response field listed in section E, the original request, and the
canonical serialized response bytes. P2 should also persist receipt metadata
outside the reproducibility-critical snapshot if needed for operations.

## M. Fields P2 must not mutate

P2 must not mutate applicant values, normalized input, feature vector, score,
probability, decision, factors, version fields, hashes, watchlist result,
serialization version, decision ID, or snapshot hash.

## N. Versioning rules

`decision_serialization_version`, feature registry version, model version, and
rulebook version are separate namespaces. A new model or rulebook must produce
a new explicit version/identity; historical records must retain old values.

## O. Example request

See section D and `fixtures/replay/decision_v1.json`.

## P. Example response

See the response produced by the fixture test. The exact canonical bytes and
expected identity hashes are checked by `tests/test_p1_integration_contract.py`.

## Q. Integration assumptions

The intended boundary is HTTP/JSON over a local or deployment network. P1 has
not verified P2's client, transport, host, port, CORS, database, or runtime.
No P2 endpoint is assumed; it is **TBD by P2**.

## R. Explicit unknowns

The P2 repository was not available during this integration-contract pass.
Therefore P2's language, version, framework, storage, API, run command, test
command, CORS policy, network assumptions, and replay schema remain unknown.
HTTP/JSON compatibility with the actual P2 implementation is not verified.
