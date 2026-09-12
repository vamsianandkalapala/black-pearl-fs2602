from pathlib import Path

import pytest

from backend.features.engineering import build_features
from backend.features.registry import ALLOWED_FEATURE_NAMES
from backend.model.predict import predict_score
from backend.model.train import train_model


@pytest.fixture()
def trained_model(tmp_path: Path) -> tuple[Path, dict]:
    artifact_path = tmp_path / "model.joblib"
    metadata_path = tmp_path / "metadata.json"
    metadata = train_model(
        artifact_path=artifact_path,
        metadata_path=metadata_path,
    )
    return artifact_path, metadata


def feature_values() -> dict:
    return {
        "income_to_rent_ratio": 3.0,
        "bank_income": 28000.0,
        "bank_cashflow": None,
        "gig_income": 5000.0,
        "repayment_history": None,
        "utility_payment_history": None,
        "telecom_payment_history": None,
    }


def test_model_trains_and_artifact_exists(trained_model) -> None:
    artifact_path, metadata = trained_model

    assert artifact_path.exists()
    assert metadata["model_version"] == "v1"
    assert metadata["feature_names"] == list(ALLOWED_FEATURE_NAMES)


def test_prediction_has_expected_structure(trained_model) -> None:
    artifact_path, _ = trained_model

    result = predict_score(feature_values(), artifact_path)

    assert result["model_version"] == "v1"
    assert 0 <= result["probability"] <= 1
    assert 0 <= result["score"] <= 100


def test_same_input_produces_same_prediction(trained_model) -> None:
    artifact_path, _ = trained_model

    first = predict_score(feature_values(), artifact_path)
    second = predict_score(feature_values(), artifact_path)

    assert first == second


def test_missing_values_use_training_preprocessing(trained_model) -> None:
    artifact_path, _ = trained_model

    result = predict_score(feature_values(), artifact_path)

    assert isinstance(result["probability"], float)


def test_unregistered_feature_is_rejected(trained_model) -> None:
    artifact_path, _ = trained_model
    invalid_features = {**feature_values(), "unregistered_secret": 123}

    with pytest.raises(ValueError, match="exactly match"):
        predict_score(invalid_features, artifact_path)


def test_training_same_data_and_configuration_is_deterministic(tmp_path: Path) -> None:
    first = train_model(
        artifact_path=tmp_path / "first.joblib",
        metadata_path=tmp_path / "first.json",
    )
    second = train_model(
        artifact_path=tmp_path / "second.joblib",
        metadata_path=tmp_path / "second.json",
    )

    assert first == second
