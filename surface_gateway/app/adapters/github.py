import uuid
from typing import Any

from surface_gateway.app.adapters.base import BaseSurfaceAdapter
from surface_gateway.app.config import config
from surface_gateway.app.schemas.events import (
    HumanActor,
    HumanInteractionEvent,
    InteractionType,
    SurfaceType,
)
from surface_gateway.app.utils.bot_filter import is_bot_event
from surface_gateway.app.utils.security import verify_github_signature


class GitHubAdapter(BaseSurfaceAdapter):
    """
    GitHub Webhook Adapter. Handles HMAC verification, bot filtering,
    and payload normalization for GitHub Issues and Issue Comments.
    """

    def verify_signature(self, raw_body: bytes, signature_header: str | None) -> bool:
        return verify_github_signature(
            raw_body, signature_header, config.github_webhook_secret
        )

    def is_bot_event(self, payload: dict[str, Any]) -> bool:
        return is_bot_event(payload)

    def parse_and_normalize(
        self, payload: dict[str, Any], event_type: str
    ) -> HumanInteractionEvent:
        event_id = str(uuid.uuid4())
        github_event_type = event_type or ""

        issue_data = payload.get("issue", {})
        comment_data = payload.get("comment", {})
        sender = payload.get("sender", {})

        user_handle = sender.get("login", "unknown_user")
        issue_id = issue_data.get("number")
        comment_id = comment_data.get("id")

        content = comment_data.get("body") or issue_data.get("body") or ""

        interaction_type = InteractionType.COMMENT
        if github_event_type == "issues" and payload.get("action") == "opened":
            interaction_type = InteractionType.ISSUE_OPENED

        actor = HumanActor(
            user_id=user_handle, surface_handle=f"@{user_handle}", is_bot=False
        )

        return HumanInteractionEvent(
            event_id=event_id,
            surface=SurfaceType.GITHUB,
            interaction_type=interaction_type,
            issue_id=issue_id,
            comment_id=comment_id,
            thread_ref=f"github:issue:{issue_id}" if issue_id else "github:general",
            actor=actor,
            content=content,
            raw_payload=payload,
        )


github_adapter = GitHubAdapter()
