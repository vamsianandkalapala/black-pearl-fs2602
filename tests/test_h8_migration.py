from pathlib import Path

from backend.model.lineage import execute_h8_transition
from backend.model.predict import predict_score_for_model
from backend.model.train import DEFAULT_DATA_PATH


def test_h8_retraining_is_deterministic_and_preserves_v1(tmp_path: Path):
    first = execute_h8_transition("repayment_history", tmp_path / "first")
    second = execute_h8_transition("repayment_history", tmp_path / "second")

    assert first["new_model_version"] == "v2"
    assert "repayment_history" not in first["metadata"]["feature_names"]
    assert first["model_artifact_sha256"] == second["model_artifact_sha256"]
    assert first["metadata"]["feature_names"] == second["metadata"]["feature_names"]
    assert Path("models/model_v1.joblib").exists()
    assert first["metadata"]["training_data_identifier"] == str(
        DEFAULT_DATA_PATH.resolve().relative_to(Path.cwd())
    )


def test_h8_model_scores_only_its_registered_feature_set(tmp_path: Path):
    result = execute_h8_transition("utility_payment_history", tmp_path)
    features = {
        name: 1.0
        for name in result["metadata"]["feature_names"]
    }
    score = predict_score_for_model(
        features,
        tmp_path / "model_v2.joblib",
    )
    assert score["model_version"] == "v2"
