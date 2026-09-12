"""Generate deterministic model probabilities and prototype scores."""

import json
import math
from pathlib import Path
from typing import Any, Dict

import joblib

from backend.features.registry import ALLOWED_FEATURE_NAMES
from backend.model.train import DEFAULT_ARTIFACT_PATH, MODEL_VERSION
from backend.model.serialization import serialize_score
from backend.integrity import sha256_file


def _ordered_values(features: Dict[str, Any]) -> list:
    """Validate feature names and arrange values in canonical registry order."""
    expected = set(ALLOWED_FEATURE_NAMES)
    actual = set(features)
    if actual != expected:
        raise ValueError(
            f"Features must exactly match {list(ALLOWED_FEATURE_NAMES)}; "
            f"received {list(features)}."
        )
    values = [features[name] for name in ALLOWED_FEATURE_NAMES]
    for value in values:
        if value is not None and (
            isinstance(value, bool)
            or not isinstance(value, (int, float))
            or not math.isfinite(float(value))
        ):
            raise ValueError("Model features must be finite numeric values or null.")
    return values


def predict_score(
    features: Dict[str, Any],
    artifact_path: Path = DEFAULT_ARTIFACT_PATH,
) -> dict:
    """Return model version, probability, and prototype score."""
    values = _ordered_values(features)
    artifact_path = Path(artifact_path)
    bundle = joblib.load(artifact_path)
    if bundle["feature_names"] != list(ALLOWED_FEATURE_NAMES):
        raise ValueError("Model artifact feature order does not match the registry.")
    if bundle.get("model_version") != MODEL_VERSION:
        raise ValueError("Model artifact version does not match the supported model.")
    if artifact_path.resolve() == DEFAULT_ARTIFACT_PATH.resolve():
        manifest = json.loads(
            (DEFAULT_ARTIFACT_PATH.parent / "manifest.json").read_text(encoding="utf-8")
        )
        registered = next(
            (item for item in manifest["models"] if item["model_version"] == MODEL_VERSION),
            None,
        )
        if registered is None or sha256_file(artifact_path) != registered["model_artifact_sha256"]:
            raise ValueError("Model artifact integrity check failed.")

    probability = float(bundle["pipeline"].predict_proba([values])[0][1])
    if not math.isfinite(probability) or not 0.0 <= probability <= 1.0:
        raise ValueError("Model returned an invalid probability.")
    return {
        "model_version": bundle.get("model_version", MODEL_VERSION),
        "probability": probability,
        "score": int(round(probability * 100)),
    }


def predict_score_for_model(features: Dict[str, Any], artifact_path: Path) -> dict:
    """Score a registered artifact using that artifact's own feature contract."""
    artifact_path = Path(artifact_path)
    bundle = joblib.load(artifact_path)
    feature_names = bundle.get("feature_names")
    if not isinstance(feature_names, list) or not feature_names:
        raise ValueError("Model artifact has no valid feature contract.")
    if set(features) != set(feature_names):
        raise ValueError("Features do not match the model artifact contract.")
    values = []
    for name in feature_names:
        value = features[name]
        if value is not None and (
            isinstance(value, bool)
            or not isinstance(value, (int, float))
            or not math.isfinite(float(value))
        ):
            raise ValueError("Model features must be finite numeric values or null.")
        values.append(value)
    probability = float(bundle["pipeline"].predict_proba([values])[0][1])
    if not math.isfinite(probability) or not 0.0 <= probability <= 1.0:
        raise ValueError("Model returned an invalid probability.")
    return {
        "model_version": bundle["model_version"],
        "probability": probability,
        "score": int(round(probability * 100)),
    }


def serialize_prediction(result: Dict[str, Any]) -> bytes:
    """Return the canonical byte representation of a prediction."""
    return serialize_score(result)


FEATURE_LABELS = {
    "income_to_rent_ratio": "Monthly income relative to rent",
    "bank_income": "Bank-reported income",
    "bank_cashflow": "Bank cashflow",
    "gig_income": "Gig income",
    "repayment_history": "Repayment history",
    "utility_payment_history": "Utility payment history",
    "telecom_payment_history": "Telecom payment history",
}


def explain_prediction(features: Dict[str, Any], decision: str) -> list[dict]:
    """Rank model-derived feature contributions for a decision explanation."""
    values = _ordered_values(features)
    bundle = joblib.load(Path(DEFAULT_ARTIFACT_PATH))
    pipeline = bundle["pipeline"]
    imputer = pipeline.named_steps["imputer"]
    scaler = pipeline.named_steps["scaler"]
    model = pipeline.named_steps["model"]
    imputed = imputer.transform([values])[0]
    scaled = scaler.transform([imputed])[0]
    contributions = []
    for index, feature_name in enumerate(ALLOWED_FEATURE_NAMES):
        if values[index] is None:
            continue
        contribution = float(model.coef_[0][index] * scaled[index])
        if abs(contribution) < 1e-12:
            continue
        direction = "supports_approval" if contribution > 0 else "reduces_approval"
        label = FEATURE_LABELS[feature_name]
        if contribution < 0:
            reason = f"{label} was low relative to the model pattern, which reduced estimated repayment capacity."
        else:
            reason = f"{label} supported the model's estimated repayment capacity."
        contributions.append(
            {
                "feature_name": feature_name,
                "contribution": round(contribution, 12),
                "direction": direction,
                "reason": reason,
                "actionability": "review_source_data",
            }
        )
    contributions.sort(key=lambda item: (-abs(item["contribution"]), list(ALLOWED_FEATURE_NAMES).index(item["feature_name"])))
    for rank, factor in enumerate(contributions[:4], start=1):
        factor["rank"] = rank
    return contributions[:4]
