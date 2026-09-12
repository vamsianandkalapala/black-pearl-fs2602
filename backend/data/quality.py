"""Data-quality signals distinct from schema validation or fraud detection."""

import math
from typing import Any, Dict, Mapping


def assess_data_quality(record: Mapping[str, Any]) -> Dict[str, Any]:
    """Surface deterministic quality signals without silently changing data."""
    signals = []
    values = dict(record)
    numeric_fields = {
        "monthly_income",
        "monthly_rent",
        "bank_income",
        "gig_income",
        "bank_cashflow",
        "utility_payment_history",
        "telecom_payment_history",
        "repayment_history",
    }

    if values.get("bank_income") is not None and values.get("gig_income") is not None:
        total_income = values.get("monthly_income")
        source_total = values["bank_income"] + values["gig_income"]
        if total_income is not None and abs(source_total - total_income) > max(100, total_income * 0.25):
            signals.append("income_sources_differ_from_declared_income")

    for field_name, value in values.items():
        if isinstance(value, bool):
            signals.append(f"boolean_numeric_value:{field_name}")
        elif field_name in numeric_fields and not isinstance(value, (int, float)):
            signals.append(f"malformed_numeric_value:{field_name}")
        elif isinstance(value, (int, float)) and not math.isfinite(float(value)):
            signals.append(f"non_finite_value:{field_name}")

    monthly_income = values.get("monthly_income")
    if isinstance(monthly_income, (int, float)) and not isinstance(monthly_income, bool):
        if monthly_income > 1_000_000:
            signals.append("implausibly_high_monthly_income")

    return {
        "quality_status": "flagged" if signals else "no_quality_flags",
        "signals": signals,
        "data_preserved": True,
        "not_fraud_detection": True,
    }
