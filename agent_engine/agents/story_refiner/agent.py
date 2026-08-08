from agent_engine.agents.state import set_user_story
from agent_engine.agents.tools import get_github_mcp_toolset
from agent_engine.skills.skills import user_story_skill_toolset
from google.adk.agents import LlmAgent
from google.adk.agents.context import Context

from agent_engine.agents.config import config
from .prompt import get_prompt


from typing import Any


async def save_user_story_callback(
    ctx: Any = None, callback_context: Any = None, **kwargs: Any
) -> None:
    """Callback triggered after user_story_refiner runs to save generated story markdown in state."""
    active_ctx = callback_context or ctx
    if active_ctx and getattr(active_ctx, "output", None):
        text = str(active_ctx.output).strip()
        if len(text) > 20:
            set_user_story(active_ctx, text)


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
