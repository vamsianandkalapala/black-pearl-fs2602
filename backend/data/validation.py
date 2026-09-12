"""Deterministic validation helpers for applicant data."""

import math
from typing import Any, Dict, Mapping

from backend.schemas.applicant import Applicant


REQUIRED_FIELDS = ("applicant_id", "monthly_income", "monthly_rent")
OPTIONAL_SOURCE_FIELDS = (
    "bank_income",
    "bank_cashflow",
    "utility_payment_history",
    "telecom_payment_history",
    "gig_income",
    "repayment_history",
)
NUMERIC_FIELDS = (
    "monthly_income",
    "monthly_rent",
    "bank_income",
    "utility_payment_history",
    "telecom_payment_history",
    "bank_cashflow",
    "gig_income",
    "repayment_history",
)
MONETARY_FIELDS = (
    "monthly_income",
    "monthly_rent",
    "bank_income",
    "bank_cashflow",
    "gig_income",
)


def _applicant_values(applicant: Any) -> Dict[str, Any]:
    """Convert a Pydantic model or mapping into a plain dictionary."""
    if isinstance(applicant, Applicant):
        return applicant.model_dump()
    if isinstance(applicant, Mapping):
        return dict(applicant)
    return {}


def validate_applicant(applicant: Any) -> Dict[str, Any]:
    """Return errors, warnings, missing data, and conflicts without deciding."""
    values = _applicant_values(applicant)
    errors = []
    warnings = []
    missing_fields = []
    missing_sources = []
    conflicts = []

    for field_name in REQUIRED_FIELDS:
        value = values.get(field_name)
        if value is None:
            missing_fields.append(field_name)
            errors.append(f"Missing required field: {field_name}")
        elif field_name == "applicant_id" and (
            not isinstance(value, str) or not value.strip()
        ):
            errors.append("Applicant ID must not be blank.")

    for field_name in OPTIONAL_SOURCE_FIELDS:
        if values.get(field_name) is None:
            missing_sources.append(field_name)
            warnings.append(f"Optional source is missing: {field_name}")

    for field_name in NUMERIC_FIELDS:
        value = values.get(field_name)
        if value is None:
            continue
        if isinstance(value, bool) or not isinstance(value, (int, float)):
            errors.append(f"Invalid numeric value: {field_name}")
            continue
        if not math.isfinite(float(value)):
            errors.append(f"Invalid numeric value: {field_name}")
            continue
        if field_name in MONETARY_FIELDS and value < 0:
            errors.append(f"Negative monetary value: {field_name}")

    return {
        "is_valid": not errors and not conflicts,
        "errors": errors,
        "warnings": warnings,
        "missing_fields": missing_fields,
        "missing_sources": missing_sources,
        "conflicts": conflicts,
    }
