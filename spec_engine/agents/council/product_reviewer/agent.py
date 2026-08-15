from google.adk.agents import LlmAgent

from spec_engine.agents.config import config
from spec_engine.agents.council.callbacks import create_review_callbacks

from .prompt import get_prompt
from .schemas import ProductReviewResult

init_product_reviewer_state_callback, save_product_review_callback = (
    create_review_callbacks(
        output_key="product_review_result",
        history_key="product_review_history",
    )
)

product_reviewer_agent = LlmAgent(
    name="product_reviewer",
    model=config.model,
    description="Product Reviewer on the Council evaluating specs for user value, INVEST principles, and scope clarity.",
    instruction=get_prompt(),
    include_contents="none",
    before_agent_callback=init_product_reviewer_state_callback,
    output_schema=ProductReviewResult,
    output_key="product_review_result",
    after_agent_callback=save_product_review_callback,
)

root_agent = product_reviewer_agent
