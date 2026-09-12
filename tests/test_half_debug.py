import json
from pathlib import Path

import pytest

from backend.api.main import app
from backend.data.quality import assess_data_quality
from backend.features.registry import (
    FEATURE_REGISTRY_VERSION,
    feature_registry_hash,
    feature_status_at,
)
from backend.integrity import sha256_file, verify_sha256
from backend.model.registry import register_model_version
from backend.model.serialization import serialize_score
from fastapi.testclient import TestClient


def test_registry_hash_and_feature_status_are_deterministic() -> None:
    assert feature_registry_hash() == feature_registry_hash()
    assert FEATURE_REGISTRY_VERSION == "v1"
    assert feature_status_at("bank_income", "2026-09-12")["allowed"] is True
    assert feature_status_at("unknown", "2026-09-12")["allowed"] is False


def test_serialized_score_is_byte_identical() -> None:
    result = {"model_version": "v1", "probability": 0.5, "score": 50}

    assert serialize_score(result) == serialize_score(result)
    assert serialize_score(result) == b'{"model_version":"v1","probability":0.5,"score":50}\n'


def test_integrity_hash_detects_modified_file(tmp_path: Path) -> None:
    file_path = tmp_path / "artifact.bin"
    file_path.write_bytes(b"original")
    original_hash = sha256_file(file_path)

    assert verify_sha256(file_path, original_hash) is True
    file_path.write_bytes(b"modified")
    assert verify_sha256(file_path, original_hash) is False


def test_model_registry_rejects_version_overwrite(tmp_path: Path) -> None:
    manifest_path = tmp_path / "manifest.json"
    metadata = {"model_version": "v1", "model_artifact_sha256": "abc"}

    register_model_version(metadata, manifest_path)

    with pytest.raises(FileExistsError):
        register_model_version(metadata, manifest_path)


def test_model_artifact_is_not_overwritten_by_training(tmp_path: Path) -> None:
    from backend.model.train import train_model

    artifact_path = tmp_path / "model.joblib"
    metadata_path = tmp_path / "metadata.json"
    train_model(artifact_path=artifact_path, metadata_path=metadata_path)

    with pytest.raises(FileExistsError):
        train_model(artifact_path=artifact_path, metadata_path=metadata_path)


def test_quality_signals_do_not_claim_fraud_detection() -> None:
    result = assess_data_quality(
        {
            "monthly_income": 2_000_000,
            "bank_income": 2_000_000,
            "gig_income": 2_000_000,
        }
    )

    assert result["quality_status"] == "flagged"
    assert result["not_fraud_detection"] is True


def test_quality_dataset_cases_are_surfaceable() -> None:
    cases = json.loads(
        Path("data/raw/data_quality_cases.json").read_text(encoding="utf-8")
    )
    results = {
        case["case_id"]: assess_data_quality(case["data"])
        for case in cases
    }

    assert results["normal"]["quality_status"] == "no_quality_flags"
    assert results["conflicting_sources"]["quality_status"] == "flagged"
    assert results["suspicious_plausible_value"]["quality_status"] == "flagged"
    assert results["malformed_value"]["quality_status"] == "flagged"


def test_metrics_endpoint_exposes_domain_metrics() -> None:
    response = TestClient(app).get("/metrics")

    assert response.status_code == 200
    assert "decision_validation_requests_total" in response.text
    assert "decision_feature_generation_requests_total" in response.text
    assert "decision_score_requests_total" in response.text


def test_training_metadata_has_top_three_features() -> None:
    metadata = json.loads(
        Path("models/model_v1_metadata.json").read_text(encoding="utf-8")
    )

    assert len(metadata.get("top_three_features", [])) == 3
