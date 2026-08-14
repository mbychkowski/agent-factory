from google.adk.agents import LlmAgent

from spec_engine.agents.config import config

from .prompt import get_prompt
from .schemas import SecurityReviewResult

security_reviewer_agent = LlmAgent(
    name="security_reviewer",
    model=config.model,
    description="Security Lead on the Council evaluating specs for OWASP risks, authentication, and compliance.",
    instruction=get_prompt(),
    include_contents="none",
    output_schema=SecurityReviewResult,
    output_key="security_review_result",
)

root_agent = security_reviewer_agent
