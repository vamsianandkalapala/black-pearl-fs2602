# Decision Snapshot v1

The `/decision` response is a replay-ready snapshot contract. It is JSON,
UTF-8, and does not require importing Python modules.

| Field | Meaning |
| --- | --- |
| `decision_id` | SHA-256 identifier of the snapshot content excluding hash fields |
| `snapshot_hash` | SHA-256 content hash excluding derived `snapshot_hash` and `decision_id` |
| `applicant_id` | Stable applicant identifier |
| `decision_date` | Explicit ISO-8601 calendar date (`YYYY-MM-DD`) |
| `normalized_input` | Deterministically normalized applicant snapshot |
| `feature_vector` | Ordered registered model features |
| `feature_registry_version` | Feature registry identity |
| `feature_registry_hash` | SHA-256 of the feature registry |
| `model_version` | Exact model version used |
| `model_artifact_sha256` | Exact model artifact identity |
| `model_metadata_sha256` | Exact metadata identity recorded in the manifest |
| `rulebook_version` | Exact rulebook version used |
| `rulebook_sha256` | Exact rulebook file identity |
| `score` / `probability` | Model output |
| `decision` | `APPROVED` or `DECLINED` |
| `contributing_factors` | Deterministically ranked model factors |
| `adverse_action` | Factors returned for a declined decision |
| `data_quality` | Non-fraud quality signals |
| `watchlist` | Screening result or explicit integration placeholder |
| `decision_serialization_version` | Canonical serialization contract version |

Canonical bytes use sorted JSON keys, compact separators, explicit `null`,
UTF-8 encoding, and no generated current timestamp. This is not a hash chain;
the audit component owns chained records and tamper detection.
