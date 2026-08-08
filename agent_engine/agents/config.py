import os
from dotenv import load_dotenv

load_dotenv()


class AgentsConfig:
    @property
    def default_llm(self) -> str:
        return os.environ.get("DEFAULT_LLM", "gemini-2.5-flash")

    @property
    def github_app_id(self) -> str:
        return os.environ.get("GITHUB_APP_ID", "")

    @property
    def github_app_installation_id(self) -> str:
        return os.environ.get("GITHUB_APP_INSTALLATION_ID", "")

    @property
    def github_app_private_key_path(self) -> str:
        return os.environ.get(
            "GITHUB_APP_PRIVATE_KEY_PATH",
            "./private-key.pem",
        )

    @property
    def github_app_private_key(self) -> str:
        return os.environ.get("GITHUB_APP_PRIVATE_KEY", "")

    @property
    def github_repo(self) -> str:
        return os.environ.get("GITHUB_REPO", "owner/repo")

    @property
    def google_cloud_project(self) -> str:
        return os.environ.get("GOOGLE_CLOUD_PROJECT", "")

    @property
    def google_cloud_location(self) -> str:
        return os.environ.get("GOOGLE_CLOUD_LOCATION", "us-east1")


config = AgentsConfig()
