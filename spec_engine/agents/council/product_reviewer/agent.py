from google.adk.agents import LlmAgent

from spec_engine.agents.config import config

from .prompt import get_prompt
from .schemas import ProductReviewResult

product_reviewer_agent = LlmAgent(
    name="product_reviewer",
    model=config.model,
    description="Product Reviewer on the Council evaluating specs for user value, INVEST principles, and scope clarity.",
    instruction=get_prompt(),
    include_contents="none",
    output_schema=ProductReviewResult,
    output_key="product_review_result",
)

root_agent = product_reviewer_agent
