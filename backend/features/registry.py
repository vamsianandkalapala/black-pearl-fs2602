"""Versioned, explicit registry of features allowed for future model input."""

import hashlib
import json
from datetime import date
from typing import Any, Dict, Optional


FEATURE_REGISTRY_VERSION = "v1"


FEATURE_REGISTRY = [
    {
        "name": "income_to_rent_ratio",
        "source_fields": ["monthly_income", "monthly_rent"],
        "description": "Monthly income divided by monthly rent.",
        "data_type": "float",
        "allowed_model_input": True,
        "status": "non-sensitive financial feature",
        "transformation": "monthly_income / monthly_rent; None when rent is zero or missing",
    },
    {
        "name": "bank_income",
        "source_fields": ["bank_income"],
        "description": "Income reported by a bank source.",
        "data_type": "float",
        "allowed_model_input": True,
        "status": "non-sensitive financial feature",
        "transformation": "copy value",
    },
    {
        "name": "bank_cashflow",
        "source_fields": ["bank_cashflow"],
        "description": "Cashflow value reported by a bank source.",
        "data_type": "float",
        "allowed_model_input": True,
        "status": "non-sensitive financial feature",
        "transformation": "copy value",
    },
    {
        "name": "gig_income",
        "source_fields": ["gig_income"],
        "description": "Income reported from gig or platform work.",
        "data_type": "float",
        "allowed_model_input": True,
        "status": "non-sensitive financial feature",
        "transformation": "copy value",
    },
    {
        "name": "repayment_history",
        "source_fields": ["repayment_history"],
        "description": "Repayment history value.",
        "data_type": "float",
        "allowed_model_input": True,
        "status": "non-sensitive repayment feature",
        "transformation": "copy value",
    },
    {
        "name": "utility_payment_history",
        "source_fields": ["utility_payment_history"],
        "description": "Utility payment history value.",
        "data_type": "float",
        "allowed_model_input": True,
        "status": "non-sensitive payment feature",
        "transformation": "copy value",
    },
    {
        "name": "telecom_payment_history",
        "source_fields": ["telecom_payment_history"],
        "description": "Telecom payment history value.",
        "data_type": "float",
        "allowed_model_input": True,
        "status": "non-sensitive payment feature",
        "transformation": "copy value",
    },
]

FEATURE_PROHIBITIONS = []

ALLOWED_FEATURE_NAMES = tuple(
    feature["name"]
    for feature in FEATURE_REGISTRY
    if feature["allowed_model_input"]
)


def canonical_registry_bytes() -> bytes:
    """Return the registry in a stable byte representation."""
    payload = {
        "version": FEATURE_REGISTRY_VERSION,
        "features": FEATURE_REGISTRY,
        "prohibitions": FEATURE_PROHIBITIONS,
    }
    return json.dumps(
        payload,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=True,
    ).encode("utf-8")


def feature_registry_hash() -> str:
    """Return the SHA-256 identity of the current registry."""
    return hashlib.sha256(canonical_registry_bytes()).hexdigest()


def feature_status_at(feature_name: str, decision_date: str) -> Dict[str, Any]:
    """Return whether a feature is allowed on a given decision date."""
    date.fromisoformat(decision_date)
    definition = next(
        (item for item in FEATURE_REGISTRY if item["name"] == feature_name),
        None,
    )
    if definition is None:
        return {"feature_name": feature_name, "allowed": False, "reason": "unknown feature"}

    applicable = [
        item
        for item in FEATURE_PROHIBITIONS
        if item["feature_name"] == feature_name
        and item["effective_date"] <= decision_date
    ]
    if applicable:
        prohibition = sorted(applicable, key=lambda item: item["effective_date"])[-1]
        return {
            "feature_name": feature_name,
            "allowed": False,
            "reason": prohibition["reason"],
            "effective_date": prohibition["effective_date"],
            "source_change_id": prohibition["source_change_id"],
        }

    return {
        "feature_name": feature_name,
        "allowed": definition["allowed_model_input"],
        "reason": definition["status"],
    }


def allowed_feature_names_at(decision_date: str) -> tuple[str, ...]:
    """Return model-allowed features for a specific decision date."""
    return tuple(
        name
        for name in ALLOWED_FEATURE_NAMES
        if feature_status_at(name, decision_date)["allowed"]
    )
