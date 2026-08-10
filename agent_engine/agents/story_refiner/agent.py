from agent_engine.agents.state import set_user_story
from agent_engine.agents.tools import get_github_mcp_toolset
from agent_engine.skills.skills import user_story_skill_toolset
from google.adk.agents import LlmAgent
from google.adk.agents.context import Context

from agent_engine.agents.config import config
from .prompt import get_prompt


from typing import Any


def extract_text_from_output(val: Any) -> str:
    """Extracts text from string, Part, Content, or Event objects."""
    if isinstance(val, str):
        return val.strip()
    if hasattr(val, "content") and val.content:
        return extract_text_from_output(val.content)
    if hasattr(val, "parts") and val.parts:
        return "\n".join(str(p.text) for p in val.parts if getattr(p, "text", None)).strip()
    return str(val or "").strip()


async def save_user_story_callback(
    ctx: Any = None, callback_context: Any = None, **kwargs: Any
) -> None:
    """Callback triggered after user_story_refiner runs to save generated story markdown in state."""
    active_ctx = callback_context or ctx
    if not active_ctx:
        return

    output = getattr(active_ctx, "output", None)
    text = extract_text_from_output(output) if output else ""

    if not text or len(text) <= 20:
        raise ValueError("user_story_refiner agent produced empty or insufficient story output.")

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
