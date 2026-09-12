"""Train and save the deterministic prototype model."""

import csv
import hashlib
import json
import platform
import subprocess
import sys
from importlib.metadata import PackageNotFoundError, version as package_version
from pathlib import Path
from typing import Dict, List, Sequence

import joblib
from sklearn.impute import SimpleImputer
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler

from backend.features.registry import ALLOWED_FEATURE_NAMES
from backend.features.registry import FEATURE_REGISTRY_VERSION, feature_registry_hash
from backend.integrity import sha256_file


MODEL_VERSION = "v1"
PROJECT_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_DATA_PATH = PROJECT_ROOT / "data" / "raw" / "training_data.csv"
DEFAULT_ARTIFACT_PATH = PROJECT_ROOT / "models" / "model_v1.joblib"
DEFAULT_METADATA_PATH = PROJECT_ROOT / "models" / "model_v1_metadata.json"


def _load_training_data(
    data_path: Path,
    feature_names: Sequence[str] = ALLOWED_FEATURE_NAMES,
) -> tuple[List[Dict[str, float]], List[int]]:
    """Load numeric feature rows and binary repayment targets from CSV."""
    with data_path.open("r", newline="", encoding="utf-8") as data_file:
        reader = csv.DictReader(data_file)
        expected_columns = list(feature_names) + ["target"]
        if reader.fieldnames is None or any(
            name not in reader.fieldnames for name in expected_columns
        ):
            raise ValueError(
                f"Training columns must include {expected_columns}, "
                f"but were {reader.fieldnames}."
            )

        rows = []
        targets = []
        for row in reader:
            rows.append(
                {
                    name: float(row[name]) if row[name] != "" else None
                    for name in feature_names
                }
            )
            targets.append(int(row["target"]))

    return rows, targets


def train_model(
    data_path: Path = DEFAULT_DATA_PATH,
    artifact_path: Path = DEFAULT_ARTIFACT_PATH,
    metadata_path: Path = DEFAULT_METADATA_PATH,
    model_version: str = MODEL_VERSION,
    parent_model_version: str = "",
    change_reason: str = "initial model",
    feature_names: Sequence[str] = ALLOWED_FEATURE_NAMES,
    feature_registry_version: str = FEATURE_REGISTRY_VERSION,
    feature_registry_identity: str | None = None,
) -> dict:
    """Train Logistic Regression and save its model and human-readable metadata."""
    data_path = Path(data_path)
    artifact_path = Path(artifact_path)
    metadata_path = Path(metadata_path)
    if artifact_path.exists():
        raise FileExistsError(
            f"Refusing to overwrite existing model artifact: {artifact_path}"
        )

    feature_names = list(feature_names)
    if not feature_names or len(set(feature_names)) != len(feature_names):
        raise ValueError("Training requires a non-empty, unique feature list.")
    unknown_features = set(feature_names) - set(ALLOWED_FEATURE_NAMES)
    if unknown_features:
        raise ValueError(f"Training features are not registered: {sorted(unknown_features)}")
    rows, targets = _load_training_data(data_path, feature_names)
    training_matrix = [[row[name] for name in feature_names] for row in rows]

    pipeline = Pipeline(
        steps=[
            ("imputer", SimpleImputer(strategy="median")),
            ("scaler", StandardScaler()),
            (
                "model",
                LogisticRegression(
                    random_state=42,
                    solver="lbfgs",
                    max_iter=1000,
                ),
            ),
        ]
    )
    pipeline.fit(training_matrix, targets)

    try:
        git_commit = subprocess.check_output(
            ["git", "rev-parse", "HEAD"],
            cwd=PROJECT_ROOT,
            text=True,
            stderr=subprocess.DEVNULL,
        ).strip()
    except (OSError, subprocess.CalledProcessError):
        git_commit = "unavailable"

    dependencies = {}
    for package_name in ("fastapi", "pydantic", "numpy", "scipy", "scikit-learn", "joblib"):
        try:
            dependencies[package_name] = package_version(package_name)
        except PackageNotFoundError:
            dependencies[package_name] = "unavailable"

    metadata = {
        "model_version": model_version,
        "model_type": "LogisticRegression",
        "feature_names": feature_names,
        "feature_registry_version": feature_registry_version,
        "feature_registry_sha256": feature_registry_identity or feature_registry_hash(),
        "preprocessing": "median imputation fitted on training data, then standard scaling",
        "training_data_identifier": str(data_path.resolve().relative_to(PROJECT_ROOT)),
        "training_data_sha256": sha256_file(data_path),
        "parent_model_version": parent_model_version,
        "change_reason": change_reason,
        "training_configuration": {
            "random_state": 42,
            "solver": "lbfgs",
            "max_iter": 1000,
        },
        "target": "historical repayment outcome; 1 means positive outcome",
        "data_status": "SYNTHETIC prototype data; not real applicant performance data",
        "python_version": platform.python_version(),
        "platform": platform.platform(),
        "dependencies": dependencies,
        "git_commit": git_commit,
        "creation_timestamp": data_path.stat().st_mtime_ns,
        "top_three_features": [
            {
                "feature_name": feature_name,
                "importance": abs(float(coefficient)),
                "importance_method": "absolute standardized Logistic Regression coefficient",
            }
            for feature_name, coefficient in sorted(
                zip(feature_names, pipeline.named_steps["model"].coef_[0]),
                key=lambda pair: (-abs(float(pair[1])), feature_names.index(pair[0])),
            )[:3]
        ],
    }

    artifact_path.parent.mkdir(parents=True, exist_ok=True)
    metadata_path.parent.mkdir(parents=True, exist_ok=True)
    joblib.dump(
        {
            "model_version": model_version,
            "feature_names": feature_names,
            "pipeline": pipeline,
        },
        artifact_path,
    )
    metadata["model_artifact_sha256"] = sha256_file(artifact_path)
    metadata_without_hash = json.dumps(
        metadata,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")
    metadata["metadata_content_sha256"] = hashlib.sha256(
        metadata_without_hash
    ).hexdigest()
    metadata_path.write_text(json.dumps(metadata, indent=2) + "\n", encoding="utf-8")

    return metadata
