import json
import logging
import uuid
from typing import Any, Dict
import google.auth
import google.auth.transport.requests
from fastapi import APIRouter, HTTPException, Request
import httpx

from gateway.app.config import config

logger = logging.getLogger(__name__)

router = APIRouter()


GITHUB_ACTION_TOOLS = {
    "add_design_comment",
    "create_github_issue",
    "update_github_issue",
    "create_developer_sub_issue",
}


def _parse_stream_response(response_text: str) -> tuple[list[str], list[str], bool, str]:
    """Parses streaming events to extract text chunks, facilitator responses, tool call flags, and author."""
    agent_text_chunks = []
    facilitator_responses = []
    tool_calls_detected = False
    active_author = "spec-deliberator-agent"

    for line in response_text.splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            event = json.loads(line)
            if not isinstance(event, dict):
                continue

            author = event.get("author")
            if author and author not in ("agile_github_planning_app", "root_workflow"):
                active_author = author

            parts = []
            if isinstance(event.get("content"), dict):
                parts = event["content"].get("parts", [])
            elif isinstance(event.get("output"), dict):
                parts = event["output"].get("parts", [])

            extracted_text = None
            for p in parts:
                if not isinstance(p, dict):
                    continue

                fc = p.get("functionCall") or p.get("function_call")
                if isinstance(fc, dict) and fc.get("name") in GITHUB_ACTION_TOOLS:
                    tool_calls_detected = True

                text = p.get("text", "").strip()
                if text:
                    if text.startswith("{") and "human_response" in text:
                        try:
                            if hr := json.loads(text).get("human_response"):
                                facilitator_responses.append(hr)
                        except Exception:
                            pass
                    elif not text.startswith("{"):
                        extracted_text = text

            if not extracted_text and isinstance(event.get("output"), str):
                out_str = event["output"].strip()
                if not out_str.startswith("{"):
                    extracted_text = out_str

            if extracted_text and (not agent_text_chunks or agent_text_chunks[-1] != extracted_text):
                agent_text_chunks.append(extracted_text)

        except Exception:
            pass

    return agent_text_chunks, facilitator_responses, tool_calls_detected, active_author


@router.post("/tasks/execute-agent-turn", status_code=200)
async def execute_agent_turn(request: Request) -> Dict[str, Any]:
    """Cloud Tasks Worker Endpoint. Decodes task payload and invokes the Vertex AI

    Reasoning Engine agent via its official REST API.
    """
    try:
        payload: Dict[str, Any] = await request.json()
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid JSON payload")

    event_id = payload.get("event_id")
    interaction_type = payload.get("interaction_type")
    content_text = payload.get("content", "")
    issue_id = payload.get("issue_id")
    actor_info = payload.get("actor", {})
    user_id = actor_info.get("user_id", "github_user") if isinstance(actor_info, dict) else "github_user"

    thread_ref = (
        str(uuid.uuid5(uuid.NAMESPACE_DNS, f"github.issue.{issue_id}"))
        if issue_id
        else str(uuid.uuid5(uuid.NAMESPACE_DNS, "github.general"))
    )

    logger.info(f"Task Worker: Executing agent turn for event {event_id} on session {thread_ref}")

    # 1. Obtain Google Cloud Auth Bearer Token
    try:
        credentials, project = google.auth.default(
            scopes=["https://www.googleapis.com/auth/cloud-platform"]
        )
        auth_request = google.auth.transport.requests.Request()
        credentials.refresh(auth_request)
        bearer_token = credentials.token
    except Exception as e:
        logger.error(f"Failed to refresh GCP credentials: {e}")
        raise HTTPException(status_code=500, detail="Authentication failed")

    # 2. Construct Vertex AI Reasoning Engine streamQuery URL
    engine_resource = config.reasoning_engine_id
    url = f"https://us-east1-aiplatform.googleapis.com/v1/{engine_resource}:streamQuery"

    headers = {
        "Authorization": f"Bearer {bearer_token}",
        "Content-Type": "application/json",
    }

    if issue_id:
        try:
            from agent_engine.agents.tools import sync_github_issue_labels
            sync_github_issue_labels(int(issue_id), status_label="agent:in-progress", phase_label="")
            logger.info(f"Task Worker: Marked Issue #{issue_id} as agent:in-progress at turn start.")
        except Exception as label_err:
            logger.warning(f"Task Worker: Could not set initial in-progress label on Issue #{issue_id}: {label_err}")

    # Ensure session exists with session state in Vertex AI Session Service
    query_url = f"https://us-east1-aiplatform.googleapis.com/v1/{engine_resource}:query"
    create_session_body = {
        "class_method": "async_create_session",
        "input": {
            "user_id": user_id,
            "session_id": thread_ref,
            "state": {"parent_issue_id": int(issue_id) if issue_id else None},
        },
    }

    try:
        async with httpx.AsyncClient(timeout=15.0) as client:
            session_resp = await client.post(query_url, json=create_session_body, headers=headers)
            logger.info(f"Task Worker: Session initialization status {session_resp.status_code}")
    except Exception as e:
        logger.warning(f"Task Worker: Session creation check warning: {e}")

    raw_payload = payload.get("raw_payload", {})
    issue_data = raw_payload.get("issue", {}) if isinstance(raw_payload, dict) else {}
    issue_title = issue_data.get("title", "") if isinstance(issue_data, dict) else ""

    issue_context_str = f"Issue #{issue_id} ({issue_title})" if issue_title else f"Issue #{issue_id}"

    prompt = (
        f"Received GitHub human interaction event on {issue_context_str} ({interaction_type}):\n\n"
        f"{content_text}\n\n"
        f"[Context: Target Issue = {issue_context_str}. Please use add_design_comment or create_developer_sub_issue to update GitHub Issue #{issue_id}.]\n"
        f"[Instruction: Focus strictly on the topic and requirements of {issue_context_str}. Do NOT mix in requirements from unrelated topics or other issues like authentication or database specs.]"
        if issue_id
        else f"Received GitHub interaction event ({interaction_type}):\n\n{content_text}"
    )

    request_body = {
        "class_method": "async_stream_query",
        "input": {
            "user_id": user_id,
            "session_id": thread_ref,
            "message": prompt,
        },
    }

    logger.info(f"Task Worker: Calling Reasoning Engine at {url} with prompt:\n{prompt}")

    try:
        async with httpx.AsyncClient(timeout=120.0) as client:
            async with client.stream("POST", url, json=request_body, headers=headers) as response:
                if response.status_code not in (200, 201):
                    error_bytes = await response.aread()
                    error_msg = error_bytes.decode("utf-8", errors="replace")
                    logger.error(f"Reasoning Engine returned error status {response.status_code}: {error_msg}")
                    raise HTTPException(status_code=502, detail=f"Reasoning Engine error: {error_msg}")

                raw_bytes = await response.aread()
                response_text = raw_bytes.decode("utf-8", errors="replace")

            output_preview = response_text[:1000]
            logger.info(f"Task Worker: Reasoning Engine output preview ({len(raw_bytes)} bytes):\n{output_preview}")

            agent_text_chunks, facilitator_human_responses, tool_calls_detected, active_author = (
                _parse_stream_response(response_text)
            )

            raw_comment = ""
            if facilitator_human_responses:
                raw_comment = "\n\n".join(facilitator_human_responses).strip()
            elif not tool_calls_detected and agent_text_chunks:
                raw_comment = "\n\n".join(agent_text_chunks).strip()

            comment_body = f"commentor: {active_author}\n\n{raw_comment}" if raw_comment else ""

            posted = False
            if issue_id and comment_body and not tool_calls_detected:
                from gateway.app.utils.github_commenter import post_agent_github_comment
                logger.info(f"Task Worker: Posting agent response ({len(comment_body)} bytes) to Issue #{issue_id}...")
                posted = post_agent_github_comment(int(issue_id), comment_body)
            elif tool_calls_detected:
                logger.info(f"Task Worker: Tool call handled GitHub interaction directly. Suppressed duplicate comment post on Issue #{issue_id}.")

            logger.info(f"Task Worker: Successfully executed turn for event {event_id}. Posted comment: {posted}")
            return {
                "status": "completed",
                "event_id": event_id,
                "session_id": thread_ref,
                "output_preview": output_preview,
                "posted_comment": posted,
            }


    except Exception as e:
        logger.error(f"Task Worker: Failed during Reasoning Engine execution: {e}")
        raise HTTPException(status_code=500, detail=str(e))

