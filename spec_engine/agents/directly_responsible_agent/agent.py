"""Directly Responsible Agent (DRA) definition for spec drafting and refinement."""

from typing import Any

from google.adk.agents import LlmAgent
from google.adk.agents.callback_context import CallbackContext
from google.genai import types

from spec_engine.agents.config import config
from spec_engine.agents.state import ensure_session_state
from spec_engine.skills.skills import agent_spec_skill_toolset

from .prompt import get_prompt
from .schemas import SpecOutput


async def init_state_callback(
    callback_context: CallbackContext,
) -> None:
    """Callback executed before directly_responsible_agent runs.

    Ensures default values for prompt state placeholders exist in session state,
    leveraging AgentSessionState Pydantic schema as the single source of truth.
    """
    ensure_session_state(callback_context.state)


def get_instruction(ctx: Any) -> str:
    """Dynamic instruction provider that safely injects state variables from specifications state."""
    state = getattr(ctx, "state", {}) if hasattr(ctx, "state") else {}
    specifications = state.get("specifications", {}) if isinstance(state, dict) else {}

    full_spec = (
        specifications.get("full_spec_markdown", "")
        if isinstance(specifications, dict)
        else ""
    )
    council_notes = (
        specifications.get("council_notes_summarized", "N/A (Initial Pass)")
        if isinstance(specifications, dict)
        else "N/A (Initial Pass)"
    )

    # Use explicit string replacements to prevent KeyError / ValueError
    # when markdown contains arbitrary braces/JSON/code blocks
    prompt_template = get_prompt()
    return prompt_template.replace("{full_spec_markdown}", full_spec).replace(
        "{council_notes_summarized}", council_notes
    )


async def save_spec_callback(
    callback_context: CallbackContext,
) -> types.Content | None:
    """Callback executed after directly_responsible_agent finishes execution."""
    raw_data = callback_context.state.get("spec_result")

    if isinstance(raw_data, SpecOutput):
        markdown_text = raw_data.full_spec_markdown
    elif hasattr(raw_data, "model_dump"):
        markdown_text = str(raw_data.model_dump().get("full_spec_markdown", ""))
    elif isinstance(raw_data, dict):
        markdown_text = str(raw_data.get("full_spec_markdown", ""))
    else:
        markdown_text = ""

    ensure_session_state(callback_context.state)
    specifications = callback_context.state.get("specifications")
    specs_dict = specifications if isinstance(specifications, dict) else {}

    updated_specs = {
        **specs_dict,
        "full_spec_markdown": markdown_text,
    }
    callback_context.state["specifications"] = updated_specs

    return None


dra_tools = [agent_spec_skill_toolset]

directly_responsible_agent = LlmAgent(
    name="directly_responsible_agent",
    model=config.model,
    description="Directly Responsible Agent (DRA) and Lead Spec Author responsible for drafting and refining technical specifications.",
    instruction=get_instruction,
    before_agent_callback=init_state_callback,
    tools=dra_tools,
    output_schema=SpecOutput,
    output_key="spec_result",
    after_agent_callback=save_spec_callback,
)

root_agent = directly_responsible_agent
