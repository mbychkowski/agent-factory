import logging
import uuid
from typing import Any

import google.auth
import google.auth.transport.requests
import httpx
from fastapi import APIRouter, HTTPException, Request

from surface_gateway.app.config import config

logger = logging.getLogger(__name__)

router = APIRouter()


@router.post("/tasks/execute-agent-turn", status_code=200)
async def execute_agent_turn(request: Request) -> dict[str, Any]:
    """Cloud Tasks Worker Endpoint. Decodes task payload and invokes the Vertex AI

    Reasoning Engine agent via its official REST API.
    """
    try:
        payload: dict[str, Any] = await request.json()
    except Exception:  # noqa: BLE001
        raise HTTPException(status_code=400, detail="Invalid JSON payload")

    event_id = payload.get("event_id")
    interaction_type = payload.get("interaction_type")
    content_text = payload.get("content", "")
    issue_id = payload.get("issue_id")
    actor_info = payload.get("actor")
    user_id = (
        actor_info.get("user_id", "github_user")
        if isinstance(actor_info, dict)
        else "github_user"
    )

    thread_ref = (
        str(uuid.uuid5(uuid.NAMESPACE_DNS, f"github.issue.{issue_id}"))
        if issue_id
        else str(uuid.uuid5(uuid.NAMESPACE_DNS, "github.general"))
    )

    logger.info(
        f"Task Worker: Executing agent turn for event {event_id} on session {thread_ref}"
    )

    # 1. Obtain Google Cloud Auth Bearer Token
    try:
        credentials, _project = google.auth.default(
            scopes=["https://www.googleapis.com/auth/cloud-platform"]
        )
        auth_request = google.auth.transport.requests.Request()
        credentials.refresh(auth_request)
        bearer_token = credentials.token
    except Exception as e:  # noqa: BLE001
        logger.error(f"Failed to refresh GCP credentials: {e}")
        raise HTTPException(status_code=500, detail="Authentication failed")

    headers = {
        "Authorization": f"Bearer {bearer_token}",
        "Content-Type": "application/json",
    }

    from surface_gateway.app.schemas.state import AgentSessionState, IssueMetadata

    # Ensure session exists with session state in Vertex AI Session Service
    engine_resource = config.reasoning_engine_id
    engine_location = config.reasoning_engine_location
    query_url = f"https://{engine_location}-aiplatform.googleapis.com/v1/{engine_resource}:query"
    parsed_issue_id = int(issue_id) if issue_id else None
    raw_payload_dict = (
        payload.get("raw_payload")
        if isinstance(payload.get("raw_payload"), dict)
        else {}
    )
    repo_dict = raw_payload_dict.get("repository")
    repo_full_name = repo_dict.get("full_name") if isinstance(repo_dict, dict) else None

    session_state = AgentSessionState(
        parent_issue_id=parsed_issue_id,
        issue=IssueMetadata(id=parsed_issue_id, repo=repo_full_name)
        if parsed_issue_id
        else IssueMetadata(repo=repo_full_name),
    )

    create_session_body = {
        "class_method": "async_create_session",
        "input": {
            "user_id": user_id,
            "session_id": thread_ref,
            "state": session_state.model_dump(),
        },
    }

    http_client: httpx.AsyncClient | None = getattr(
        getattr(request, "app", None), "state", None
    ) and getattr(request.app.state, "http_client", None)

    try:
        if http_client is not None:
            session_resp = await http_client.post(
                query_url, json=create_session_body, headers=headers, timeout=15.0
            )
        else:
            async with httpx.AsyncClient(timeout=15.0) as client:
                session_resp = await client.post(
                    query_url, json=create_session_body, headers=headers
                )
        logger.info(
            f"Task Worker: Session initialization status {session_resp.status_code}"
        )
    except Exception as e:  # noqa: BLE001
        logger.warning(f"Task Worker: Session creation check warning: {e}")

    from surface_gateway.app.utils.prompts import build_agent_interaction_prompt

    raw_payload = payload.get("raw_payload", {})
    prompt = build_agent_interaction_prompt(
        interaction_type=str(interaction_type or "COMMENT"),
        content_text=content_text,
        issue_id=parsed_issue_id,
        raw_payload=raw_payload if isinstance(raw_payload, dict) else {},
    )

    request_body = {
        "class_method": "async_stream_query",
        "input": {
            "user_id": user_id,
            "session_id": thread_ref,
            "message": prompt,
        },
    }

    logger.info(
        f"Task Worker: Calling Reasoning Engine at {query_url} with prompt:\n{prompt}"
    )

    try:
        if http_client is not None:
            response = await http_client.post(
                query_url, json=request_body, headers=headers, timeout=600.0
            )
        else:
            async with httpx.AsyncClient(timeout=600.0) as client:
                response = await client.post(query_url, json=request_body, headers=headers)
        if response.status_code not in (200, 201):
            logger.error(
                f"Reasoning Engine returned error status {response.status_code}: {response.text}"
            )
            raise HTTPException(
                status_code=502, detail=f"Reasoning Engine error: {response.text}"
            )

        response_text = response.text
        output_preview = response_text[:1000]
        logger.info(
            f"Task Worker: Reasoning Engine output preview ({len(response_text)} bytes):\n{output_preview}"
        )
        logger.info(
            f"Task Worker: Successfully executed turn for event {event_id}."
        )
        return {
            "status": "completed",
            "event_id": event_id,
            "session_id": thread_ref,
            "output_preview": output_preview,
        }

    except HTTPException:
        raise
    except Exception as e:  # noqa: BLE001
        logger.error(f"Task Worker: Failed during Reasoning Engine execution: {e}")
        raise HTTPException(status_code=500, detail=str(e))
