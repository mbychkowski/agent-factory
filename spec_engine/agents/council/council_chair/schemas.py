from pydantic import BaseModel, Field


class CouncilChairResult(BaseModel):
    """Structured output for Council Chair aggregation."""

    consolidated_feedback: str = Field(
        ...,
        description="Unified summary synthesising product, technical, and security review findings.",
    )
    required_revisions: list[str] = Field(
        default_factory=list,
        description="Prioritized list of mandatory changes required before the spec can be approved.",
    )
    overall_approved: bool = Field(
        ...,
        description="True if all council panel requirements are satisfied and spec is certified for development.",
    )
