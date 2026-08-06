from google.adk.agents import LlmAgent
from google.adk.agents.context import Context

from agent_engine.agents.state import set_user_story
from agent_engine.agents.tools import get_github_mcp_toolset
from agent_engine.skills.skills import user_story_skill_toolset

from .config import config
from .prompt import get_prompt


async def save_user_story_callback(ctx: Context) -> None:
    """Callback triggered after user_story_refiner runs to save generated story markdown in state."""
    if ctx.output:
        text = str(ctx.output).strip()
        if len(text) > 20:
            set_user_story(ctx, text)


root_agent = LlmAgent(
    name="user_story_refiner",
    model=config.default_llm,
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
