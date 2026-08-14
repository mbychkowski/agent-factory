import os
from dotenv import load_dotenv

load_dotenv()


class AppConfig:
    @property
    def allow_origins(self) -> list[str]:
        origins = os.environ.get("ALLOW_ORIGINS", "")
        return [o.strip() for o in origins.split(",") if o.strip()]

    @property
    def session_service_uri(self) -> str | None:
        return os.environ.get("SESSION_SERVICE_URI")

    @property
    def google_cloud_agent_engine_id(self) -> str | None:
        return os.environ.get("GOOGLE_CLOUD_AGENT_ENGINE_ID")

    @property
    def google_cloud_project(self) -> str | None:
        return os.environ.get("GOOGLE_CLOUD_PROJECT")

    @property
    def google_cloud_location(self) -> str:
        return os.environ.get("GOOGLE_CLOUD_LOCATION", "us-east1")

    @property
    def logs_bucket_name(self) -> str | None:
        return os.environ.get("LOGS_BUCKET_NAME")

    @property
    def agent_version(self) -> str:
        return os.environ.get("AGENT_VERSION", "0.1.0")

    @property
    def app_url(self) -> str | None:
        return os.environ.get("APP_URL")

    @property
    def enable_telemetry(self) -> bool:
        return os.environ.get(
            "GOOGLE_CLOUD_AGENT_ENGINE_ENABLE_TELEMETRY", "true"
        ).lower() in ("true", "1", "yes")

    @property
    def capture_message_content_in_spans(self) -> bool:
        return os.environ.get(
            "ADK_CAPTURE_MESSAGE_CONTENT_IN_SPANS", "true"
        ).lower() in ("true", "1", "yes")

    @property
    def commit_sha(self) -> str:
        return os.environ.get("COMMIT_SHA", "dev")

    @property
    def genai_telemetry_path(self) -> str:
        return os.environ.get("GENAI_TELEMETRY_PATH", "completions")


config = AppConfig()
