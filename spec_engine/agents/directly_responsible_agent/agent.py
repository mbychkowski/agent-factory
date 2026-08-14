from typing import Optional

from google.adk.agents import LlmAgent
from google.adk.agents.callback_context import CallbackContext
from google.genai import types

from spec_engine.agents.config import config
from spec_engine.agents.tools import get_github_mcp_toolset
from spec_engine.skills.skills import user_story_skill_toolset

from .prompt import get_prompt
from .schemas import UserStoryOutput


async def init_refiner_state_callback(
    callback_context: CallbackContext,
) -> None:
    """Callback executed before user_story_refiner agent runs.

    Ensures default values for prompt state placeholders exist in session state.
    """
    callback_context.state.setdefault("latest_critique_notes", "N/A (Initial Pass)")
    callback_context.state.setdefault("latest_missing_elements", "None")
    callback_context.state.setdefault("latest_critique_score", 0)
    callback_context.state.setdefault("latest_critique_is_approved", False)
    callback_context.state.setdefault("user_story_markdown", "")


async def save_user_story_callback(
    callback_context: CallbackContext,
) -> Optional[types.Content]:
    """Callback executed after user_story_refiner agent finishes execution.

    Extracts user_story_markdown from the structured result and saves it in session state.
    """
    data = callback_context.state.get("user_story_result", {})
    markdown_text = ""
    if isinstance(data, dict):
        markdown_text = str(data.get("user_story_markdown", ""))
    elif hasattr(data, "user_story_markdown"):
        markdown_text = str(getattr(data, "user_story_markdown", ""))

    callback_context.state["user_story_markdown"] = markdown_text
    return None


directly_responsible_agent = LlmAgent(
    name="directly_responsible_agent",
    model=config.model,
    description="Directly Responsible Agent (DRA) and Lead Spec Author responsible for drafting and refining technical specifications.",
    instruction=get_prompt(),
    before_agent_callback=init_refiner_state_callback,
    tools=[
        user_story_skill_toolset,
        get_github_mcp_toolset(
            toolsets="issues,repos",
            allowed_tools=["search_code", "get_issue"],
        ),
    ],
    output_schema=UserStoryOutput,
    output_key="user_story_result",
    after_agent_callback=save_user_story_callback,
)

dra_agent = directly_responsible_agent
user_story_refiner_agent = directly_responsible_agent
root_agent = directly_responsible_agent
