import os
import time
from typing import Any, Dict, List
from google.adk.agents.context import Context

# Mock fallback databases
MOCK_LOCAL_REQUIREMENTS = [
    {
        "id": "prd-1",
        "title": "Legacy Authentication Service",
        "content": "The system utilizes standard JWT tokens for session management.",
        "similarity": 0.92,
    }
]

MOCK_LOCAL_CODEBASE_FILES = [
    {
        "filepath": "agent_engine/agents/agent.py",
        "content": "# Root multi-agent workflow definition",
        "dependencies": []
    }
]


def get_github_installation_token() -> str:
    """Acquires a short-lived GitHub App Installation Access Token."""
    app_id = os.getenv("GITHUB_APP_ID")
    installation_id = os.getenv("GITHUB_APP_INSTALLATION_ID")
    pem_path = os.getenv("GITHUB_APP_PRIVATE_KEY_PATH", "./agent-factory-spec-deliberator.2026-08-04.private-key.pem")
    pem_string = os.getenv("GITHUB_APP_PRIVATE_KEY")

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

        url = f"https://api.github.com/app/installations/{installation_id}/access_tokens"
        resp = requests.post(
            url,
            headers={"Authorization": f"Bearer {jwt_token}", "Accept": "application/vnd.github+json"},
            timeout=10,
        )
        if resp.status_code in (200, 201):
            return resp.json().get("token", "")
    except Exception as e:
        print(f"[GitHub Auth Warning] Could not obtain installation token: {e}")
    return ""


def search_local_requirements(query: str, ctx: Context) -> List[Dict[str, Any]]:
    """Search the local workspace or repository for historical PRDs, Epics, Features, or User Stories.

    Args:
        query: Search term or semantic query to find related requirements.
    """
    print(f"[Tool: Local Requirements] Searching for '{query}'...")
    return MOCK_LOCAL_REQUIREMENTS


def create_github_issue(title: str, body: str, ctx: Context) -> Dict[str, Any]:
    """Create a parent user story issue on GitHub.

    Args:
        title: The title of the issue.
        body: The comprehensive user story markdown body.
    """
    print(f"[Tool: GitHub] Creating parent issue: '{title}'")
    token = get_github_installation_token()
    if token:
        try:
            import requests

            headers = {"Authorization": f"Bearer {token}", "Accept": "application/vnd.github+json"}
            repo = os.getenv("GITHUB_REPO", "mbychkowski/agent-factory")
            url = f"https://api.github.com/repos/{repo}/issues"
            resp = requests.post(url, headers=headers, json={"title": title, "body": body}, timeout=10)
            if resp.status_code in (200, 201):
                issue_data = resp.json()
                issue_id = issue_data.get("number")
                ctx.state["parent_issue_id"] = issue_id
                ctx.state["user_story_markdown"] = body
                print(f"[Tool: GitHub] Created real GitHub issue #{issue_id} in {repo}")
                return {"id": issue_id, "title": title, "status": "open", "url": issue_data.get("html_url")}
        except Exception as e:
            print(f"[Tool: GitHub Issue Creation Error] {e}")

    # Fallback to local state if offline/mock
    issue_id = ctx.state.get("parent_issue_id", 100)
    ctx.state["parent_issue_id"] = issue_id
    ctx.state["user_story_markdown"] = body
    print(f"[Tool: GitHub] Saved parent issue #{issue_id} to session state")
    return {"id": issue_id, "title": title, "status": "open"}


def update_github_issue(issue_id: int, body: str, title: str = None, ctx: Context = None) -> Dict[str, Any]:
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

            headers = {"Authorization": f"Bearer {token}", "Accept": "application/vnd.github+json"}
            repo = os.getenv("GITHUB_REPO", "mbychkowski/agent-factory")
            url = f"https://api.github.com/repos/{repo}/issues/{issue_id}"
            payload = {"body": body}
            if title:
                payload["title"] = title
            resp = requests.patch(url, headers=headers, json=payload, timeout=10)
            if resp.status_code in (200, 201):
                issue_data = resp.json()
                if ctx and hasattr(ctx, "state"):
                    ctx.state["user_story_markdown"] = body
                print(f"[Tool: GitHub] Successfully updated description for Issue #{issue_id} in {repo}")
                return {"id": issue_id, "status": "updated", "url": issue_data.get("html_url")}
            else:
                print(f"[Tool: GitHub Update Error] ({resp.status_code}): {resp.text}")
        except Exception as e:
            print(f"[Tool: GitHub Update Error] {e}")

    return {"id": issue_id, "status": "simulated_update"}



def search_local_codebase(query: str, ctx: Context) -> List[Dict[str, Any]]:
    """Search the actual repository codebase for files, classes, functions, and standard packages.

    Args:
        query: Search term for files, classes, or code content.
    """
    print(f"[Tool: Local Codebase] Searching codebase for '{query}'...")
    results = []
    base_dir = os.getcwd()
    search_query = query.lower()

    for root, _, files in os.walk(base_dir):
        if any(ignored in root for ignored in [".git", ".venv", "__pycache__", ".adk"]):
            continue
        for file in files:
            if file.endswith((".py", ".md", ".json", ".yaml", ".yml", ".toml", ".sh")):
                rel_path = os.path.relpath(os.path.join(root, file), base_dir)
                try:
                    full_p = os.path.join(root, file)
                    with open(full_p, "r", encoding="utf-8", errors="ignore") as f:
                        content = f.read()
                        if search_query in rel_path.lower() or search_query in content.lower():
                            results.append({
                                "filepath": rel_path,
                                "content": content[:2000],
                            })
                            if len(results) >= 10:
                                return results
                except Exception:
                    pass

    return results or MOCK_LOCAL_CODEBASE_FILES


def execute_code_experiment(code: str, ctx: Context) -> Dict[str, Any]:
    """Execute a Python code snippet internally to experiment on ideas or verify architectural assumptions.

    Args:
        code: Python code string to execute.
    """
    print(f"[Tool: Code Experiment] Executing code snippet ({len(code)} bytes)...")
    import subprocess

    try:
        res = subprocess.run(
            ["python3", "-c", code],
            capture_output=True,
            text=True,
            timeout=10,
            cwd=os.getcwd(),
        )
        return {
            "stdout": res.stdout,
            "stderr": res.stderr,
            "returncode": res.returncode,
        }
    except Exception as e:
        return {"error": str(e)}


def add_design_comment(issue_id: int, spec_body: str, ctx: Context) -> Dict[str, Any]:
    """Append the RFC technical specification as a comment to an existing GitHub issue.

    Args:
        issue_id: The ID of the GitHub issue to comment on.
        spec_body: The complete technical design spec body.
    """
    print(f"[Tool: GitHub] Appending design comment to issue #{issue_id}")
    token = get_github_installation_token()
    if token:
        try:
            import requests

            headers = {"Authorization": f"Bearer {token}", "Accept": "application/vnd.github+json"}
            repo = os.getenv("GITHUB_REPO", "mbychkowski/agent-factory")
            url = f"https://api.github.com/repos/{repo}/issues/{issue_id}/comments"
            resp = requests.post(url, headers=headers, json={"body": spec_body}, timeout=10)
            if resp.status_code in (200, 201):
                data = resp.json()
                comment_id = data.get("id")
                ctx.state["tech_design_comment_id"] = comment_id
                ctx.state["tech_design_completed"] = True
                ctx.state["tech_design_markdown"] = spec_body
                print(f"[Tool: GitHub] Added real RFC comment #{comment_id} to Issue #{issue_id}")
                return {"id": comment_id, "body": spec_body, "url": data.get("html_url")}
        except Exception as e:
            print(f"[Tool: GitHub Design Comment Error] {e}")

    comment_id = 456
    ctx.state["tech_design_comment_id"] = comment_id
    ctx.state["tech_design_completed"] = True
    ctx.state["tech_design_markdown"] = spec_body
    return {"id": comment_id, "body": spec_body}


def create_developer_sub_issue(
    parent_issue_id: int, title: str, body: str, depends_on: List[int], ctx: Context
) -> Dict[str, Any]:
    """Create a child developer sub-issue on GitHub linked to the parent issue and upstream dependencies.

    Args:
        parent_issue_id: The ID of the parent feature issue.
        title: The title of the developer task sub-issue.
        body: The comprehensive task breakdown body with ACs and branch specs.
        depends_on: List of upstream issue IDs that block this task.
    """
    print(f"[Tool: GitHub Sub-Issue] Creating sub-issue for Parent #{parent_issue_id}: '{title}'")
    token = get_github_installation_token()

    dep_refs = ", ".join([f"#{dep_id}" for dep_id in depends_on]) if depends_on else "None"
    formatted_body = (
        f"**Parent Issue:** #{parent_issue_id}\n"
        f"**Dependencies / Blocked By:** {dep_refs}\n\n"
        "---\n\n"
        f"{body}"
    )

    if token:
        try:
            import requests

            headers = {"Authorization": f"Bearer {token}", "Accept": "application/vnd.github+json"}
            repo = os.getenv("GITHUB_REPO", "mbychkowski/agent-factory")
            url = f"https://api.github.com/repos/{repo}/issues"
            resp = requests.post(
                url,
                headers=headers,
                json={"title": f"[Sub-Task] {title}", "body": formatted_body},
                timeout=10,
            )
            if resp.status_code in (200, 201):
                sub_issue_data = resp.json()
                sub_id = sub_issue_data.get("number")
                print(f"[Tool: GitHub] Created real sub-issue #{sub_id} in {repo}")
                return {
                    "id": sub_id,
                    "title": title,
                    "parent_issue_id": parent_issue_id,
                    "status": "open",
                    "url": sub_issue_data.get("html_url"),
                }
        except Exception as e:
            print(f"[Tool: GitHub Sub-Issue Creation Error] {e}")

    sub_id = 101
    return {"id": sub_id, "title": title, "parent_issue_id": parent_issue_id, "status": "open"}

