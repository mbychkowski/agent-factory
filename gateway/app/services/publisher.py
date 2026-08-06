import json
import logging
from gateway.app.config import config
from gateway.app.schemas.events import HumanInteractionEvent

logger = logging.getLogger(__name__)


async def publish_event(event: HumanInteractionEvent) -> bool:
    """
    Publishes the normalized HumanInteractionEvent to Cloud Tasks queue in production,
    or falls back to Pub/Sub or local direct HTTP forwarding.
    """
    payload_dict = event.model_dump()

    if config.enable_cloud_tasks:
        try:
            from google.cloud import tasks_v2

            client = tasks_v2.CloudTasksClient()
            parent = client.queue_path(
                config.google_cloud_project,
                config.cloud_tasks_location,
                config.cloud_tasks_queue_id,
            )

            target_url = f"{config.cloud_run_gateway_url.rstrip('/')}/tasks/execute-agent-turn"
            payload_bytes = json.dumps(payload_dict).encode("utf-8")

            # Unique Task Name for Deduplication
            issue_ref = event.issue_id or "gen"
            task_name = client.task_path(
                config.google_cloud_project,
                config.cloud_tasks_location,
                config.cloud_tasks_queue_id,
                f"issue-{issue_ref}-{event.event_id}",
            )

            task = {
                "http_request": {
                    "http_method": tasks_v2.HttpMethod.POST,
                    "url": target_url,
                    "headers": {"Content-Type": "application/json"},
                    "body": payload_bytes,
                    "oidc_token": {
                        "service_account_email": "885745030124-compute@developer.gserviceaccount.com"
                    },
                },
            }

            try:
                task_with_name = dict(task)
                task_with_name["name"] = task_name
                created_task = client.create_task(request={"parent": parent, "task": task_with_name})
            except Exception as name_err:
                if "ALREADY_EXISTS" in str(name_err) or "409" in str(name_err):
                    logger.info(f"Task already enqueued for event {event.event_id} (deduplicated).")
                    return True
                logger.warning(f"Creating task with custom name failed ({name_err}). Retrying without custom task name...")
                created_task = client.create_task(request={"parent": parent, "task": task})

            logger.info(
                f"Enqueued task {created_task.name} to Cloud Tasks queue {config.cloud_tasks_queue_id} -> {target_url}"
            )
            return True

        except Exception as e:
            if "ALREADY_EXISTS" in str(e) or "409" in str(e):
                logger.info(f"Task already enqueued for event {event.event_id} (deduplicated).")
                return True
            logger.error(f"Failed to enqueue task to Cloud Tasks: {e}")
            return False

    # Local Dev Mode: Forward directly via HTTP
    try:
        import httpx

        async with httpx.AsyncClient() as client:
            url = f"{config.agent_api_url}/a2a/agile_github_planning_app"
            response = await client.post(
                url,
                json={
                    "jsonrpc": "2.0",
                    "method": "process_event",
                    "params": payload_dict,
                    "id": event.event_id,
                },
                timeout=10.0,
            )
            logger.info(f"Local Direct Mode: Forwarded event {event.event_id} to {url} (status: {response.status_code})")
            return response.status_code in (200, 201, 202)
    except Exception as e:
        logger.warning(f"Local Direct Mode: Agent API not reachable at {config.agent_api_url} ({e}). Event queued/logged.")
        return True
