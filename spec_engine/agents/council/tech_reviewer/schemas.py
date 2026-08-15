from pydantic import BaseModel, Field


class TechReviewResult(BaseModel):
    """Structured output for Technical Architect Reviewer evaluation."""

    tech_score: int = Field(
        ...,
        description="Score (1-100) evaluating technical feasibility, architecture alignment, NFR completeness, and testability.",
    )
    architecture_feedback: str = Field(
        ...,
        description="Detailed feedback evaluating software design, component boundaries, modularity, and integration patterns.",
    )
    nfr_assessments: list[str] = Field(
        default_factory=list,
        description="List of Non-Functional Requirement (NFR) assessments (e.g., performance, scalability, reliability, error handling).",
    )
    recommendations: list[str] = Field(
        default_factory=list,
        description="Specific actionable recommendations to improve technical architecture, implementation feasibility, and testability.",
    )
    is_approved: bool = Field(
        ...,
        description="True if technical requirements meet standard quality bar (tech_score >= 80 and no critical architectural gaps), False if revisions are required.",
    )
