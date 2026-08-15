import os
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()
_env_path = Path(__file__).resolve().parent.parent / ".env"
if _env_path.exists():
    load_dotenv(dotenv_path=_env_path)


class AgentsConfig:
    @property
    def default_llm(self) -> str:
        return os.environ.get("DEFAULT_LLM", "gemini-3.6-flash")

    @property
    def llm_location(self) -> str:
        return os.environ.get("LLM_LOCATION", "global")

    @property
    def model(self):
        from google.adk.models import Gemini

        return Gemini(
            model=self.default_llm,
            client_kwargs={"location": self.llm_location},
        )

    @property
    def github_app_id(self) -> str:
        return os.environ.get("GITHUB_APP_ID", "")

    @property
    def github_app_installation_id(self) -> str:
        return os.environ.get("GITHUB_APP_INSTALLATION_ID", "")

    @property
    def github_app_private_key_path(self) -> str:
        raw_path = os.environ.get(
            "GITHUB_APP_PRIVATE_KEY_PATH",
            "./agent-factory-private-key.pem",
        )
        p = Path(raw_path)
        if not p.is_absolute():
            base_dir = Path(__file__).resolve().parent.parent
            p = base_dir / raw_path
        return str(p)

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
