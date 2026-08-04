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

    @property
    def cloud_tasks_queue_id(self) -> str:
        return os.environ.get("CLOUD_TASKS_QUEUE_ID", "github-agent-queue")

    @property
    def cloud_tasks_location(self) -> str:
        return os.environ.get("CLOUD_TASKS_LOCATION", "us-east1")

    @property
    def enable_cloud_tasks(self) -> bool:
        return os.environ.get("ENABLE_CLOUD_TASKS", "true").lower() in ("true", "1", "yes")

    @property
    def cloud_run_gateway_url(self) -> str:
        return os.environ.get("CLOUD_RUN_GATEWAY_URL", "https://spec-deliberator-gateway-mberhmbfsa-ue.a.run.app")

    @property
    def reasoning_engine_id(self) -> str:
        return os.environ.get("REASONING_ENGINE_ID", "projects/885745030124/locations/us-east1/reasoningEngines/4685520423255801856")

    @property
    def reasoning_engine_location(self) -> str:
        return os.environ.get("REASONING_ENGINE_LOCATION", "us-east1")


config = GatewayConfig()

