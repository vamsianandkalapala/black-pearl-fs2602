"""LOCAL BENCHMARK — NOT SEALED EVALUATION."""

import json
import platform
import statistics
import sys
import time
from pathlib import Path

from fastapi.testclient import TestClient

import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from backend.api.main import app


PAYLOAD = {
    "applicant": {
        "applicant_id": "benchmark",
        "monthly_income": 2500,
        "monthly_rent": 1000,
        "bank_income": 34000,
        "bank_cashflow": 30000,
        "gig_income": 7000,
        "repayment_history": 7,
        "utility_payment_history": 9,
        "telecom_payment_history": 8,
    },
    "rulebook_version": "v1",
    "decision_date": "2026-09-12",
    "language": "en",
}


def main() -> None:
    count = int(sys.argv[1]) if len(sys.argv) > 1 else 1000
    if count < 1:
        raise ValueError("Benchmark count must be positive.")
    client = TestClient(app)
    latencies = []
    for _ in range(count):
        started = time.perf_counter()
        response = client.post("/decision", json=PAYLOAD)
        response.raise_for_status()
        latencies.append((time.perf_counter() - started) * 1000)
    ordered = sorted(latencies)
    p95 = ordered[int(count * 0.95) - 1]
    p99 = ordered[int(count * 0.99) - 1]
    print(json.dumps({
        "label": "LOCAL BENCHMARK — NOT SEALED EVALUATION",
        "environment": {"python": platform.python_version(), "platform": platform.platform()},
        "decisions": count,
        "failures": 0,
        "mean_ms": round(statistics.mean(latencies), 3),
        "median_ms": round(statistics.median(latencies), 3),
        "p95_ms": round(p95, 3),
        "p99_ms": round(p99, 3),
        "max_ms": round(max(latencies), 3),
        "throughput_per_second": round(count / (sum(latencies) / 1000), 3),
    }, indent=2))


if __name__ == "__main__":
    main()
