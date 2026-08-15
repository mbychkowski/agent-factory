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

import logging
import os

logger = logging.getLogger(__name__)


from spec_engine.app.config import config


def setup_telemetry() -> str | None:
    """Configure GenAI prompt/response logging via OpenTelemetry."""
    # Keep full prompts/responses out of trace span attributes (use GenAI logging instead).
    os.environ.setdefault("ADK_CAPTURE_MESSAGE_CONTENT_IN_SPANS", "false")
    os.environ.setdefault("GOOGLE_CLOUD_AGENT_ENGINE_ENABLE_TELEMETRY", "true")

    bucket = config.logs_bucket_name
    capture_content = os.environ.get(
        "OTEL_INSTRUMENTATION_GENAI_CAPTURE_MESSAGE_CONTENT", "NO_CONTENT"
    )
    if bucket and capture_content != "false":
        logger.info(
            f"Prompt-response logging enabled - bucket: {bucket}, mode: {capture_content}"
        )
        os.environ["OTEL_INSTRUMENTATION_GENAI_CAPTURE_MESSAGE_CONTENT"] = (
            capture_content
        )
        os.environ.setdefault("OTEL_INSTRUMENTATION_GENAI_UPLOAD_FORMAT", "jsonl")
        os.environ.setdefault("OTEL_INSTRUMENTATION_GENAI_COMPLETION_HOOK", "upload")
        os.environ.setdefault(
            "OTEL_SEMCONV_STABILITY_OPT_IN", "gen_ai_latest_experimental"
        )
        commit_sha = config.commit_sha
        os.environ.setdefault(
            "OTEL_RESOURCE_ATTRIBUTES",
            f"service.namespace=agent-factory,service.version={commit_sha}",
        )
        path = config.genai_telemetry_path
        os.environ.setdefault(
            "OTEL_INSTRUMENTATION_GENAI_UPLOAD_BASE_PATH",
            f"gs://{bucket}/{path}",
        )
    else:
        logger.info(
            "Prompt-response logging disabled (set LOGS_BUCKET_NAME=your-bucket to enable)"
        )

    return bucket


def setup_agent_engine_telemetry() -> None:
    """Install the Agent Engine tracer provider (traces/logs to the customer project).

    Tags spans with the reasoningEngine resource. The OTel resource is fixed at
    provider creation, so this must run before get_fast_api_app to set the tags.
    No-op unless GOOGLE_CLOUD_AGENT_ENGINE_ENABLE_TELEMETRY is set.
    """
    if not config.enable_telemetry:
        return

    try:
        import google.auth
        from vertexai.agent_engines.templates.adk import _default_instrumentor_builder

        _, project_id = google.auth.default()
        if project_id:
            _default_instrumentor_builder(
                project_id, enable_tracing=True, enable_logging=True
            )
    except Exception as e:  # noqa: BLE001
        logger.warning("Failed to setup agent engine telemetry: %s", e)
