from agent_engine.agents.tools import get_github_mcp_toolset
from agent_engine.skills.skills import user_story_skill_toolset
from google.adk.agents import LlmAgent

from agent_engine.agents.config import config
from .prompt import get_prompt
from .schemas import CritiqueResult

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
)

root_agent = story_critic_agent
