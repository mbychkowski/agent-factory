import logging
from typing import Any

from fastapi import APIRouter, Header, HTTPException, Request
from fastapi.responses import JSONResponse

from surface_gateway.app.adapters.github import github_adapter
from surface_gateway.app.schemas.events import GatewayResponse
from surface_gateway.app.services.publisher import publish_event

logger = logging.getLogger(__name__)

router = APIRouter()


@router.post("/webhooks/github", response_model=GatewayResponse, status_code=202)
async def github_webhook(
    request: Request,
    x_github_event: str = Header(..., alias="X-GitHub-Event"),
    x_hub_signature_256: str | None = Header(None, alias="X-Hub-Signature-256"),
):
    raw_body = await request.body()

    # 1. Verify HMAC SHA-256 Signature using GitHubAdapter
    if not github_adapter.verify_signature(raw_body, x_hub_signature_256):
        logger.warning("GitHub Webhook: HMAC signature verification failed.")
        raise HTTPException(status_code=401, detail="Invalid HMAC signature")

    try:
        payload: dict[str, Any] = await request.json()
    except Exception:  # noqa: BLE001
        raise HTTPException(status_code=400, detail="Invalid JSON payload")

    # 2. Filter out Bot Self-Loops & Non-Actionable Events (e.g. issues.edited)
    action = payload.get("action", "")
    if (
        github_adapter.is_bot_event(payload)
        or (x_github_event == "issues" and action != "opened")
        or (x_github_event == "issue_comment" and action != "created")
    ):
        logger.info(
            f"GitHub Webhook: Dropping event '{x_github_event}.{action}' to prevent self-loops."
        )
        return JSONResponse(
            status_code=200,
            content={
                "status": "ignored",
                "event_id": None,
                "message": f"Event '{x_github_event}.{action}' ignored to prevent self-loops.",
            },
        )

    # 3. Parse & Normalize to Canonical HumanInteractionEvent
    normalized_event = github_adapter.parse_and_normalize(payload, x_github_event)

    # 4. Publish Event
    http_client = getattr(
        getattr(request, "app", None), "state", None
    ) and getattr(request.app.state, "http_client", None)

    success = await publish_event(
        normalized_event, base_url=str(request.base_url), http_client=http_client
    )

    if success:
        return GatewayResponse(
            status="accepted",
            event_id=normalized_event.event_id,
            message="GitHub interaction event normalized and queued successfully.",
        )
    else:
        raise HTTPException(
            status_code=500, detail="Failed to publish event to message bus."
        )
