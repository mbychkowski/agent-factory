from google.adk.agents import LlmAgent

from spec_engine.agents.config import config
from spec_engine.agents.council.callbacks import create_review_callbacks

from .prompt import get_prompt
from .schemas import CouncilChairResult

init_council_chair_state_callback, save_council_chair_callback = (
    create_review_callbacks(
        output_key="council_chair_result",
        history_key="council_chair_history",
    )
)

council_chair_agent = LlmAgent(
    name="council_chair",
    model=config.model,
    description="Council Chair synthesizing Product, Tech, and Security reviews into a consolidated revision guide.",
    instruction=get_prompt(),
    include_contents="none",
    before_agent_callback=init_council_chair_state_callback,
    output_schema=CouncilChairResult,
    output_key="council_chair_result",
    after_agent_callback=save_council_chair_callback,
)

root_agent = council_chair_agent
