from google.adk.agents import LlmAgent

from spec_engine.agents.config import config
from spec_engine.agents.council.callbacks import create_review_callbacks

from .prompt import get_prompt
from .schemas import SecurityReviewResult

init_security_reviewer_state_callback, save_security_review_callback = (
    create_review_callbacks(
        output_key="security_review_result",
        history_key="security_review_history",
    )
)

security_reviewer_agent = LlmAgent(
    name="security_reviewer",
    model=config.model,
    description="Security Lead on the Council evaluating specs for OWASP risks, authentication, and compliance.",
    instruction=get_prompt(),
    include_contents="none",
    before_agent_callback=init_security_reviewer_state_callback,
    output_schema=SecurityReviewResult,
    output_key="security_review_result",
    after_agent_callback=save_security_review_callback,
)

root_agent = security_reviewer_agent
