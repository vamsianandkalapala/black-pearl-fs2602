"""Language-independent request fields for the decision endpoint."""

from typing import Optional

from pydantic import BaseModel, ConfigDict, Field

from backend.schemas.applicant import Applicant


class WatchlistResult(BaseModel):
    """Language-independent screening result supplied by P2/P4."""

    model_config = ConfigDict(extra="forbid")

    status: str = Field(..., pattern="^(NOT_SCREENED|CLEAR|CONFIRMED_MATCH|POSSIBLE_MATCH|UNAVAILABLE)$")
    matched: bool
    match_type: Optional[str] = None
    confidence: Optional[float] = Field(default=None, ge=0, le=1)
    reason: str


class DecisionRequest(BaseModel):
    """Versioned decision request accepted by POST /decision."""

    model_config = ConfigDict(extra="forbid")

    applicant: Applicant
    rulebook_version: str = Field(default="v1", min_length=1)
    decision_date: str = Field(..., min_length=10)
    language: str = Field(default="en", min_length=2, max_length=10)
    watchlist: Optional[WatchlistResult] = None
