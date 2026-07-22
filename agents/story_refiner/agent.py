from google.adk.agents import LlmAgent

from .config import config
from .prompt import get_prompt
from agents.tools import search_local_requirements, create_github_issue


root_agent = LlmAgent(
    name="user_story_refiner",
    model=config.default_llm,
    description="An expert Agile Product Owner agent that refines draft requirements into standardized, actionable user stories.",
    instruction=get_prompt(),
    tools=[search_local_requirements, create_github_issue],
)
