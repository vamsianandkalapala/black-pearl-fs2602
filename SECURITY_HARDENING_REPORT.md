# Security and Reproducibility Hardening Report

Audit date: 2026-09-12

## Scope

Inspected the backend, API, schemas, validation/normalization, feature
registry, model loading/training/prediction, rules, snapshots, fixtures,
benchmarks, tests, documentation, generated metadata, and configuration.

## Findings

| Severity | Status | Finding | Evidence | Change/verification |
| --- | --- | --- | --- | --- |
| HIGH | FIXED | Unknown applicant fields were silently ignored by Pydantic. | `Applicant` lacked `extra="forbid"`. | Unknown-field HTTP test now expects 422. |
| MEDIUM | FIXED | Applicant IDs were not explicitly Unicode-normalized. | Identifier entered the snapshot without canonical normalization. | NFC normalization and whitespace rejection added; Unicode determinism tested. |
| HIGH | FIXED | Model predictions did not verify the default artifact identity. | Prediction loaded the fixed path without manifest hash verification. | Default artifact is checked against the manifest; v1 verification passes. |
| MEDIUM | FIXED | Non-finite direct feature values could reach the model boundary. | `_ordered_values` accepted arbitrary values. | Finite numeric validation added and tested. |
| MEDIUM | FIXED | Explicit confirmed/unavailable watchlist results could be ignored. | Decision orchestration accepted all typed statuses. | Those statuses now fail closed; tests cover both. |
| MEDIUM | FIXED | Rulebook version accepted unsafe path characters. | Version was interpolated into a filesystem path. | Version allowlist and resolved-directory check added. |
| LOW | FIXED | Score endpoint could expose internal model-load errors. | Errors were not mapped to a stable API response. | Model failures return a generic HTTP 500 detail. |
| INFO | PARTIAL | Metrics use process-local mutable counters. | `backend/api/main.py`. | Preserved existing observability; durable metrics belong to deployment integration. |

## Security scan

No real API keys, passwords, tokens, private keys, or credentials were found.
Matches were limited to `.env.example` documentation and tests that verify
unregistered secret-like fields are ignored by feature engineering.

No hosted LLM, network call, external watchlist API, or new dependency was
introduced.

## Determinism and reproducibility

- Applicant IDs use NFC normalization.
- Unknown input fields are rejected.
- Model feature values must be finite numeric values or `null`.
- Default model artifact hash is verified against the manifest.
- Rulebook versions are validated before filesystem access.
- Decision snapshots use canonical UTF-8 JSON and SHA-256 identity.
- The same score was serialized 100 times and produced one unique byte output.
- JSON key reordering produced the same decision and snapshot IDs.

## Verification

- Full test suite: 62 passed, 2 warnings in 6.17 seconds.
- `compileall`: PASS.
- Live `/healthz`, `/metrics`, `/validate`, `/features`, `/score`, and `/decision` smoke checks: PASS (all HTTP 200).
- Final local benchmark: 100 decisions, mean 21.695 ms, p95 44.999 ms, max 140.296 ms.
- Benchmark label: `LOCAL BENCHMARK — NOT SEALED EVALUATION`.

## Remaining limitations

Full historical replay storage/execution, fairness and proxy analysis,
watchlist screening, fraud detection, hash-chain audit storage, and complete
H+8 workflow remain incomplete. These are not claimed as fixed.

## Ownership

- P2: replay storage/execution and audit integration.
- P3: fairness, parity, and proxy-leakage analysis.
- P4: watchlist screening and related latency integration.
- Human review: still required.

## Final status

SECURITY HARDENING COMPLETE

Tests: 62 passed, 0 failed
Compileall: PASS
API smoke tests: PASS
Determinism test: PASS
Security scan: PASS
Benchmark: local, not sealed; mean 21.695 ms, p95 44.999 ms, max 140.296 ms
Critical issues remaining: none identified
High issues remaining: none identified in P1 code
P2 dependencies remaining: replay and audit integration
Files modified: recorded in `AI_LEDGER.md`
