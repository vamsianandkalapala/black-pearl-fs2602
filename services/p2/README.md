# P2: Compliance & Reproducibility Engine

**Team:** BLACK PEARL  
**FinTech Sprint '26** | **Problem:** FS-2602 — Reproducible Credit Decisioning for Thin-File Borrowers  
**Core Principle:** `SCORE + PROVE`

---

## 🎯 Purpose

The **Compliance & Reproducibility Engine** persists every credit decision made
by P1 so it can be proven, audited, replayed, and checked for bias:
- **Decision Snapshots & Audit Records:** Immutable records of inputs, features, model versions, rulebooks, and outputs.
- **Hash Chain & Tamper Detection:** Cryptographic proof that decision history has not been altered.
- **Historical Decision Replay:** Exact deterministic re-execution of historical decisions under original conditions.
- **Fairness Audit & Proxy-Leakage Testing:** Ensuring compliance with fair lending standards and detecting hidden bias proxies.

---

## 📁 Project Structure

```text
p2_compliance/
├── main.py           # FastAPI application entry point with /healthz endpoint
├── database.py       # Persistent SQLite schema and snapshot storage
├── schemas.py        # Complete P1 snapshot contract
├── audit.py          # Durable audit-chain recording and verification
├── hashing.py        # Canonical JSON and SHA-256 helpers
├── replay.py         # Historical replay through P1 HTTP/JSON
├── fairness.py       # Honest prohibited-input limitation check
├── proxy.py          # Explicitly limited proxy-analysis response
├── versioning.py     # P1 version availability metadata
├── requirements.txt  # Python package dependencies
└── README.md         # Project documentation and quickstart guide
```

---

## 🚀 Quickstart Guide

### 1. Install Dependencies

Open PowerShell and navigate to the project directory:

```powershell
cd <repository-root>
```

From the integrated repository, install the shared environment dependencies:

```powershell
pip install -r requirements.txt
```

The integrated service is started with:

```powershell
python -m uvicorn services.p2.main:app --host 127.0.0.1 --port 8001
```

`P2_DATABASE_PATH` controls the SQLite file and defaults to
`p2_compliance.db`. `P1_BASE_URL` controls the P1 endpoint used for replay.
For Docker, these values are set to service URLs and the SQLite path is
mounted under `/data`.

### 2. Run the Application

Start the local development server with Uvicorn:

```powershell
python -m uvicorn services.p2.main:app --host 127.0.0.1 --port 8001
```

The server will start listening at `http://127.0.0.1:8000`.

### 3. Test the `/healthz` Endpoint

You can test the endpoint in three easy ways:

#### Option A: Web Browser
Open your browser and navigate to:
[http://127.0.0.1:8000/healthz](http://127.0.0.1:8000/healthz)

#### Option B: PowerShell
Run this in PowerShell:
```powershell
Invoke-RestMethod -Uri "http://127.0.0.1:8000/healthz"
```

#### Option C: cURL
```powershell
curl http://127.0.0.1:8000/healthz
```

#### Expected Output
```json
{
  "status": "ok",
  "service": "P2 Compliance Engine"
}
```

Interactive API documentation will also be automatically available at:
- **Swagger UI:** [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)
- **ReDoc:** [http://127.0.0.1:8000/redoc](http://127.0.0.1:8000/redoc)

## P1 integration

P1 remains authoritative for score, probability, decision, factors, versions,
and snapshot identity. Submit the complete P1 `POST /decision` JSON response to
`POST /snapshot` either directly or in this envelope:

```json
{
  "snapshot": { "decision_id": "...", "snapshot_hash": "...", "...": "P1 response" },
  "request": { "applicant": { "...": "original request" }, "rulebook_version": "v1", "decision_date": "2026-09-12" }
}
```

The database path is controlled by `P2_DATABASE_PATH` and defaults to
`p2_compliance.db`. SQLite is persistent and initialized idempotently; it is
appropriate for local development. A production deployment should place the
database on persistent storage or replace the small database module with the
team's managed database adapter.

Replay uses `P1_BASE_URL` (default `http://127.0.0.1:8000`) and calls the real
P1 `/decision` endpoint. It rejects unavailable historical model versions
instead of silently substituting the current model. `/audit/verify` checks the
stored sequence, previous hashes, current hashes, record count, and persisted
chain head.
