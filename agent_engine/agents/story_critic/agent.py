from typing import Any

from google.adk.agents import LlmAgent

from agent_engine.agents.config import config
from agent_engine.agents.state import record_critique_result
from agent_engine.agents.store import AgentStore, create_agent_state_callback
from agent_engine.agents.tools import get_github_mcp_toolset
from agent_engine.skills.skills import user_story_skill_toolset

from .prompt import get_prompt
from .schemas import CritiqueResult


def _record_critique_updater(data: dict[str, Any], store: AgentStore) -> None:
    record_critique_result(
        store.ctx,
        is_approved=bool(data.get("is_approved", False)),
        critique_notes=str(data.get("critique_notes", "")),
        score=data.get("score"),
        missing_elements=data.get("missing_elements", []),
    )


save_critique_callback = create_agent_state_callback(
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
