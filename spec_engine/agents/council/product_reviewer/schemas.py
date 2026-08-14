from pydantic import BaseModel, Field


class ProductReviewResult(BaseModel):
    """Structured output for Product Reviewer evaluation."""

    invest_score: int = Field(
        ...,
        description="Score (1-100) evaluating adherence to INVEST criteria (Independent, Negotiable, Valuable, Estimable, Small, Testable).",
    )
    user_value_rating: str = Field(
        ...,
        description="Rating of business/user value delivered: HIGH, MEDIUM, LOW, or UNCLEAR.",
    )
    scope_feedback: str = Field(
        ...,
        description="Feedback on feature scope, potential scope creep, or missing user acceptance scenarios.",
    )
    recommendations: list[str] = Field(
        default_factory=list,
        description="Specific actionable recommendations to improve product clarity and INVEST alignment.",
    )
    is_approved: bool = Field(
        ...,
        description="True if product requirements meet standard quality bar, False if revisions are required.",
    )
