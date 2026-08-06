from datetime import UTC, datetime, timezone
from enum import Enum
from typing import Any, Dict, Optional

from pydantic import BaseModel, Field


class SurfaceType(str, Enum):
    GITHUB = "github"
    SLACK = "slack"
    DISCORD = "discord"
    A2A = "a2a"


class InteractionType(str, Enum):
    COMMENT = "COMMENT"
    ISSUE_OPENED = "ISSUE_OPENED"
    APPROVE_GATE = "APPROVE_GATE"
    REQUEST_REVISION = "REQUEST_REVISION"


class HumanActor(BaseModel):
    user_id: str = Field(..., description="Canonical user ID or handle")
    surface_handle: str = Field(..., description="Surface-specific handle (e.g. @mbychkowski)")
    is_bot: bool = Field(default=False, description="True if account is a bot")


class HumanInteractionEvent(BaseModel):
    event_id: str = Field(..., description="Unique ID for this interaction event")
    surface: SurfaceType = Field(default=SurfaceType.GITHUB)
    interaction_type: InteractionType = Field(default=InteractionType.COMMENT)
    issue_id: int | None = Field(default=None, description="GitHub Issue or Parent Issue ID")
    comment_id: int | None = Field(default=None, description="GitHub Comment ID if applicable")
    thread_ref: str = Field(..., description="Canonical thread reference (e.g. github:issue:100)")
    actor: HumanActor
    content: str = Field(..., description="Sanitized human message content")
    timestamp: str = Field(
        default_factory=lambda: datetime.now(UTC).isoformat()
    )
    raw_payload: dict[str, Any] | None = Field(default=None, description="Original raw payload for audit")


class GatewayResponse(BaseModel):
    status: str = Field(..., description="Status of gateway processing (e.g. accepted, dropped, ignored_bot)")
    event_id: str | None = Field(default=None)
    message: str = Field(..., description="Summary message")
