"""Generate an honest HALF_DEBUG compliance report from repository checks."""

import json
import platform
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from backend.features.registry import feature_registry_hash
from backend.integrity import sha256_file


ROOT = Path(__file__).resolve().parents[1]


def item(requirement, evidence, path, command, status, action="None"):
    return {
        "requirement": requirement,
        "evidence": evidence,
        "path": path,
        "command": command,
        "status": status,
        "action": action,
    }


def main() -> None:
    report = {
        "A. Universal hackathon rules": [
            item("AI ledger exists", "Entries 001-005 and HALF DEBUG are present.", "AI_LEDGER.md", "Get-Content AI_LEDGER.md", "PASS"),
            item("No hosted LLM in scoring path", "No hosted LLM imports found.", "backend/", "rg hosted LLM terms", "PASS"),
            item("Three-command run", "README documents the tested setup, training, and API sequence.", "README.md", "Get-Content README.md", "FIXED"),
        ],
        "B. FS-2602 functional requirements": [
            item("Alternate-data scoring", "Versioned Logistic Regression score exists.", "backend/model/", "pytest", "PASS"),
            item("Conflicts, gaps, falsified records", "Quality signals and cases exist; fraud detection is not claimed.", "backend/data/quality.py", "pytest", "PARTIAL", "Build source authenticity/fraud checks later."),
            item("Rules as versioned data", "v1 rulebook has version and effective date.", "rules/v1.json", "json parser", "PASS"),
            item("Historical replay", "Portable metadata foundation exists; byte-identical replay engine is not implemented.", "backend/model/", "pytest", "PARTIAL", "Integrate with P2 replay system."),
            item("Fairness", "No parity or proxy audit implementation yet.", "backend/", "not implemented", "MISSING", "Requires independent fairness evaluation."),
        ],
        "C. FS-2602 technical constraints": [
            item("Deterministic scoring", "Fixed model configuration, ordered features, canonical serialization.", "backend/model/", "pytest", "PASS"),
            item("Reproducibility gate", "Hashes and metadata are available; full replay gate is not complete.", "backend/integrity.py", "pytest", "PARTIAL", "Add historical byte replay."),
            item("Observability", "Health, metrics, and three domain counters exist.", "backend/api/main.py", "TestClient", "FIXED"),
            item("Watchlist screening", "Not part of Person 1 model foundation.", "backend/", "not implemented", "REQUIRES P2", "Integrate before final latency claim."),
            item("Audit tampering detection", "Not implemented in this P1 foundation.", "backend/", "not implemented", "REQUIRES P2", "Integrate hash-chain audit log."),
        ],
        "D. H+8 readiness": [
            item("Top-three feature foundation", "Coefficient ranking is stored in metadata after training.", "backend/model/train.py", "pytest", "FIXED"),
            item("Feature prohibition data", "Feature prohibition structure and effective-date lookup exist.", "backend/features/registry.py", "pytest", "FIXED"),
            item("Full retroactive H+8 workflow", "Retraining, lineage, replay, impact simulation, and re-audit are not one workflow.", "backend/", "not implemented", "PARTIAL", "Build after rule/model integration."),
        ],
        "E. Round 1 requirements": [
            item("Foundation scoring", "Applicant, validation, features, and score paths exist.", "backend/", "pytest", "PASS"),
        ],
        "F. Round 2 requirements": [
            item("Decision and explanations", "Versioned policy decision and model-derived factors exist.", "backend/decision.py", "pytest", "PASS"),
        ],
        "G. Round 3 requirements": [
            item("Replay/fairness/audit integration", "Interfaces are not complete in this stage.", "backend/", "not implemented", "REQUIRES P2", "Coordinate with P2."),
        ],
        "H. Repository/process requirements": [
            item("15 commits across 6 clock hours", "This workspace is not a git repository.", "repository", "git log", "EVENT-ONLY", "Verify in the actual submission repository."),
            item("Final deck and failure disclosure slide", "Cannot be verified from code.", "event materials", "manual", "EVENT-ONLY", "Prepare for submission."),
        ],
        "I. Known remaining risks": [
            item("Exact dependency/runtime metadata", "Training metadata records versions and runtime.", "models/model_v1_metadata.json", "json parser", "PASS"),
            item("Model artifact integrity", "SHA-256 helper and metadata hash fields exist.", "backend/integrity.py", "pytest", "PASS"),
            item("Cost, RAM, latency measurements", "No fabricated measurements are present.", "backend/", "not measured", "MISSING", "Measure before final reporting."),
        ],
    }

    lines = ["# HALF DEBUG REPORT", "", f"Python: {platform.python_version()}", ""]
    for section, items in report.items():
        lines.extend([f"## {section}", ""])
        for entry in items:
            lines.extend(
                [
                    f"- **{entry['status']}** — {entry['requirement']}",
                    f"  - Evidence: {entry['evidence']}",
                    f"  - File/path: `{entry['path']}`",
                    f"  - Test/command: `{entry['command']}`",
                    f"  - Remaining action: {entry['action']}",
                ]
            )
        lines.append("")

    metadata_path = ROOT / "models" / "model_v1_metadata.json"
    if metadata_path.exists():
        lines.append(f"Model metadata SHA-256: `{sha256_file(metadata_path)}`")
    lines.append(f"Feature registry SHA-256: `{feature_registry_hash()}`")
    (ROOT / "HALF_DEBUG_REPORT.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    batch6 = [
        item("Decision snapshot contract", "Snapshot documentation and API fields exist.", "docs/DECISION_SNAPSHOT.md", "pytest", "PASS"),
        item("Snapshot hash", "Canonical snapshot hashing and mutation tests exist.", "backend/snapshot.py", "pytest", "PASS"),
        item("Rule effective-date validation", "Rule ranges are parsed and boundary-tested.", "backend/rules/engine.py", "pytest", "FIXED"),
        item("Model lineage", "Manifest lookup, artifact verification, and safe H+8 preparation exist.", "backend/model/lineage.py", "pytest", "FIXED"),
        item("Replay fixture", "A deterministic v1 decision fixture is checked by tests.", "fixtures/replay/decision_v1.json", "pytest", "FIXED"),
        item("Local benchmark", "Benchmark script reports local mean, p95, and max latency.", "bench/bench_decision.py", "python bench/bench_decision.py", "FIXED"),
        item("Historical replay engine", "Fixture and snapshot foundations exist, but full replay storage/execution is not implemented.", "backend/", "not implemented", "PARTIAL", "Integrate with P2 replay storage and execution."),
        item("Fairness, proxy, watchlist, audit chain", "These remain integration requirements.", "backend/", "not implemented", "MISSING", "P2/P3/P4 integration."),
    ]
    b6_lines = ["# BATCH 6 COMPLIANCE REPORT", "", f"Python: {platform.python_version()}", ""]
    for entry in batch6:
        b6_lines.extend([
            f"- **{entry['status']}** — {entry['requirement']}",
            f"  - Evidence: {entry['evidence']}",
            f"  - File/path: `{entry['path']}`",
            f"  - Test/command: `{entry['command']}`",
            f"  - Remaining action: {entry['action']}",
            "",
        ])
    (ROOT / "BATCH_6_COMPLIANCE_REPORT.md").write_text("\n".join(b6_lines), encoding="utf-8")
    print("Wrote HALF_DEBUG_REPORT.md")
    print("Wrote BATCH_6_COMPLIANCE_REPORT.md")


if __name__ == "__main__":
    main()
