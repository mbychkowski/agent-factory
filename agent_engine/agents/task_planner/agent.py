from google.adk.agents import LlmAgent

from .config import config
from .prompt import get_prompt


root_agent = LlmAgent(
    name="task_planner",
    model=config.default_llm,
    description="An expert Engineering Lead agent that breaks down technical design documents into concrete, ready-to-execute developer tasks.",
    instruction=get_prompt(),
    tools=[],
)
