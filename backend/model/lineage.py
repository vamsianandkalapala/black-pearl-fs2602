"""Safe model-lineage and future H+8 preparation helpers."""

import json
import hashlib
from pathlib import Path
from typing import Any, Dict

from backend.features.registry import ALLOWED_FEATURE_NAMES
from backend.integrity import sha256_file
from backend.model.train import DEFAULT_ARTIFACT_PATH, DEFAULT_DATA_PATH, train_model
from backend.model.registry import register_model_version


PROJECT_ROOT = Path(__file__).resolve().parents[2]
MANIFEST_PATH = PROJECT_ROOT / "models" / "manifest.json"
METADATA_PATH = PROJECT_ROOT / "models" / "model_v1_metadata.json"


def load_model_lineage(
    model_version: str,
    manifest_path: Path = MANIFEST_PATH,
) -> Dict[str, Any]:
    """Return exact manifest metadata for one model version."""
    manifest = json.loads(Path(manifest_path).read_text(encoding="utf-8"))
    for model in manifest.get("models", []):
        if model.get("model_version") == model_version:
            return dict(model)
    raise FileNotFoundError(f"Unknown model version: {model_version}")


def prepare_h8_transition(
    prohibited_feature: str,
    model_version: str = "v1",
    metadata_path: Path = METADATA_PATH,
) -> Dict[str, Any]:
    """Prepare, but do not execute, a deterministic next-model transition."""
    metadata = json.loads(Path(metadata_path).read_text(encoding="utf-8"))
    top_three = [
        item["feature_name"] for item in metadata.get("top_three_features", [])
    ]
    if prohibited_feature not in top_three:
        raise ValueError("H+8 feature must be one of the model top-three features.")
    allowed_features = [
        name for name in ALLOWED_FEATURE_NAMES if name != prohibited_feature
    ]
    next_number = int(model_version.lstrip("v")) + 1
    return {
        "parent_model_version": model_version,
        "new_model_version": f"v{next_number}",
        "prohibited_feature": prohibited_feature,
        "allowed_features": allowed_features,
        "training_configuration": {
            "feature_names": allowed_features,
            "change_reason": f"H+8 prohibition of {prohibited_feature}",
            "overwrite_existing_versions": False,
        },
        "artifact_path": str(DEFAULT_ARTIFACT_PATH.parent / f"model_v{next_number}.joblib"),
    }


def execute_h8_transition(
    prohibited_feature: str,
    output_directory: Path,
    model_version: str = "v1",
    data_path: Path = DEFAULT_DATA_PATH,
) -> Dict[str, Any]:
    """Retrain a new model without one top-three feature, preserving v1."""
    transition = prepare_h8_transition(prohibited_feature, model_version)
    output_directory = Path(output_directory)
    artifact_path = output_directory / f"model_{transition['new_model_version']}.joblib"
    metadata_path = output_directory / f"model_{transition['new_model_version']}_metadata.json"
    manifest_path = output_directory / "manifest.json"
    registry_identity = hashlib.sha256(
        json.dumps(
            {
                "version": "h8-" + transition["new_model_version"],
                "features": transition["allowed_features"],
                "prohibited_feature": prohibited_feature,
            },
            sort_keys=True,
            separators=(",", ":"),
        ).encode("utf-8")
    ).hexdigest()
    metadata = train_model(
        data_path=data_path,
        artifact_path=artifact_path,
        metadata_path=metadata_path,
        model_version=transition["new_model_version"],
        parent_model_version=model_version,
        change_reason=transition["training_configuration"]["change_reason"],
        feature_names=transition["allowed_features"],
        feature_registry_version="h8-" + transition["new_model_version"],
        feature_registry_identity=registry_identity,
    )
    try:
        artifact_reference = str(artifact_path.relative_to(PROJECT_ROOT))
        metadata_reference = str(metadata_path.relative_to(PROJECT_ROOT))
    except ValueError:
        artifact_reference = str(artifact_path.resolve())
        metadata_reference = str(metadata_path.resolve())
    manifest_entry = {
        "artifact_path": artifact_reference,
        "metadata_path": metadata_reference,
        "model_version": metadata["model_version"],
        "model_artifact_sha256": metadata["model_artifact_sha256"],
        "metadata_content_sha256": metadata["metadata_content_sha256"],
        "feature_registry_sha256": metadata["feature_registry_sha256"],
        "training_data_sha256": metadata["training_data_sha256"],
        "parent_model_version": model_version,
        "change_reason": metadata["change_reason"],
        "prohibited_feature": prohibited_feature,
    }
    register_model_version(manifest_entry, manifest_path)
    return {
        **transition,
        "metadata": metadata,
        "manifest_entry": manifest_entry,
        "model_artifact_sha256": metadata["model_artifact_sha256"],
    }


def verify_model_artifact(model_version: str = "v1") -> bool:
    """Verify the currently registered artifact hash for a model version."""
    lineage = load_model_lineage(model_version)
    artifact_path = Path(lineage["artifact_path"])
    if not artifact_path.is_absolute():
        artifact_path = PROJECT_ROOT / artifact_path
    return sha256_file(artifact_path) == lineage["model_artifact_sha256"]
