from pydantic import BaseModel, Field


class SecurityReviewResult(BaseModel):
    """Structured output for Security Reviewer evaluation."""

    security_score: int = Field(
        ...,
        description="Score (1-100) evaluating security posture, threat mitigation, and OWASP compliance.",
    )
    vulnerability_concerns: list[str] = Field(
        default_factory=list,
        description="List of identified security risks, missing auth/authz checks, or data protection gaps.",
    )
    compliance_notes: str = Field(
        ...,
        description="Notes regarding regulatory or policy compliance (e.g. GDPR, SOC2, HIPAA, OWASP).",
    )
    recommendations: list[str] = Field(
        default_factory=list,
        description="Actionable recommendations to harden security controls and mitigate threats.",
    )
    is_approved: bool = Field(
        ...,
        description="True if security requirements meet acceptable standards, False if security revisions are required.",
    )
