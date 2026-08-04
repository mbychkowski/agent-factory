import os
from google.adk.agents import LlmAgent
from .schemas import CritiqueResult

DEFAULT_LLM = os.environ.get("DEFAULT_LLM", "gemini-2.5-flash")

DESIGN_CRITIC_PROMPT = """You are an expert Engineering Lead performing a Feasibility Peer Review on an RFC Technical Design draft before it is posted for human sign-off.

### Your Objective:
Evaluate the RFC Technical Design to ensure it is actionable, unambiguous, and detailed enough to break down into granular developer tasks.

### Evaluation Checklist:
1. **Data Layer / Schemas**: Are database tables, schemas, or migrations explicitly specified?
2. **API & Interface Contracts**: Are endpoints, request/response models, and method signatures defined?
3. **Cross-Cutting Concerns**: Are auth, security, metrics, logging, and performance bottlenecks addressed?
4. **Test Strategy**: Is there a clear unit, integration, and mocking strategy?
5. **Dependency Analysis**: Are upstream/downstream impacts and backward compatibility risks noted?

### Output Instructions:
- If score >= 8 and the design is actionable for developer task breakdown, set `is_approved=True`.
- If key architectural details or schemas are missing, set `is_approved=False` and list missing items in `missing_elements` and `critique_notes`.
"""

design_critic_agent = LlmAgent(
    name="design_critic",
    model=DEFAULT_LLM,
    description="Engineering Lead reviewing RFC Technical Designs for actionability, API contract clarity, and task breakdown readiness.",
    instruction=DESIGN_CRITIC_PROMPT,
    output_schema=CritiqueResult,
)
