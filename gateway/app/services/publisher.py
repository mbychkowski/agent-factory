import json
import logging
from gateway.app.config import config
from gateway.app.schemas.events import HumanInteractionEvent

logger = logging.getLogger(__name__)


async def publish_event(event: HumanInteractionEvent) -> bool:
    """
    Publishes the normalized HumanInteractionEvent to GCP Pub/Sub in production,
    or forwards directly to the Agent API in local dev mode.
    """
    payload_dict = event.model_dump()

    if config.enable_pubsub:
        try:
            from google.cloud import pubsub_v1

            publisher = pubsub_v1.PublisherClient()
            topic_path = publisher.topic_path(config.google_cloud_project, config.pubsub_topic_id)
            data = json.dumps(payload_dict).encode("utf-8")

            future = publisher.publish(topic_path, data=data, event_type=event.interaction_type.value)
            message_id = future.result(timeout=5.0)
            logger.info(f"Published event {event.event_id} to Pub/Sub topic {config.pubsub_topic_id}, msg_id: {message_id}")
            return True
        except Exception as e:
            logger.error(f"Failed to publish to Pub/Sub: {e}")
            return False
    else:
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
