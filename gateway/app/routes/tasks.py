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


@router.post("/tasks/execute-agent-turn", status_code=200)
async def execute_agent_turn(request: Request) -> Dict[str, Any]:
    """
    Cloud Tasks Worker Endpoint. Decodes task payload and invokes the Vertex AI
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

    if issue_id:
        thread_ref = str(uuid.uuid5(uuid.NAMESPACE_DNS, f"github.issue.{issue_id}"))
    else:
        thread_ref = str(uuid.uuid5(uuid.NAMESPACE_DNS, "github.general"))

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

    # 1b. Mark issue as in-progress immediately upon turn execution
    if issue_id:
        try:
            from agent_engine.agents.tools import sync_github_issue_labels
            sync_github_issue_labels(int(issue_id), status_label="agent:in-progress", phase_label="")
            logger.info(f"Task Worker: Marked Issue #{issue_id} as agent:in-progress at turn start.")
        except Exception as label_err:
            logger.warning(f"Task Worker: Could not set initial in-progress label on Issue #{issue_id}: {label_err}")

    # 2. Ensure session exists with session state in Vertex AI Session Service
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

            # Parse output text and tool calls from Reasoning Engine stream events
            agent_text_chunks = []
            facilitator_human_responses = []
            tool_calls_detected = False

            for line in response_text.splitlines():
                line = line.strip()
                if not line:
                    continue
                try:
                    event_data = json.loads(line)
                    if not isinstance(event_data, dict):
                        continue

                    # Check for tool/function calls in event data
                    content_dict = event_data.get("content", {})
                    if isinstance(content_dict, dict) and content_dict:
                        parts = content_dict.get("parts", [])
                        for p in parts:
                            if isinstance(p, dict):
                                if "functionCall" in p or "function_call" in p:
                                    fc = p.get("functionCall") or p.get("function_call")
                                    fc_name = fc.get("name", "") if isinstance(fc, dict) else ""
                                    if fc_name in ("add_design_comment", "create_github_issue", "update_github_issue", "create_developer_sub_issue"):
                                        logger.info(f"Task Worker: Detected tool call '{fc_name}' in stream.")
                                        tool_calls_detected = True

                    extracted_text = None
                    if isinstance(content_dict, dict) and content_dict:
                        parts = content_dict.get("parts", [])
                        for p in parts:
                            if isinstance(p, dict) and p.get("text"):
                                text_val = p["text"].strip()
                                if text_val.startswith("{") and "human_response" in text_val:
                                    try:
                                        triage_json = json.loads(text_val)
                                        if triage_json.get("human_response"):
                                            facilitator_human_responses.append(triage_json["human_response"])
                                    except Exception:
                                        pass
                                elif not text_val.startswith("{"):
                                    extracted_text = text_val
                                    break

                    if not extracted_text:
                        output_val = event_data.get("output")
                        if isinstance(output_val, str) and not output_val.startswith("{"):
                            extracted_text = output_val
                        elif isinstance(output_val, dict):
                            parts = output_val.get("parts", [])
                            for p in parts:
                                if isinstance(p, dict) and p.get("text"):
                                    text_val = p["text"].strip()
                                    if not text_val.startswith("{"):
                                        extracted_text = text_val
                                        break

                    if extracted_text:
                        if not agent_text_chunks or agent_text_chunks[-1] != extracted_text:
                            agent_text_chunks.append(extracted_text)
                except Exception:
                    pass

            active_author = "spec-deliberator-agent"
            for line in response_text.splitlines():
                line = line.strip()
                if not line:
                    continue
                try:
                    event_data = json.loads(line)
                    if isinstance(event_data, dict) and event_data.get("author"):
                        a = event_data["author"]
                        if a not in ("agile_github_planning_app", "root_workflow"):
                            active_author = a
                except Exception:
                    pass

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

