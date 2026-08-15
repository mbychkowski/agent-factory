from google.adk.agents import LlmAgent

from spec_engine.agents.config import config
from spec_engine.agents.council.callbacks import create_review_callbacks
from spec_engine.skills.skills import agent_spec_skill_toolset

from .prompt import get_prompt
from .schemas import TechReviewResult

init_tech_reviewer_state_callback, save_tech_review_callback = create_review_callbacks(
    output_key="tech_review_result",
    history_key="tech_review_history",
)

tools_list = [agent_spec_skill_toolset]

tech_reviewer_agent = LlmAgent(
    name="tech_reviewer",
    model=config.model,
    description="Technical Architect on the Council evaluating specs for technical feasibility, architecture alignment, NFR completeness, and testability.",
    instruction=get_prompt(),
    include_contents="none",
    before_agent_callback=init_tech_reviewer_state_callback,
    tools=tools_list,
    output_schema=TechReviewResult,
    output_key="tech_review_result",
    after_agent_callback=save_tech_review_callback,
)

root_agent = tech_reviewer_agent
