"""P2 request models for the complete P1 decision contract."""

from typing import Any, Dict, Optional

from pydantic import BaseModel, ConfigDict, Field


class DecisionSnapshot(BaseModel):
    model_config = ConfigDict(extra="allow")

    decision_id: str = Field(min_length=1)
    snapshot_hash: str = Field(min_length=64, max_length=64)
    applicant_id: str = Field(min_length=1)
    decision_date: str = Field(min_length=10, max_length=10)
    decision: str
    score: int
    probability: float
    model_version: str
    model_artifact_sha256: str
    model_metadata_sha256: str
    rulebook_version: str
    rulebook_sha256: str
    feature_registry_version: str
    feature_registry_hash: str
    normalized_input: Dict[str, Any]
    feature_vector: Dict[str, Any]
    contributing_factors: list[Dict[str, Any]] = Field(default_factory=list)
    adverse_action: list[Dict[str, Any]] = Field(default_factory=list)
    data_quality: Dict[str, Any] = Field(default_factory=dict)
    watchlist: Dict[str, Any] = Field(default_factory=dict)
    decision_serialization_version: str


class SnapshotSubmission(BaseModel):
    model_config = ConfigDict(extra="forbid")

    snapshot: DecisionSnapshot
    request: Optional[Dict[str, Any]] = None
