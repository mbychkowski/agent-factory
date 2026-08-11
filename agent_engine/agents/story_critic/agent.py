from typing import Any, Optional

from google.adk.agents import LlmAgent
from google.adk.agents.callback_context import CallbackContext
from google.genai import types

from agent_engine.agents.config import config
from agent_engine.agents.tools import get_github_mcp_toolset
from agent_engine.skills.skills import user_story_skill_toolset

from .prompt import get_prompt
from .schemas import CritiqueResult


async def init_critic_state_callback(
    callback_context: CallbackContext,
) -> None:
    """Callback executed before story_critic agent runs."""
    callback_context.state.setdefault("user_story_markdown", "")


async def save_critique_callback(
    callback_context: CallbackContext,
) -> Optional[types.Content]:
    # Retrieve structured CritiqueResult output from state (populated via output_key)
    data = callback_context.state.get("critique_result", {})

    # Safely initialize nested state dictionaries and lists
    specifications = callback_context.state.setdefault("specifications", {})
    if "critique_history" not in specifications or not isinstance(specifications["critique_history"], list):
        specifications["critique_history"] = []

    raw_missing = data.get("missing_elements", [])
    missing_elements = [str(x) for x in raw_missing] if isinstance(raw_missing, list) else []

    # Append entry in-place
    critique_entry = {
        "critique_notes": str(data.get("critique_notes", "")),
        "missing_elements": missing_elements,
        "score": int(data.get("score", 0)),
        "is_approved": bool(data.get("is_approved", False)),
    }
    specifications["critique_history"].append(critique_entry)

    callback_context.state["latest_critique_notes"] = str(data.get("critique_notes", ""))
    callback_context.state["latest_missing_elements"] = ", ".join(missing_elements) if missing_elements else "None"
    callback_context.state["latest_critique_score"] = int(data.get("score", 0))
    callback_context.state["latest_critique_is_approved"] = bool(data.get("is_approved", False))

    specifications["story_peer_reviewed"] = bool(data.get("is_approved", False))
    specifications["story_review_rounds"] = int(specifications.get("story_review_rounds", 0)) + 1

    # Re-assign top-level state key so ADK session state tracker registers the nested list updates
    callback_context.state["specifications"] = dict(specifications)

    return None


story_critic_agent = LlmAgent(
    name="story_critic",
    model=config.model,
    description="Technical Architect reviewing User Story drafts for technical feasibility, NFR completeness, and testability.",
    instruction=get_prompt(),
    include_contents="none",
    before_agent_callback=init_critic_state_callback,
    tools=[
        user_story_skill_toolset,
        get_github_mcp_toolset(
            toolsets="repos",
            allowed_tools=["search_code"],
        ),
    ],
    output_schema=CritiqueResult,
    output_key="critique_result",
    after_agent_callback=save_critique_callback,
)

root_agent = story_critic_agent


