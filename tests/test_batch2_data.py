import math

import pytest
from pydantic import ValidationError

from backend.data.normalization import normalize_applicant
from backend.data.validation import validate_applicant
from backend.schemas.applicant import Applicant


def valid_values() -> dict:
    return {
        "applicant_id": "applicant-001",
        "monthly_income": 30000,
        "monthly_rent": 10000,
        "utility_payment_history": 12,
        "telecom_payment_history": 10,
        "bank_cashflow": 28000,
        "gig_income": 5000,
        "repayment_history": 8,
    }


def test_valid_applicant_is_valid() -> None:
    result = validate_applicant(Applicant(**valid_values()))

    assert result["is_valid"] is True
    assert result["errors"] == []


def test_missing_required_field_is_an_error() -> None:
    values = valid_values()
    del values["monthly_income"]

    result = validate_applicant(values)

    assert result["is_valid"] is False
    assert "monthly_income" in result["missing_fields"]


def test_blank_applicant_id_is_an_error() -> None:
    result = validate_applicant({**valid_values(), "applicant_id": "   "})

    assert result["is_valid"] is False
    assert "Applicant ID must not be blank." in result["errors"]


def test_invalid_numeric_type_is_an_error() -> None:
    result = validate_applicant({**valid_values(), "monthly_income": "abc"})

    assert result["is_valid"] is False
    assert "Invalid numeric value: monthly_income" in result["errors"]


def test_negative_monetary_value_is_rejected_by_schema() -> None:
    with pytest.raises(ValidationError):
        Applicant(**{**valid_values(), "monthly_income": -1})


@pytest.mark.parametrize("bad_value", [math.nan, math.inf, -math.inf, True])
def test_invalid_numeric_values_are_reported(bad_value) -> None:
    result = validate_applicant({**valid_values(), "monthly_income": bad_value})

    assert result["is_valid"] is False
    assert "Invalid numeric value: monthly_income" in result["errors"]


def test_missing_optional_sources_are_warnings_not_errors() -> None:
    values = valid_values()
    values["utility_payment_history"] = None
    values["telecom_payment_history"] = None

    result = validate_applicant(values)

    assert result["is_valid"] is True
    assert "utility_payment_history" in result["missing_sources"]
    assert "telecom_payment_history" in result["missing_sources"]
    assert result["errors"] == []


def test_bank_and_gig_income_are_separate_sources() -> None:
    values = valid_values()
    values["bank_income"] = 30000
    values["gig_income"] = 45000

    result = validate_applicant(values)

    assert result["is_valid"] is True
    assert result["conflicts"] == []


def test_validation_is_deterministic() -> None:
    values = {**valid_values(), "bank_income": 30000}

    assert validate_applicant(values) == validate_applicant(values)


def test_normalization_is_deterministic_and_preserves_missing_values() -> None:
    values = valid_values()
    values["utility_payment_history"] = None

    first = normalize_applicant(values)
    second = normalize_applicant(values)

    assert first == second
    assert first["monthly_income"] == 30000.0
    assert first["utility_payment_history"] is None
