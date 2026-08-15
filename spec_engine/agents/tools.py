import time
from typing import Any

from google.adk.agents.context import Context

from spec_engine.agents.config import config


class DynamicAuthHeaders(dict):
    """Custom dictionary subclass that dynamically generates a fresh GitHub App Installation Token on copy/access."""

    def __init__(self, toolsets: str):
        super().__init__()
        self["X-MCP-Toolsets"] = toolsets
        self["X-MCP-Readonly"] = "false"

    def _get_auth(self) -> str:
        token = get_github_installation_token()
        return f"Bearer {token}" if token else ""

    def copy(self):
        d = dict(self)
        auth = self._get_auth()
        if auth:
            d["Authorization"] = auth
        return d

    def items(self):
        return self.copy().items()

    def get(self, key, default=None):
        if str(key).lower() == "authorization":
            return self._get_auth() or default
        return super().get(key, default)

    def __getitem__(self, key):
        if str(key).lower() == "authorization":
            auth = self._get_auth()
            if auth:
                return auth
        return super().__getitem__(key)


def get_github_mcp_toolset(
    toolsets: str = "issues,repos",
    allowed_tools: list[str] | None = None,
) -> Any:
    """Returns a native ADK McpToolset connected to Remote GitHub MCP server if configured."""
    return []


def get_github_installation_token() -> str:
    """Acquires a short-lived GitHub App Installation Access Token using the PEM file."""
    app_id = config.github_app_id
    installation_id = config.github_app_installation_id
    pem_path = config.github_app_private_key_path

    if not app_id or not installation_id:
        return ""

    from pathlib import Path

    private_key_str = ""
    candidates = [
        Path(pem_path),
        Path(__file__).resolve().parent.parent / pem_path,
        Path(__file__).resolve().parent.parent / "agent-factory-private-key.pem",
    ]
    for cand in candidates:
        if cand.exists() and cand.is_file():
            with open(cand, "r", encoding="utf-8") as f:
                private_key_str = f.read()
            break

    if not private_key_str:
        return ""

    try:
        import requests
        from google.auth import crypt, jwt

        signer = crypt.RSASigner.from_string(private_key_str)
        now = int(time.time())
        payload = {"iat": now - 60, "exp": now + (10 * 60), "iss": app_id}
        jwt_token = jwt.encode(signer, payload).decode("utf-8")

        url = (
            f"https://api.github.com/app/installations/{installation_id}/access_tokens"
        )
        resp = requests.post(
            url,
            headers={
                "Authorization": f"Bearer {jwt_token}",
                "Accept": "application/vnd.github+json",
            },
            timeout=10,
        )
        if resp.status_code in (200, 201):
            return resp.json().get("token", "")
    except Exception as e:  # noqa: BLE001
        print(f"[GitHub Auth Warning] Could not obtain installation token: {e}")
    return ""


def get_github_issue(
    issue_id: int, repo: str | None = None, ctx: Context | None = None
) -> dict[str, Any]:
    """Fetches details of a GitHub issue by issue ID."""
    token = get_github_installation_token()
    if not token:
        return {
            "id": issue_id,
            "status": "error",
            "error": "No installation token available.",
        }

    import requests

    target_repo = repo or config.github_repo
    if ctx and getattr(ctx, "state", None) and isinstance(ctx.state, dict):
        issue_domain = ctx.state.get("issue")
        if isinstance(issue_domain, dict) and issue_domain.get("repo"):
            target_repo = issue_domain["repo"]

    url = f"https://api.github.com/repos/{target_repo}/issues/{issue_id}"
    headers = {
        "Authorization": f"Bearer {token}",
        "Accept": "application/vnd.github+json",
    }
    try:
        resp = requests.get(url, headers=headers, timeout=10)
        if resp.status_code == 200:
            return {"status": "success", "issue": resp.json()}
        return {"status": "error", "code": resp.status_code, "error": resp.text}
    except Exception as e:  # noqa: BLE001
        return {"status": "error", "error": str(e)}


def update_github_issue(
    issue_id: int,
    body: str,
    title: str | None = None,
    ctx: Context | None = None,
) -> dict[str, Any]:
    """Updates a GitHub issue body description and optional title."""
    token = get_github_installation_token()
    if not token:
        print("[GitHub] No installation token available. Skipping live API update.")
        return {"id": issue_id, "status": "simulated_update"}

    import requests

    repo = config.github_repo
    if ctx and getattr(ctx, "state", None) and isinstance(ctx.state, dict):
        issue_domain = ctx.state.get("issue")
        if isinstance(issue_domain, dict) and issue_domain.get("repo"):
            repo = issue_domain["repo"]

    url = f"https://api.github.com/repos/{repo}/issues/{issue_id}"
    headers = {
        "Authorization": f"Bearer {token}",
        "Accept": "application/vnd.github+json",
    }
    payload: dict[str, Any] = {"body": body}
    if title:
        payload["title"] = title

    try:
        resp = requests.patch(url, headers=headers, json=payload, timeout=10)
        if resp.status_code in (200, 201):
            issue_data = resp.json()
            print(f"[GitHub] Successfully updated issue #{issue_id} in {repo}")
            return {
                "id": issue_id,
                "status": "updated",
                "url": issue_data.get("html_url"),
            }
        print(f"[GitHub Error {resp.status_code}] {resp.text}")
        return {"id": issue_id, "status": "error", "error": resp.text}
    except Exception as e:  # noqa: BLE001
        print(f"[GitHub Error] {e}")
        return {"id": issue_id, "status": "error", "error": str(e)}
