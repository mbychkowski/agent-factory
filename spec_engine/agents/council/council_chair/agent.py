from google.adk.agents import LlmAgent

from spec_engine.agents.config import config

from .prompt import get_prompt
from .schemas import CouncilChairResult

council_chair_agent = LlmAgent(
    name="council_chair",
    model=config.model,
    description="Council Chair synthesizing Product, Tech, and Security reviews into a consolidated revision guide.",
    instruction=get_prompt(),
    include_contents="none",
    output_schema=CouncilChairResult,
    output_key="council_chair_result",
)

root_agent = council_chair_agent
