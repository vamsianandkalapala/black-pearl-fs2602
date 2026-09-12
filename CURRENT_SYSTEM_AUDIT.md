# BLACK PEARL — FS-2602
# Current System Audit

Date: 2026-09-12  
Scope: Audit and implementation baseline for the complete delivered P1/P2/P3/P4
integration workspace.

## Executive verdict

The current local P1/P2 HTTP integration is real and deterministic at the tested
contract level. P1 remains the authoritative decision engine. P2 is vendored
under `services/p2` with persistent local SQLite storage, audit-chain
verification, and replay through P1. The delivered frontend and gateway are
part of this repository and are the browser-facing integration layer.

The repository contains P1, P2, delivered P3/P4 integration assets, the
gateway, frontend, Dockerfiles, and Compose configuration. There is no
dependency on the prior external Windows P2 folder. Public HTTPS deployment
remains unverified.

## A. Current architecture

### Processes and ports

| Component | Process/command | Current address | Authority |
|---|---|---|---|
| P1 | Uvicorn importing `backend.api.main:app` | `127.0.0.1:8000` | Authoritative score, model, rules, decision, snapshot identity |
| P2 | Uvicorn importing `services.p2.main:app` | `127.0.0.1:8001` locally; `p2:8001` in Compose | Authoritative persistence, audit chain, replay |
| Gateway | Uvicorn importing `gateway.main:app` | `127.0.0.1:8080` | Transport adapter; not a decision authority |
| Browser client | Gateway serves `frontend/index.html` through `StaticFiles` | `http://127.0.0.1:8080/` | Presentation only |

P1 also exposes FastAPI documentation at `/docs`. P2 exposes `/docs` when its
process is running. The gateway has FastAPI documentation as well.

### Data flow

1. The browser submits JSON to gateway `POST /decision`.
2. The gateway forwards the unchanged request to P1 `POST /decision`.
3. P1 validates and normalizes the applicant, creates registered features,
   scores with the versioned model, evaluates the versioned rulebook, and
   returns the authoritative decision package.
4. The gateway sends the P1 response plus the original request to P2
   `POST /snapshot`.
5. P2 verifies the P1 snapshot hash, stores the snapshot and canonical bytes,
   appends a hash-chain audit record, and persists chain state in SQLite.
6. The gateway returns the P1 result with an added `audit` result.
7. Later replay requests go to P2, which loads the persisted request/snapshot
   and calls P1's `/decision` endpoint again for comparison.

The browser does not calculate a score, decision, probability, decision ID, or
hash.

## B. Current file structure and ownership

### P1 and integration workspace

- `backend/api/main.py` — P1 FastAPI application: `/healthz`, `/metrics`,
  `/validate`, `/features`, `/score`, `/decision`, and `/rules/{version}`.
- `backend/decision.py` — authoritative P1 decision orchestration.
- `backend/schemas/applicant.py` and `backend/schemas/decision.py` — P1 input
  and decision contract models.
- `backend/data/validation.py`, `normalization.py`, and `quality.py` —
  validation, deterministic normalization, and data-quality signals.
- `backend/features/registry.py` and `engineering.py` — registered feature
  names/order and feature generation.
- `backend/model/train.py`, `predict.py`, `serialization.py`, `registry.py`,
  and `lineage.py` — deterministic model training, inference, artifact
  identity, serialization, and H+8 migration support.
- `backend/rules/engine.py` — JSON rulebook loading, validation, effective-date
  selection, and evaluation.
- `backend/snapshot.py` and `backend/integrity.py` — canonical decision bytes
  and SHA-256 identities.
- `models/` — `model_v1.joblib`, `model_v2.joblib`, metadata, and manifest.
  `model_v1` is preserved.
- `rules/v1.json` and `rules/v2.json` — data-driven rulebooks.
- `data/raw/training_data.csv` — synthetic model training data.
- `data/raw/data_quality_cases.json` and `demo_cases.json` — quality/demo data.
- `fixtures/replay/decision_v1.json` — deterministic replay fixture.
- `gateway/main.py` — gateway HTTP adapter and static frontend host.
- `frontend/index.html` — minimal browser form using the gateway.
- `tests/` — 74 P1/integration tests covering P1, gateway, determinism,
  security, H+8, and contracts.
- `scripts/train_model.py`, `seed_demo.py`, and `compliance_check.py` —
  training, demo seeding, and compliance checks.
- `bench/bench_decision.py` — local, explicitly non-sealed benchmark.
- `README.md`, `AI_LEDGER.md`, and the existing reports/docs — operational and
  compliance documentation.
- `.env.example` — P1 URL and local P2 database example.
- `.gitignore` — cache, environment, log, and generated-artifact exclusions.

### Integrated P2 service

P2 source is physically present under `services/p2`.

Important P2 files:

- `main.py` — P2 FastAPI routes.
- `database.py` — SQLite schema, snapshot persistence, audit records, and
  persisted chain state.
- `schemas.py` — P1 snapshot submission validation.
- `hashing.py` — canonical JSON bytes and P1 snapshot hash verification.
- `audit.py` — durable audit-chain recording and verification.
- `replay.py` — historical request replay through P1 HTTP/JSON.
- `fairness.py` — prohibited-input presence check only.
- `proxy.py` — explicit limited proxy-analysis response.
- `versioning.py` — small model/rule availability registry.
- `tests/test_p2_integration.py` — temporary-database persistence, tamper,
  and replay tests.
- `integration-test.sqlite` — existing local test database artifact in the
  original P2 folder; integrated runtime databases are configured separately.

The complete P2 Python package and its tests are included in this workspace.

### Delivered deployment files

- `docker-compose.yml` — real P1, P2, and gateway services with named
  persistent `p2_data` storage.
- `Dockerfile.p1` — real P1 image.
- `Dockerfile.p2` — real vendored P2 image.
- `Dockerfile.gateway` — real gateway/frontend image.

## C. API contract

### P1 endpoints

| Method/path | Request | Response/source | Role |
|---|---|---|---|
| `GET /healthz` | None | `{"status":"ok"}` | P1 process health |
| `GET /docs` | None | FastAPI Swagger UI | Documentation |
| `GET /metrics` | None | Prometheus-style text counters | P1 runtime counters |
| `POST /validate` | Applicant JSON | Structured validation result | P1 validation, not a decision |
| `POST /features` | Applicant JSON | Deterministic feature map | P1 feature generation, not a decision |
| `POST /score` | Applicant JSON | Probability, score, model/factor data | P1 model output |
| `POST /decision` | `{"applicant": {...}, "rulebook_version": "v1", "decision_date": "YYYY-MM-DD", optional "language", optional "watchlist"}` | Authoritative versioned decision package containing decision, score, probability, factors, normalized input, feature vector, lineage, quality, watchlist, IDs, and hashes | Authoritative |
| `GET /rules/{version}` | Version path parameter | Rulebook, effective date, rules, SHA-256 | P1 rulebook display/provenance |

### P2 endpoints

| Method/path | Request | Response/source | Role |
|---|---|---|---|
| `GET /healthz` | None | P2 status and `"database":"sqlite"` | P2 health |
| `POST /snapshot` | Full P1 decision, or `{"snapshot": full P1 decision, "request": original request}` | Record status, decision ID, chain hashes, fairness prohibited-input check | P2 persistence/audit |
| `GET /audit/verify` | None | `VALID`/`INVALID`, chain state and reason | P2 audit verification |
| `GET /audit/replay/{decision_id}` | Decision ID | `MATCH`, `MISMATCH`, or `FAILED` plus differences/replayed result | P2 historical replay |
| `POST /compliance/proxy-check` | JSON list of feature names | Limited result stating proxy analysis was not performed | P2 diagnostic only |

### Gateway endpoints

| Method/path | Request | Behavior/response | Authority |
|---|---|---|---|
| `GET /` | None | Serves `frontend/index.html` | Presentation |
| `GET /healthz` | None | Calls P1 and P2 `/healthz` and combines results | Proxy |
| `GET /metrics` | None | Calls P1 `/metrics` and adds a gateway counter currently fixed at zero | Proxy/adapter |
| `POST /decision` | Same request as P1 `/decision` | Calls P1, then P2 `/snapshot`, returns P1 result plus audit result | P1 remains authoritative |
| `GET /audit/verify` | None | Proxies P2 verification | Proxy |
| `GET /audit/replay/{decision_id}` | Decision ID | Proxies P2 replay | Proxy |
| `GET /rules/{version}` | Version path parameter | Proxies P1 rulebook response | Proxy |

Gateway upstream HTTP/JSON failures are mapped to a generic HTTP 502 response
with `upstream_unavailable`; the gateway does not expose upstream exception
details.

## D. Database and persistence

- Database technology: SQLite in the separate P2 service.
- Configuration: `P2_DATABASE_PATH`; default is relative path
  `p2_compliance.db`, resolved relative to the P2 process working directory.
- Existing local artifact: `integration-test.sqlite` is present in the P2
  folder. The default `p2_compliance.db` was not assumed to be a production
  database.
- Persisted snapshot table: decision ID, applicant ID, decision date, complete
  snapshot JSON, original request JSON, canonical bytes, snapshot hash, model
  and rule versions, decision, score, probability, and creation timestamp.
- Persisted audit table: sequence, decision ID, snapshot hash, previous hash,
  current hash, and timestamp.
- Persisted chain state: record count and chain head hash.
- Snapshot persistence: implemented and tested.
- Audit-chain persistence: implemented and tested; it survives process restart
  if the SQLite file is stored on persistent storage.
- Replay: uses persisted historical request/snapshot data, then calls P1 over
  HTTP and compares selected decision identity fields. It currently refuses
  historical model versions other than `v1`.
- Container restart survival: possible for a mounted/persistent SQLite file,
  but no container or volume configuration exists in this repository, so it is
  unverified operationally.
- Production PostgreSQL: missing. No PostgreSQL driver, schema migration, or
  managed database configuration was found.
- Security boundary: the persisted chain anchor is in the same SQLite database;
  compromise of both database contents and chain state is not prevented.

## E. Deployment

- Docker availability check: `docker` was not available on this machine.
- Docker Compose execution: not possible to verify; no compose file exists on
  disk.
- Dockerfiles: absent in the current repository.
- Self-contained composition: missing. P2 is a separate folder/service.
- Local path dependency: P2 is run from
  `C:\Users\Dell\Downloads\P2_Compliance_Engine_Final`; the integration
  workspace itself does not contain it.
- `P2_BASE_URL`: required for the gateway to reach a separately running P2;
  the gateway default is `http://127.0.0.1:8001`.
- Public serving: no public host, DNS, deployment provider, or verified public
  URL exists.
- HTTPS/reverse proxy: none found.
- Current frontend can be served locally by the gateway at port 8080, but this
  is not a public deployment.

## F. Security audit

- Obvious API keys, passwords, tokens, private keys, and secret assignments:
  none found by the source scan.
- Committed `.env` files: none found; only `.env.example` files exist.
- Secret hygiene: `.env` is ignored in both relevant folders. Example files
  contain local URLs/paths, not credentials.
- CORS: P1 allows only `http://127.0.0.1:8080` and
  `http://localhost:8080`, with credentials disabled. This is appropriately
  narrow for the local adapter, but not a production origin configuration.
- Exposed internal ports: P1 8000 and P2 8001 are local-development ports in
  the documented setup. No firewall or public-network policy was found.
- Error leakage: P1 sanitizes validation errors and gateway upstream errors.
  P1 still returns some application error messages for invalid decision
  requests; production review is still required.
- Authentication/authorization: none found for P1, P2, gateway, or audit
  endpoints.
- Insecure defaults: services default to loopback URLs and local SQLite, which
  is safe for a local demo but not production-grade deployment.

## G. FS-2602 requirement mapping

| Requirement | Status | Evidence / limitation |
|---|---|---|
| Alternate-data scorer | IMPLEMENTED | P1 uses income/rent and registered alternate-data features with deterministic Logistic Regression artifacts. |
| Missing records handled without automatic rejection | IMPLEMENTED | Optional fields remain missing; training-only median imputation is recorded. |
| Conflicting records surfaced | PARTIAL | P1 validation/data-quality signals surface conflicts and quality issues; no complete cross-source adjudication policy exists. |
| Deliberately falsified records | MISSING | Documentation explicitly says P1 quality signals are not fraud detection; no falsification detector/provider exists. |
| Decision under 90 seconds | PARTIAL | Local P1 benchmark reported sub-second decision latency; no official sealed or integrated end-to-end measurement exists. |
| Rules as data | IMPLEMENTED | `rules/v1.json` and `v2.json`, loaded and validated by P1. |
| Versioning and effective dates | IMPLEMENTED | Model/rule/feature lineage and rule effective-date validation exist. |
| Exact historical replay | PARTIAL | P2 stores canonical bytes and replays through P1, but replay compares selected fields, supports only v1, and no production historical-version registry exists. |
| Adverse-action top four factors | IMPLEMENTED | P1 returns up to four deterministic adverse-action factors. |
| Applicant-language explanation | PARTIAL | English output and deterministic fallback exist; broad applicant-language coverage is not implemented. |
| Approval-rate parity | MISSING | P2 only checks prohibited input presence; no group approval-rate calculation. |
| Error-rate parity | MISSING | No labeled outcome dataset or error-rate parity calculation. |
| Selected/optimized fairness criterion | MISSING | No selected parity criterion or optimization/tradeoff report. |
| Proxy leakage analysis | PARTIAL | P2 endpoint explicitly reports that feature names alone cannot perform proxy reconstruction/R-squared analysis; actual analysis is absent. |
| Impact simulator | MISSING | No policy/model impact simulator found. |
| Hash-chained audit log | IMPLEMENTED | P2 persists audit records, previous/current hashes, chain state, and tamper verification in SQLite. |
| Watchlist transliteration/homoglyph/name-order handling | MISSING | P1 has typed watchlist states and fail-closed handling, but no provider or matching implementation was found. |
| Equal overblocking penalty | MISSING | No overblocking metric or penalty calculation. |
| No hosted LLM in graded path | IMPLEMENTED | No hosted LLM dependency or external decision API in P1/P2/gateway path. |
| H+8 prohibited-feature migration | PARTIAL | P1 can create v2 without a selected feature while preserving v1; full official event policy, re-audit, fairness impact, and sealed migration evidence are absent. |
| AI ledger | IMPLEMENTED | `AI_LEDGER.md` contains dated implementation/testing entries; its latest entry still says final-regression testing was pending, which is stale relative to the verified 74-test run. |
| Random Author Challenge | MISSING | No implementation or verified evidence found. |
| Determinism | IMPLEMENTED | Fixed model configuration, explicit feature order, canonical serialization, and repeated-decision tests pass. |
| “Where This Breaks” | PARTIAL | Reports and README document several limitations; no single complete challenge-specific break analysis was found. |
| Cost/RAM | MISSING | Latency/throughput benchmark exists; RAM and deployment cost measurements do not. |
| Three-command run | PARTIAL | P1 README has a three-command local setup, but P2 is separate and no verified single-system three-command run exists. |
| `/healthz` | IMPLEMENTED | P1, P2, and gateway health routes exist; P1 smoke check returned HTTP 200. |
| `/metrics` | IMPLEMENTED | P1 exposes Prometheus-style counters; gateway proxies P1 metrics. |
| Seed script | IMPLEMENTED | `scripts/seed_demo.py` exists and is documented. |
| No secrets | IMPLEMENTED | Source scan found no obvious secrets; `.env` is ignored and examples contain placeholders/local configuration. |
| Public website | MISSING | Only a local static browser client exists; no public URL or hosting deployment. |
| Persistent production database | PARTIAL | Durable local SQLite is implemented; production PostgreSQL/managed persistence is absent and unverified. |

## H. Verification performed

All checks below were read-only with respect to production source and behavior.

### P1 tests

Command:

```powershell
.venv\Scripts\python.exe -m pytest
```

Result: **74 passed, 2 warnings** in 11.67 seconds.

### P2 tests

Command attempted:

```powershell
py -m pytest
```

Result: **2 passed** in the integrated repository environment.

### Compile checks

Commands:

```powershell
.venv\Scripts\python.exe -m compileall -q backend gateway tests scripts
py -m compileall -q .
```

Result: P1 and P2 compileall both exited with code 0.

### Local P1 endpoint and determinism smoke checks

Using FastAPI `TestClient` without starting a server:

- P1 `/healthz`: HTTP 200, `{"status":"ok"}`.
- P1 `/docs`: HTTP 200.
- Two identical P1 decision calls produced equal response objects.
- Two canonical serialized decision outputs were byte-identical.

No live multi-process P1/P2/gateway smoke test was rerun in this audit because
the services were not started and the task prohibited implementation changes.
The existing integration report records an earlier local P1→P2 result of P1
HTTP 200, P2 snapshot HTTP 200, audit `VALID`, and replay `MATCH`; that remains
historical evidence, not a new audit execution.

### Docker

`docker` was not available. Docker build/startup was not verified; the real
Dockerfiles and Compose configuration are present.

## I. Final blockers

### P0 — prevents a credible final submission

1. **No public deployment**: no public HTTPS website, reverse proxy, hosting,
   or reachable final URL.
2. **No production persistence**: only local SQLite exists; PostgreSQL or an
   equivalent managed durable database is absent.
3. **Required fairness evidence is missing**: approval parity, error parity,
   selected fairness criterion/tradeoff, proxy leakage analysis, and
   overblocking penalty are not implemented.
4. **Falsified-record handling is missing**: current quality signals must not
   be presented as fraud detection.
5. **Self-contained deployment is unverified**: Dockerfiles/Compose and
   vendored P2 are present, but Docker build/startup could not be run here.
6. **Replay scope is incomplete**: exact byte-identical historical replay
   across retained model/rule versions is not demonstrated as a production
   capability.

### P1 — required for a strong submission

1. Implement or document the Random Author Challenge and complete “Where This
   Breaks” evidence.
2. Add watchlist matching behavior for transliteration, homoglyphs, and
   name-order cases, with equal overblocking measurement.
3. Add impact simulation and an auditable H+8 re-audit/evaluation package.
4. Add RAM/cost measurements and an integrated end-to-end latency result.
5. Expand applicant-language explanations beyond English fallback.
6. Reconcile stale documentation, especially the final AI ledger entry and
   references to missing Docker files.
7. Add authentication/authorization and production network policy before any
   external exposure.

### P2 — improvement/nice-to-have

1. Add a managed migration path and operational backup/restore procedures.
2. Add gateway-specific metrics rather than the current fixed zero counter.
3. Add service-level integration tests that start P1, P2, and gateway together.
4. Add production observability, rate limiting, and structured request
   correlation IDs.

## Final status

**Local P1/P2 integration: PARTIALLY COMPLETE and verified at the contract
level.**

**Full FS-2602 submission readiness: NOT COMPLETE.**

## Post-audit implementation update

The following changes were made after the read-only audit:

- Vendored the complete P2 implementation and its tests into `services/p2`.
- Changed only P2 module imports required for package execution; P2 business
  behavior, API paths, SQLite schema, audit-chain logic, replay behavior, and
  compliance responses were preserved.
- Added `Dockerfile.p1`, `Dockerfile.p2`, `Dockerfile.gateway`, and
  `docker-compose.yml`.
- Added a named `p2_data` volume and configured P2 to store
  `/data/p2_compliance.db` in Compose.
- Added `P2_BASE_URL` and `GATEWAY_PORT` to `.env.example`.
- Removed the integration dependency on the external Windows P2 folder.

Verification after implementation:

- Integrated suite: **76 passed, 2 warnings**.
- P1/P2/gateway compileall: passed.
- P1, P2, and gateway imports: passed.
- Live browser-to-gateway-to-P1-to-P2 smoke test: passed.
- Snapshot persistence: passed.
- Audit verification: `VALID`.
- Replay: `MATCH`.
- P2 restart against the retained SQLite file: passed; audit remained `VALID`
  and replay remained `MATCH`.
- Docker: unavailable on this machine; build/startup unverified.
- PostgreSQL: not implemented or tested; SQLite remains the verified backend.
- Public deployment: not performed.
