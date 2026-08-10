import json
from typing import Any

from google.adk.agents import LlmAgent

from agent_engine.agents.config import config
from agent_engine.agents.state import record_critique_result
from agent_engine.agents.tools import get_github_mcp_toolset
from agent_engine.skills.skills import user_story_skill_toolset

from .prompt import get_prompt
from .schemas import CritiqueResult


def extract_critique_data(node_input: Any) -> dict[str, Any] | None:
    """Extracts structured critique dictionary from dicts, Pydantic models, or JSON strings."""
    if not node_input:
        return None
    if isinstance(node_input, dict):
        return node_input
    if hasattr(node_input, "model_dump"):
        return node_input.model_dump()
    if hasattr(node_input, "dict"):
        return node_input.dict()
    if isinstance(node_input, str):
        clean = node_input.strip()
        if "```json" in clean:
            clean = clean.split("```json")[1].split("```")[0].strip()
        elif "```" in clean:
            clean = clean.split("```")[1].split("```")[0].strip()
        try:
            res = json.loads(clean)
            if isinstance(res, dict):
                return res
        except Exception:
            pass
    return None


from agent_engine.agents.store import create_agent_state_callback, AgentStore


def _record_critique_updater(data: dict[str, Any], store: AgentStore) -> None:
    record_critique_result(
        store.ctx,
        is_approved=bool(data.get("is_approved", False)),
        critique_notes=str(data.get("critique_notes", "")),
        score=data.get("score"),
        missing_elements=data.get("missing_elements", []),
    )


save_critique_callback = create_agent_state_callback(
    extractor=extract_critique_data,
    updater=_record_critique_updater,
    required_error_msg="story_critic agent produced invalid or empty critique output.",
)


story_critic_agent = LlmAgent(
    name="story_critic",
    model=config.model,
    description="Technical Architect reviewing User Story drafts for technical feasibility, NFR completeness, and testability.",
    instruction=get_prompt(),
    tools=[
        user_story_skill_toolset,
        get_github_mcp_toolset(
            toolsets="repos",
            allowed_tools=["search_code"],
        ),
    ],
    output_schema=CritiqueResult,
    after_agent_callback=save_critique_callback,
)

root_agent = story_critic_agent

