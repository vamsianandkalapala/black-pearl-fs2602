# BLACK PEARL — FS-2602

## Problem

FS-2602 is about reproducible credit decisioning for thin-file borrowers. This
project is a software-only prototype for making future credit decisions
deterministic, explainable, and reproducible.

## Intended system

The planned flow is:

Applicant data → validation → normalization → feature engineering →
deterministic model → score → versioned rules → decision → explanation.

The project now includes a small, deterministic decision-engine demonstration.
It is not the complete FS-2602 submission.

## Person 1 responsibilities

Person 1 owns the decision-engine foundation:

- Applicant data ingestion and schema
- Validation and missing-data handling
- Normalization and feature engineering
- Deterministic scoring
- Versioned rules integration
- Approve/decline decisions and explanations
- Decision API and determinism tests

## Current status

Implemented:

- Minimal FastAPI application
- `GET /healthz` endpoint
- Basic Pydantic applicant schema
- Versioned rules-as-data evaluation
- Deterministic approve/decline decision package
- Model-derived contributing factors and adverse-action output
- Basic health test
- Deterministic Logistic Regression model and score

Not implemented yet:

- Full historical replay and hash-chain audit integration
- Database, frontend, and audit/replay systems
- Full fairness, parity, and proxy-leakage evaluation
- Watchlist screening and fraud detection

## Setup

From the project root, create a virtual environment:

```powershell
python -m venv .venv
```

Activate it on Windows PowerShell:

```powershell
.venv\Scripts\Activate.ps1
```

Install dependencies:

```powershell
pip install -r requirements.txt
```

## Start the API

Run:

```powershell
uvicorn backend.api.main:app --reload --host 127.0.0.1 --port 8000
```

The health endpoint is available at:

```text
http://127.0.0.1:8000/healthz
```

FastAPI's interactive documentation is available at:

```text
http://127.0.0.1:8000/docs
```

## Run the test

```powershell
pytest
```

The health test checks that `/healthz` returns:

```json
{"status": "ok"}
```

## 3-Command Run

From the project root in a clean Python environment:

```powershell
python -m venv .venv; .venv\Scripts\python.exe -m pip install -r requirements.txt
.venv\Scripts\python.exe scripts\train_model.py
.venv\Scripts\python.exe -m uvicorn backend.api.main:app --host 127.0.0.1 --port 8000
```

The first command creates the environment and installs dependencies, the
second creates the model artifact, and the third starts the API.

The API exposes `/healthz`, `/metrics`, `/validate`, `/features`, `/score`, and
`/decision`.

`/metrics` exposes three domain counters for validation, feature generation, and
scoring requests. These are runtime counters, not performance claims.

The repository also contains `data/raw/data_quality_cases.json` and
`backend/data/quality.py` for deterministic data-quality signals. These signals
surface suspicious or inconsistent records; they are not fraud detection.

## Train the prototype model

The current training data is clearly labelled synthetic data in
`data/raw/training_data.csv`. It is not real applicant performance data.

Run:

```powershell
.venv\Scripts\python.exe scripts\train_model.py
```

This creates the versioned model artifact and metadata in `models/`.
The model uses median imputation fitted only on the training data, followed by
standard scaling and Logistic Regression. The current model version is `v1`.

After training, `POST /score` returns a model probability and prototype score.
`POST /decision` applies the selected JSON rulebook to that score and returns a
versioned decision package. The rules are in `rules/v1.json` and
`rules/v2.json`; changing rule data does not require changing Python source.

## Decision demo

```powershell
$body = @{
  applicant = @{
    applicant_id = "demo-001"
    monthly_income = 2500
    monthly_rent = 1000
    bank_income = 34000
    bank_cashflow = 30000
    gig_income = 7000
    repayment_history = 7
    utility_payment_history = 9
    telecom_payment_history = 8
  }
  rulebook_version = "v1"
  decision_date = "2026-09-12"
  language = "en"
} | ConvertTo-Json -Depth 5

Invoke-RestMethod -Method Post -Uri http://127.0.0.1:8000/decision `
  -ContentType "application/json" -Body $body
```

The language-independent request and response contract is documented in
`docs/DECISION_CONTRACT.md`. English is supported now; unsupported languages
are reported and deterministically fall back to English. Fairness, watchlist,
historical replay, and hash-chain audit work remain integration work.

## Batch 6 replay and hardening

Decision responses now include a deterministic snapshot hash, rulebook hash,
model artifact/metadata identity, normalized input, and feature vector.
`docs/DECISION_SNAPSHOT.md` documents the fields. The small fixture at
`fixtures/replay/decision_v1.json` demonstrates the expected v1 identity; it
is not a complete historical replay service.

Run the local benchmark with:

```powershell
.venv\Scripts\python.exe bench\bench_decision.py
```

The output is labelled `LOCAL BENCHMARK — NOT SEALED EVALUATION` and must not
be presented as the official 90-second evaluation.

## P1 Integration Contract

P1 accepts applicant data, an explicit `decision_date`, a rulebook version, and
an optional language/watchlist result at `POST /decision`. It returns the
decision, score, probability, deterministic factors, normalized input, feature
vector, model/rule/feature versions and hashes, quality signals, watchlist
status, `decision_id`, `snapshot_hash`, and serialization version.

P2 should persist the complete request and response, canonical UTF-8 response
bytes, and every reproducibility-critical version/hash field. P1 guarantees
deterministic output for the same versioned inputs and artifact identities.
P1 does not implement P2's replay database, historical replay execution, or
hash-chain audit storage.

See `docs/P1_P2_INTEGRATION_CONTRACT.md` and
`docs/DECISION_SNAPSHOT.md`. P2 implementation was not available in this
workspace during this integration-contract pass, so compatibility with the
actual P2 repository has not been tested.

Run all tests with:

```powershell
.venv\Scripts\python.exe -m pytest
```

## P1 hardening

The P1 engine includes deterministic adversarial-input tests, a local
hidden-evaluation simulation, model artifact integrity checks, and an
executable H+8 migration helper. H+8 removes a selected top-three feature,
rebuilds a new model version, writes new metadata and hashes, and never
overwrites `model_v1`.

Run the synthetic demo with:

```powershell
.venv\Scripts\python.exe scripts\seed_demo.py
```

The demo data contains complete, thin-file, and Unicode-ID examples. The local
benchmark reports mean, median, p95, p99, maximum, and throughput; it is not an
official evaluation result.

P2 still owns persistence, replay storage, and the hash-chain audit. P3 owns
fairness and proxy-leakage analysis. P4 owns public deployment and the actual
watchlist service. P1 does not detect fraud or falsified records and does not
use a hosted LLM or external decision API.

## Local gateway and browser demo

The repository now includes a small gateway and browser client. Start P1 and
P2 first, then set `P1_BASE_URL` and `P2_BASE_URL` and run:

```powershell
$env:P1_BASE_URL = "http://127.0.0.1:8000"
$env:P2_BASE_URL = "http://127.0.0.1:8001"
.venv\Scripts\python.exe -m uvicorn gateway.main:app --host 127.0.0.1 --port 8080
```

Open `http://127.0.0.1:8080`. The browser submits to the gateway; it does not
calculate an approval, score, probability, decision ID, or audit hash.
Production mode fails closed when P1 or P2 cannot be reached.

The complete P1/P2/gateway composition is now in this repository. The P2
implementation is vendored unchanged under `services/p2`, with package-import
updates required by the integrated layout. Start it with:

```powershell
.venv\Scripts\python.exe -m uvicorn services.p2.main:app --host 127.0.0.1 --port 8001
```

The local gateway uses `P1_BASE_URL`, `P2_BASE_URL`, and `GATEWAY_PORT`.
P2 uses `P2_DATABASE_PATH` for SQLite. In Docker Compose, P2 stores its
database in the named `p2_data` volume, so container recreation does not
remove the local database volume.

Docker files are provided for P1, P2, and the gateway. Docker availability and
build/startup remain deployment-dependent and must not be treated as verified
until run on a machine with Docker. PostgreSQL is not implemented; SQLite is
the verified local database backend.
