import os
import time
from typing import Any

from google.adk.agents.context import Context
from google.adk.tools.mcp_tool import McpToolset
from google.adk.tools.mcp_tool.mcp_session_manager import StreamableHTTPConnectionParams


from agent_engine.agents.config import config


def get_github_mcp_toolset(
    toolsets: str = "issues,repos",
    allowed_tools: list[str] | None = None,
) -> McpToolset:
    """Returns a native ADK McpToolset connected to the official Remote GitHub MCP server endpoint.

    Args:
        toolsets: Comma-separated list of GitHub MCP toolsets to enable on server side (e.g. 'issues,repos').
        allowed_tools: Exact list of function names allowed for client-side tool whitelisting.
    """
    installation_token = get_github_installation_token()
    return McpToolset(
        connection_params=StreamableHTTPConnectionParams(
            url="https://api.githubcopilot.com/mcp/",
            headers={
                "Authorization": f"Bearer {installation_token}",
                "X-MCP-Toolsets": toolsets,
                "X-MCP-Readonly": "false",
            },
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
    except Exception as e:
        print(f"[GitHub Auth Warning] Could not obtain installation token: {e}")
    return ""


def update_github_issue(
    issue_id: int, body: str, title: str | None = None, ctx: Context = None
) -> dict[str, Any]:
    """Update an existing GitHub issue's body description and/or title.

    Args:
        issue_id: The ID of the GitHub issue to update.
        body: The updated issue body markdown.
        title: Optional updated title for the issue.
    """
    print(f"[Tool: GitHub] Updating GitHub issue #{issue_id} description...")
    token = get_github_installation_token()
    if token:
        try:
            import requests

            headers = {
                "Authorization": f"Bearer {token}",
                "Accept": "application/vnd.github+json",
            }
            repo = config.github_repo
            if ctx and hasattr(ctx, "state") and isinstance(ctx.state, dict):
                issue_domain = ctx.state.get("issue")
                if isinstance(issue_domain, dict) and issue_domain.get("repo"):
                    repo = issue_domain["repo"]

            url = f"https://api.github.com/repos/{repo}/issues/{issue_id}"
            payload = {"body": body}
            if title:
                payload["title"] = title
            resp = requests.patch(url, headers=headers, json=payload, timeout=10)
            if resp.status_code in (200, 201):
                issue_data = resp.json()
                if ctx and hasattr(ctx, "state"):
                    ctx.state["user_story_markdown"] = body
                print(
                    f"[Tool: GitHub] Successfully updated description for Issue #{issue_id} in {repo}"
                )
                return {
                    "id": issue_id,
                    "status": "updated",
                    "url": issue_data.get("html_url"),
                }
            else:
                print(f"[Tool: GitHub Update Error] ({resp.status_code}): {resp.text}")
        except Exception as e:
            print(f"[Tool: GitHub Update Error] {e}")
    else:
        print("[Tool: GitHub Warning] No GitHub installation token available (check GITHUB_APP_ID and GITHUB_APP_PRIVATE_KEY). Skipping live API update.")

    return {"id": issue_id, "status": "simulated_update"}


def sync_github_issue_labels(
    issue_id: int, status_label: str, phase_label: str, ctx: Context = None
) -> dict[str, Any]:
    """Replaces agent status and phase labels on a GitHub issue to reflect active workflow state.

    Args:
        issue_id: The ID of the GitHub issue to update.
        status_label: Active status label (e.g., 'agent:in-progress', 'agent:completed').
        phase_label: Active phase label (e.g., 'phase:user-story').
        ctx: Workflow Context instance.
    """
    print(
        f"[Tool: GitHub Labels] Syncing labels for Issue #{issue_id}: status='{status_label}', phase='{phase_label}'"
    )
    token = get_github_installation_token()

    managed_status_labels = {
        "agent:in-progress",
        "agent:needs-human-lgtm",
        "agent:completed",
    }
    managed_phase_labels = {
        "phase:user-story",
    }

    if token and issue_id:
        try:
            import requests

            headers = {
                "Authorization": f"Bearer {token}",
                "Accept": "application/vnd.github+json",
            }
            repo = config.github_repo
            if ctx and hasattr(ctx, "state") and isinstance(ctx.state, dict):
                issue_domain = ctx.state.get("issue")
                if isinstance(issue_domain, dict) and issue_domain.get("repo"):
                    repo = issue_domain["repo"]

            url = f"https://api.github.com/repos/{repo}/issues/{issue_id}/labels"

            resp = requests.get(url, headers=headers, timeout=10)
            current_labels = []
            if resp.status_code == 200:
                current_labels = [
                    l["name"] if isinstance(l, dict) else str(l) for l in resp.json()
                ]

            preserved_labels = [
                lbl
                for lbl in current_labels
                if lbl not in managed_status_labels and lbl not in managed_phase_labels
            ]

            updated_labels = list(preserved_labels)
            if status_label:
                updated_labels.append(status_label)
            if phase_label:
                updated_labels.append(phase_label)

            put_resp = requests.put(
                url, headers=headers, json={"labels": updated_labels}, timeout=10
            )
            if put_resp.status_code in (200, 201):
                print(
                    f"[Tool: GitHub Labels] Successfully updated Issue #{issue_id} labels: {updated_labels}"
                )
                if ctx and hasattr(ctx, "state"):
                    ctx.state["current_status_label"] = status_label
                    ctx.state["current_phase_label"] = phase_label
                return {"id": issue_id, "status": "updated", "labels": updated_labels}
            else:
                print(
                    f"[Tool: GitHub Labels Warning] ({put_resp.status_code}): {put_resp.text}"
                )
        except Exception as e:
            print(f"[Tool: GitHub Labels Error] {e}")

    if ctx and hasattr(ctx, "state"):
        ctx.state["current_status_label"] = status_label
        ctx.state["current_phase_label"] = phase_label
    return {
        "id": issue_id,
        "status": "simulated_update",
        "status_label": status_label,
        "phase_label": phase_label,
    }



