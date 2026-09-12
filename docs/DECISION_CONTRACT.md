# Decision Contract v1

`POST /decision` is a language-independent JSON-over-HTTP contract. A client
does not need to import Python code.

## Request

The request contains `applicant`, `rulebook_version`, `decision_date`, and
`language`. `decision_date` is required so system time cannot change a score.
Unsupported languages deterministically fall back to English and are reported
in `language_used`.

## Response

The response contains the final `APPROVED` or `DECLINED` decision, score,
probability, model/rulebook/feature-registry versions, deterministic
contributing factors, adverse-action factors, data-quality signals, watchlist
placeholder, normalized input snapshot, feature vector, and `decision_id`.

`decision_id` is the SHA-256 hash of the canonical decision serialization.
Rules are loaded from `rules/{rulebook_version}.json`; changing rule data does
not require changing application source code.

This batch does not implement fairness measurement, watchlist screening, fraud
detection, or hash-chained audit logs. Those integrations must not be inferred
from this contract.

JSON is UTF-8 with stable sorted keys for canonical bytes. Numbers are emitted
as JSON numbers without NaN or infinity; absent optional values are explicit
`null`. Dates use `YYYY-MM-DD`. Decisions are `APPROVED` or `DECLINED`.
Invalid dates, unknown rulebooks, and invalid requests return HTTP 400/404
errors. See `docs/DECISION_SNAPSHOT.md` for replay fields and hashes.
