from google.adk.agents import LlmAgent

from .config import config
from .prompt import get_prompt
from agents.tools import search_local_codebase, add_design_comment


root_agent = LlmAgent(
    name="technical_designer",
    model=config.default_llm,
    description="An expert Software Architect agent that analyzes user stories and drafts RFC technical design specs.",
    instruction=get_prompt(),
    tools=[search_local_codebase, add_design_comment],
)
