import os
import time
from typing import Any

from google.adk.agents.context import Context
from google.adk.tools.mcp_tool import McpToolset
from google.adk.tools.mcp_tool.mcp_session_manager import StreamableHTTPConnectionParams

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
) -> McpToolset:
    """Returns a native ADK McpToolset connected to the official Remote GitHub MCP server endpoint.

    Args:
        toolsets: Comma-separated list of GitHub MCP toolsets to enable on server side (e.g. 'issues,repos').
        allowed_tools: Exact list of function names allowed for client-side tool whitelisting.
    """
    return McpToolset(
        connection_params=StreamableHTTPConnectionParams(
            url="https://api.githubcopilot.com/mcp/",
            headers=DynamicAuthHeaders(toolsets=toolsets),
        ),
        tool_filter=allowed_tools,
    )


def get_github_installation_token() -> str:
    """Acquires a short-lived GitHub App Installation Access Token."""
    app_id = config.github_app_id
    installation_id = config.github_app_installation_id
    pem_path = config.github_app_private_key_path
    pem_string = config.github_app_private_key

    private_key_str = ""
    if pem_string:
        private_key_str = pem_string.replace("\\n", "\n")
    elif os.path.exists(pem_path):
        with open(pem_path, "r", encoding="utf-8") as f:
            private_key_str = f.read()

    if not private_key_str or not app_id or not installation_id:
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


def update_github_issue(
    issue_id: int, body: str, title: str | None = None, ctx: Context = None
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
