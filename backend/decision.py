"""Deterministic decision orchestration for the P1 engine."""

from datetime import date
from pathlib import Path
from typing import Any, Dict

from backend.data.normalization import normalize_applicant
from backend.data.quality import assess_data_quality
from backend.data.validation import validate_applicant
from backend.features.engineering import build_features
from backend.features.registry import FEATURE_REGISTRY_VERSION, feature_registry_hash
from backend.model.predict import explain_prediction, predict_score
from backend.model.lineage import load_model_lineage
from backend.rules.engine import evaluate_rulebook, load_rulebook
from backend.snapshot import decision_id, snapshot_hash
from backend.integrity import sha256_file


DECISION_CONTRACT_VERSION = "v1"


def make_decision(request: Any) -> Dict[str, Any]:
    """Run validation, features, model scoring, rules, and explanations."""
    decision_date = date.fromisoformat(request.decision_date).isoformat()
    raw = request.applicant.model_dump()
    if request.watchlist and request.watchlist.status in {"CONFIRMED_MATCH", "UNAVAILABLE"}:
        raise ValueError(
            "Decision cannot proceed with a confirmed or unavailable watchlist result."
        )
    validation = validate_applicant(request.applicant)
    if not validation["is_valid"]:
        raise ValueError("Applicant data failed validation.")

    normalized = normalize_applicant(request.applicant)
    features = build_features(normalized)
    score_result = predict_score(features)
    rulebook = load_rulebook(request.rulebook_version)
    rule_result = evaluate_rulebook(
        rulebook,
        {"score": score_result["score"], "probability": score_result["probability"]},
        decision_date,
    )
    factors = explain_prediction(features, rule_result["action"])
    decision = rule_result["action"]
    requested_language = request.language.lower()
    language_used = "en" if requested_language != "en" else requested_language
    result = {
        "contract_version": DECISION_CONTRACT_VERSION,
        "applicant_id": normalized["applicant_id"],
        "decision": decision,
        "probability": score_result["probability"],
        "score": score_result["score"],
        "model_version": score_result["model_version"],
        "rulebook_version": rulebook["version"],
        "rulebook_sha256": sha256_file(
            Path(__file__).resolve().parents[1]
            / "rules"
            / f"{rulebook['version']}.json"
        ),
        "rule_id": rule_result["rule_id"],
        "feature_registry_version": FEATURE_REGISTRY_VERSION,
        "feature_registry_hash": feature_registry_hash(),
        "decision_date": decision_date,
        "decision_timestamp": f"{decision_date}T00:00:00Z",
        "contributing_factors": factors,
        "adverse_action": factors if decision == "DECLINED" else [],
        "data_quality": assess_data_quality(raw),
        "watchlist": (request.watchlist.model_dump() if request.watchlist else {
            "status": "NOT_SCREENED",
            "matched": False,
            "match_type": None,
            "confidence": None,
            "reason": "Watchlist screening is owned by the integration component.",
        }),
        "language_requested": request.language,
        "language_used": language_used,
        "normalized_input": normalized,
        "feature_vector": features,
        "decision_serialization_version": "v1",
    }
    lineage = load_model_lineage(score_result["model_version"])
    result["model_artifact_sha256"] = lineage["model_artifact_sha256"]
    result["model_metadata_sha256"] = lineage["metadata_content_sha256"]
    result["snapshot_hash"] = snapshot_hash(result)
    result["decision_id"] = decision_id(result)
    return result
