# Copyright 2026 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     https://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import asyncio
import base64
import contextlib
import json
import os
from collections.abc import AsyncIterator

from typing import Any

import google.auth
from a2a.server.tasks import InMemoryTaskStore
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException, Request
from google.adk.cli.fast_api import get_fast_api_app
from google.adk.runners import Runner
from google.cloud import logging as google_cloud_logging

from agent_engine.app.app_utils import services
from agent_engine.app.app_utils.a2a import attach_a2a_routes
from agent_engine.app.app_utils.reasoning_engine_adapter import (
    attach_reasoning_engine_routes,
)
from agent_engine.app.app_utils.telemetry import (
    setup_agent_engine_telemetry,
    setup_telemetry,
)
from agent_engine.app.app_utils.typing import Feedback

load_dotenv()
setup_telemetry()
# Must run before get_fast_api_app to set the tracer provider resource.
setup_agent_engine_telemetry()
_, project_id = google.auth.default()
logging_client = google_cloud_logging.Client()
logger = logging_client.logger(__name__)
allow_origins = (
    os.getenv("ALLOW_ORIGINS", "").split(",") if os.getenv("ALLOW_ORIGINS") else None
)

AGENT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


@contextlib.asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    # Runner for the A2A path, sharing the same session/artifact services as the
    # adk_api and reasoning_engine paths (see services.py). Imported here so the
    # agent is built after env/telemetry setup.
    from agent_engine.app.agent import app as adk_app
    from agent_engine.app.agent import root_agent

    runner = Runner(
        app=adk_app,
        session_service=services.get_session_service(),
        artifact_service=services.get_artifact_service(),
        auto_create_session=True,
    )
    # Shared by the A2A path and the reasoning_engine adapter routes.
    app.state.runner = runner
    app.state.agent_app_name = adk_app.name
    await attach_a2a_routes(
        app,
        agent=root_agent,
        runner=runner,
        task_store=InMemoryTaskStore(),
        rpc_path=f"/a2a/{adk_app.name}",
    )
    yield


app: FastAPI = get_fast_api_app(
    agents_dir=AGENT_DIR,
    web=True,
    artifact_service_uri=services.ARTIFACT_SERVICE_URI,
    allow_origins=allow_origins,
    session_service_uri=services.SESSION_SERVICE_URI,
    otel_to_cloud=False,
    lifespan=lifespan,
)
app.title = "agent-factory"
app.description = "API for interacting with the Agent agent-factory"


# Proxy routes so the Vertex AI Console Playground (reasoning_engine SDK) can
# talk to this agent alongside the native adk_api routes.
attach_reasoning_engine_routes(app)


@app.post("/feedback")
def collect_feedback(feedback: Feedback) -> dict[str, str]:
    """Collect and log feedback.

    Args:
        feedback: The feedback data to log

    Returns:
        Success message
    """
    logger.log_struct(feedback.model_dump(), severity="INFO")
    return {"status": "success"}


@app.post("/pubsub/push")
async def handle_pubsub_push(request: Request) -> dict[str, Any]:
    """Pub/Sub Push Endpoint. Decodes incoming Pub/Sub envelope data,
    extracts the HumanInteractionEvent, and invokes the ADK runner.
    """
    try:
        body = await request.json()
        message = body.get("message", {})
        data_b64 = message.get("data")
        if not data_b64:
            raise HTTPException(status_code=400, detail="Missing message.data in Pub/Sub push payload")

        raw_payload = json.loads(base64.b64decode(data_b64).decode("utf-8"))
        logger.log_struct(
            {
                "event": "pubsub_push_received",
                "event_id": raw_payload.get("event_id"),
                "interaction_type": raw_payload.get("interaction_type"),
            },
            severity="INFO",
        )

        runner: Runner | None = getattr(app.state, "runner", None)
        if runner:
            content_text = raw_payload.get("content", "")
            issue_id = raw_payload.get("issue_id")
            thread_ref = raw_payload.get("thread_ref") or (f"github:issue:{issue_id}" if issue_id else "github:general")

            from google.genai import types
            new_message = types.Content(
                parts=[
                    types.Part(
                        text=f"Received GitHub human interaction event ({raw_payload.get('interaction_type')}):\n\n{content_text}"
                    )
                ]
            )

            asyncio.create_task(
                runner.run_async(
                    user_id=raw_payload.get("actor", {}).get("user_id", "github_user"),
                    session_id=thread_ref,
                    new_message=new_message,
                )
            )

        return {"status": "accepted", "event_id": raw_payload.get("event_id")}
    except Exception as e:
        logger.log_struct({"event": "pubsub_push_error", "error": str(e)}, severity="ERROR")
        raise HTTPException(status_code=500, detail=str(e))


# Main execution
if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
