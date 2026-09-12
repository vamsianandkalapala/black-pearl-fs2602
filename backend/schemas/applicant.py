from typing import Optional

import unicodedata

from pydantic import BaseModel, ConfigDict, Field, field_validator


class Applicant(BaseModel):
    """Applicant data used by the validation and normalization foundation."""

    model_config = ConfigDict(
        allow_inf_nan=False,
        extra="forbid",
        str_strip_whitespace=True,
    )

    applicant_id: str = Field(
        ...,
        min_length=1,
        description="Stable applicant identifier.",
    )

    @field_validator(
        "monthly_income",
        "monthly_rent",
        "bank_income",
        "utility_payment_history",
        "telecom_payment_history",
        "bank_cashflow",
        "gig_income",
        "repayment_history",
        mode="before",
    )
    @classmethod
    def reject_unsafe_numeric_inputs(cls, value):
        """Reject values Pydantic might otherwise coerce unexpectedly."""
        if isinstance(value, bool) or isinstance(value, str):
            raise ValueError("Numeric fields must contain numbers.")
        return value

    @field_validator("applicant_id")
    @classmethod
    def normalize_applicant_id(cls, value: str) -> str:
        """Use one Unicode-normalized identifier representation."""
        normalized = unicodedata.normalize("NFC", value).strip()
        if not normalized:
            raise ValueError("Applicant ID must not be blank.")
        return normalized
    monthly_income: float = Field(
        ...,
        ge=0,
        description="Monthly income in the local currency.",
    )
    monthly_rent: float = Field(
        ...,
        ge=0,
        description="Monthly rent in the local currency.",
    )
    bank_income: Optional[float] = Field(
        default=None,
        ge=0,
        description="Optional income reported by a bank source.",
    )
    utility_payment_history: Optional[float] = Field(default=None, ge=0)
    telecom_payment_history: Optional[float] = Field(default=None, ge=0)
    bank_cashflow: Optional[float] = Field(default=None, ge=0)
    gig_income: Optional[float] = Field(default=None, ge=0)
    repayment_history: Optional[float] = Field(default=None, ge=0)
