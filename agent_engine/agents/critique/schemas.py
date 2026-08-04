from pydantic import BaseModel, Field
from typing import List, Optional


class CritiqueResult(BaseModel):
    is_approved: bool = Field(
        ...,
        description="Set to True if the artifact meets all quality standards and is ready for human review, or False if revisions are required."
    )
    score: int = Field(
        ...,
        ge=1,
        le=10,
        description="Quality and completeness score from 1 (poor) to 10 (exceptional)."
    )
    critique_notes: str = Field(
        ...,
        description="Detailed constructive critique outlining specific improvements, missing edge cases, or architectural gaps."
    )
    missing_elements: List[str] = Field(
        default_factory=list,
        description="List of specific missing items (e.g. ['Missing rate-limiting NFR', 'Unclear API contract', 'Undefined error state'])."
    )
