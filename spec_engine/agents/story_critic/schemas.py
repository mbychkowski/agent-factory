from pydantic import BaseModel, Field


class CritiqueResult(BaseModel):
    is_approved: bool = Field(
        description="Set to True if the story passes peer review with a score >= 8 and no critical gaps exist."
    )
    score: int = Field(
        description="Numerical score from 1-10 evaluating overall technical clarity, testability, and NFR completeness."
    )
    critique_notes: str = Field(
        description="Detailed, actionable feedback detailing missing elements or technical revisions required."
    )
    missing_elements: list[str] = Field(
        default_factory=list,
        description="List of specific missing acceptance criteria, NFRs, or technical assumptions.",
    )
