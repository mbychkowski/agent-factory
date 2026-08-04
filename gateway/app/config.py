import os


class GatewayConfig:
    @property
    def github_webhook_secret(self) -> str:
        return os.environ.get("GITHUB_WEBHOOK_SECRET", "dev_secret_change_me")

    @property
    def google_cloud_project(self) -> str:
        return os.environ.get("GOOGLE_CLOUD_PROJECT", os.environ.get("GCP_PROJECT_ID", "default_project"))

    @property
    def pubsub_topic_id(self) -> str:
        return os.environ.get("PUBSUB_TOPIC_ID", "github-human-events")

    @property
    def enable_pubsub(self) -> bool:
        return os.environ.get("ENABLE_PUBSUB", "false").lower() in ("true", "1", "yes")

    @property
    def agent_api_url(self) -> str:
        return os.environ.get("AGENT_API_URL", "http://localhost:8000")


config = GatewayConfig()
