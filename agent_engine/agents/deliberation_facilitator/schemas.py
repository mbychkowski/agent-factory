from enum import Enum
from typing import Optional
from pydantic import BaseModel, Field


class MessageClassification(str, Enum):
    NOISE_OFF_TOPIC = "NOISE_OFF_TOPIC"
    META_QUESTION = "META_QUESTION"
    UNRESOLVED_DISCUSSION = "UNRESOLVED_DISCUSSION"
    ACTIONABLE_SPEC_FEEDBACK = "ACTIONABLE_SPEC_FEEDBACK"


class TargetSpecPhase(str, Enum):
    USER_STORY = "USER_STORY"
    TECHNICAL_DESIGN = "TECHNICAL_DESIGN"
    TASK_PLANNING = "TASK_PLANNING"
    NONE = "NONE"


class FacilitatorTriageOutput(BaseModel):
    classification: MessageClassification = Field(
        ...,
        description="Category of the human interaction: NOISE_OFF_TOPIC, META_QUESTION, UNRESOLVED_DISCUSSION, or ACTIONABLE_SPEC_FEEDBACK."
    )
    target_phase: TargetSpecPhase = Field(
        default=TargetSpecPhase.NONE,
        description="Which phase of the spec process this feedback targets: USER_STORY, TECHNICAL_DESIGN, TASK_PLANNING, or NONE."
    )
    synthesized_delta: Optional[str] = Field(
        default=None,
        description="Clean, concise summary of the spec change or consensus decision to pass to downstream spec agents."
    )
    human_response: Optional[str] = Field(
        default=None,
        description="Message to post back to the human surface channel (e.g. answering a meta-question or asking a clarifying question)."
    )
    is_gate_approval: bool = Field(
        default=False,
        description="Set to True if the human explicitly approved the current spec phase/gate."
    )
