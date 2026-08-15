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

"""Serve the reasoning_engine ``{class_method, input}`` contract over HTTP.

Exists to guarantee support for the Vertex AI Console Playground and Gemini
Enterprise (via ADK registration), which both invoke the engine through this
contract. Agent Engine forwards calls to ``/api/reasoning_engine`` (sync) and
``/api/stream_reasoning_engine`` (streaming); dispatch is limited to the
:class:`AdkApp` ``register_operations()`` methods so the wire output matches a
packaged Agent Engine.
"""

import inspect
import json
import logging

from agent_engine.app.app_utils import services
from fastapi import FastAPI, HTTPException, Request, encoders, responses
from vertexai.agent_engines.templates.adk import AdkApp

logger = logging.getLogger(__name__)


def attach_reasoning_engine_routes(app: FastAPI) -> None:
    """Register reasoning_engine routes that dispatch to an AdkApp."""
    runtime: AdkApp | None = None
    streaming_methods: set[str] = set()
    sync_methods: set[str] = set()

    def get_runtime() -> AdkApp:
        nonlocal runtime, streaming_methods, sync_methods
        if runtime is None:
            from agent_engine.app.agent import app as adk_app

            # Reuse the process-wide services so sessions created here are
            # visible to the adk_api and A2A paths, and vice versa (see services.py).
            runtime = AdkApp(
                app=adk_app,
                session_service_builder=services.get_session_service,
                artifact_service_builder=services.get_artifact_service,
            )
            runtime.set_up()
            operations = runtime.register_operations()
            streaming_methods = set(operations.get("stream", [])) | set(
                operations.get("async_stream", [])
            )
            sync_methods = set(operations.get("", [])) | set(
                operations.get("async", [])
            )
        return runtime

    def resolve_method(class_method: str, *, streaming: bool):
        rt = get_runtime()
        # Map query/async_query aliases to stream_query/async_stream_query
        if (
            class_method in ("query", "async_query")
            and class_method not in sync_methods
        ):
            class_method = (
                "async_stream_query"
                if "async_stream_query" in streaming_methods
                else "stream_query"
            )
            streaming = True

        allowed = streaming_methods if streaming else sync_methods
        if class_method not in allowed:
            raise HTTPException(
                status_code=404,
                detail=f"Unsupported reasoning_engine method: {class_method!r}",
            )
        return getattr(rt, class_method)

    @app.post("/api/stream_reasoning_engine")
    async def stream_query(request: Request) -> responses.StreamingResponse:
        body = await request.json()
        method = resolve_method(
            body.get("class_method", "stream_query"), streaming=True
        )

        async def generator():
            async for event in method(**(body.get("input") or {})):
                yield json.dumps(encoders.jsonable_encoder(event)) + "\n"

        return responses.StreamingResponse(
            content=generator(), media_type="application/json"
        )

    @app.post("/api/reasoning_engine")
    async def query(request: Request) -> responses.Response:
        body = await request.json()
        class_method = body.get("class_method", "")
        kwargs = body.get("input") or {}

        if class_method in (
            "query",
            "async_query",
            "stream_query",
            "async_stream_query",
        ):
            method = resolve_method(class_method, streaming=True)
            output_events = []
            async for event in method(**kwargs):
                output_events.append(event)
            return responses.JSONResponse(
                content=encoders.jsonable_encoder(
                    {"output": output_events[-1] if output_events else {}}
                )
            )

        method = resolve_method(class_method, streaming=False)
        try:
            output = (
                await method(**kwargs)
                if inspect.iscoroutinefunction(method)
                else method(**kwargs)
            )
            return responses.JSONResponse(
                content=encoders.jsonable_encoder({"output": output})
            )
        except Exception as err:
            err_str = str(err)
            if "already exists" in err_str or "400" in err_str:
                logger.info(f"Session initialization notice: {err_str}")
                return responses.JSONResponse(
                    content=encoders.jsonable_encoder(
                        {
                            "output": {
                                "session_id": kwargs.get("session_id"),
                                "status": "already_exists",
                            }
                        }
                    )
                )
            raise
