from google.adk.agents import LlmAgent

from .config import config
from .prompt import get_prompt
from .schemas import FacilitatorTriageOutput


root_agent = LlmAgent(
    name="deliberation_facilitator",
    model=config.default_llm,
    description=(
        "An expert Spec Deliberation Facilitator that triages human messages, "
        "filters noise, synthesizes consensus deltas, and routes actionable feedback "
        "to downstream spec agents."
    ),
    instruction=get_prompt(),
    output_schema=FacilitatorTriageOutput,
)
