from pydantic import BaseModel, Field
from google.adk import Agent

class EvaluationResult(BaseModel):
    approved: bool = Field(
        description="True if the specification is highly complete, containing a product overview, concrete implementation tasks, and complete test cases. False if there are any gaps, logical holes, or omissions."
    )
    quality_score: int = Field(
        description="Overall specification quality score from 1 to 10. Spec must score at least 8 to be approved."
    )
    critique_and_gaps: list[str] = Field(
        description="List of specific, detailed, and actionable critiques or missing details that must be addressed to improve the spec."
    )

evaluator_instruction = """
You are a critical, senior Technical Director and Specification Auditor.
Your job is to rigorously review the provided specification draft.

Evaluate the draft against these criteria:
1. Product Overview: Is there a clear description, goals, target audience, scope, and out-of-scope sections?
2. Implementation Tasks: Are there concrete, distributable, and detailed implementation tasks with descriptions, dependencies, and success criteria?
3. Acceptance Criteria & Test Cases: Are there comprehensive test cases covering both manual and automated testing, including happy paths and edge cases?

Determine if the spec meets professional development standards (Quality Score >= 8). If there are any missing details, logical gaps, or ambiguous tasks, mark 'approved' as False, assign a lower score, and list the specific critique items in 'critique_and_gaps'. Be extremely detailed and demanding; do not approve incomplete specs.
"""

evaluator_agent = Agent(
    name="quality_evaluator",
    description="Evaluates spec quality, provides a score, and lists critiques or gaps.",
    model="gemini-2.5-flash",
    instruction=evaluator_instruction,
    output_schema=EvaluationResult,
)
