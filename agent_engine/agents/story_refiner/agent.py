from typing import Any

from google.adk.agents import LlmAgent

from agent_engine.agents.config import config
from agent_engine.agents.state import set_user_story
from agent_engine.agents.store import create_agent_state_callback, extract_text_from_output
from agent_engine.agents.tools import get_github_mcp_toolset
from agent_engine.skills.skills import user_story_skill_toolset

from .prompt import get_prompt

save_user_story_callback = create_agent_state_callback(
    target_path="specifications.user_story_markdown",
    updater=lambda text, store: set_user_story(store.ctx, text),
    required_error_msg="user_story_refiner agent produced empty or insufficient story output.",
)


user_story_refiner_agent = LlmAgent(
    name="user_story_refiner",
    model=config.model,
    description="An expert Agile Product Owner agent that refines draft requirements into standardized, actionable user stories.",
    instruction=get_prompt(),
    tools=[
        user_story_skill_toolset,
        get_github_mcp_toolset(
            toolsets="issues,repos",
            allowed_tools=["search_code", "get_issue"],
        ),
    ],
    after_agent_callback=save_user_story_callback,
)

root_agent = user_story_refiner_agent
