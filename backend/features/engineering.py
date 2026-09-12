"""Deterministic feature engineering using the explicit feature registry."""

import math
from typing import Any, Dict

from backend.features.registry import FEATURE_REGISTRY


def _copy_value(normalized_applicant: Dict[str, Any], source_field: str) -> Any:
    """Read a registered source field without inventing a missing value."""
    return normalized_applicant.get(source_field)


def _income_to_rent_ratio(normalized_applicant: Dict[str, Any]) -> Any:
    """Calculate a safe income-to-rent ratio."""
    income = normalized_applicant.get("monthly_income")
    rent = normalized_applicant.get("monthly_rent")

    if income is None or rent in (None, 0):
        return None

    ratio = float(income) / float(rent)
    return ratio if math.isfinite(ratio) else None


def build_features(normalized_applicant: Dict[str, Any]) -> Dict[str, Any]:
    """Build only the registered, allowed features in registry order."""
    features = {}

    for definition in FEATURE_REGISTRY:
        if not definition["allowed_model_input"]:
            continue

        feature_name = definition["name"]
        if feature_name == "income_to_rent_ratio":
            features[feature_name] = _income_to_rent_ratio(normalized_applicant)
        else:
            source_field = definition["source_fields"][0]
            features[feature_name] = _copy_value(normalized_applicant, source_field)

    return features
