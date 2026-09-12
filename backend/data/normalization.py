"""Simple deterministic applicant normalization."""

from typing import Any, Dict

from backend.data.validation import NUMERIC_FIELDS, _applicant_values


NORMALIZED_FIELDS = (
    "applicant_id",
    "monthly_income",
    "monthly_rent",
    "bank_income",
    "utility_payment_history",
    "telecom_payment_history",
    "bank_cashflow",
    "gig_income",
    "repayment_history",
)


def normalize_applicant(applicant: Any) -> Dict[str, Any]:
    """Return fixed-order values with numeric values represented as floats."""
    values = _applicant_values(applicant)
    normalized = {}

    for field_name in NORMALIZED_FIELDS:
        value = values.get(field_name)
        if field_name in NUMERIC_FIELDS and value is not None:
            normalized[field_name] = float(value)
        else:
            normalized[field_name] = value

    return normalized
