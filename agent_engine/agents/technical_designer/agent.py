from google.adk.agents import LlmAgent

from .config import config
from .prompt import get_prompt
from agent_engine.agents.tools import (
    add_design_comment,
    execute_code_experiment,
    search_local_codebase,
)


root_agent = LlmAgent(
    name="technical_designer",
    model=config.default_llm,
    description="An expert Software Architect agent that analyzes user stories and drafts RFC technical design specs.",
    instruction=get_prompt(),
    tools=[search_local_codebase, execute_code_experiment, add_design_comment],
)
