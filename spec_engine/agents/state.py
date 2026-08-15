"""State schema models and initialization utilities for Spec Engine."""

from collections.abc import Mapping
from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class CouncilScores(BaseModel):
    model_config = ConfigDict(extra="allow")
    product: int = 0
    tech: int = 0
    security: int = 0


class SpecificationsState(BaseModel):
    model_config = ConfigDict(extra="allow")
    full_spec_markdown: str = Field(
        default="", description="Generated full specification markdown"
    )
    revision_summary: str = Field(
        default="", description="Summary of changes in latest revision"
    )
    council_scores: CouncilScores = Field(default_factory=CouncilScores)
    council_notes_summarized: str = Field(
        default="N/A (Initial Pass)", description="Summarized council review feedback"
    )
    council_review_rounds: int = Field(
        default=0, description="Council review round count"
    )
    council_approved: bool = Field(
        default=False, description="True if council approved the spec"
    )
    product_review_history: list[dict[str, Any]] = Field(default_factory=list)
    tech_review_history: list[dict[str, Any]] = Field(default_factory=list)
    security_review_history: list[dict[str, Any]] = Field(default_factory=list)
    council_chair_history: list[dict[str, Any]] = Field(default_factory=list)


class AgentSessionState(BaseModel):
    model_config = ConfigDict(extra="allow")
    council_review: list[dict[str, Any]] = Field(default_factory=list)
    specifications: SpecificationsState = Field(default_factory=SpecificationsState)


def _to_plain_dict(data: Any) -> Any:
    """Recursively converts mappings and state proxies to plain dictionaries."""
    if hasattr(data, "model_dump"):
        return data.model_dump()
    if hasattr(data, "to_dict"):
        return _to_plain_dict(data.to_dict())
    if isinstance(data, Mapping):
        return {k: _to_plain_dict(v) for k, v in data.items()}
    if isinstance(data, list):
        return [_to_plain_dict(item) for item in data]
    return data


def _strip_none_deep(data: Any) -> Any:
    """Recursively removes keys whose values are None so Pydantic defaults can kick in."""
    if isinstance(data, dict):
        return {k: _strip_none_deep(v) for k, v in data.items() if v is not None}
    if isinstance(data, list):
        return [_strip_none_deep(item) for item in data if item is not None]
    return data


def ensure_session_state(raw_state: Any) -> Any:
    """Ensures raw_state dictionary or ADK State object is fully populated with default state schema values.

    Validates and fills nested defaults while preserving custom extra keys.
    """
    if raw_state is None:
        state_dict: dict[str, Any] = {}
    else:
        plain = _to_plain_dict(raw_state)
        state_dict = plain if isinstance(plain, dict) else {}

    sanitized = _strip_none_deep(state_dict)
    validated = AgentSessionState.model_validate(sanitized)
    dumped = validated.model_dump()

    # Mutates raw_state in place to register updates with ADK state managers or dicts
    if hasattr(raw_state, "update") and callable(raw_state.update) or isinstance(raw_state, dict):
        raw_state.update(dumped)
    elif hasattr(raw_state, "__setitem__"):
        for k, v in dumped.items():
            raw_state[k] = v

    return raw_state
