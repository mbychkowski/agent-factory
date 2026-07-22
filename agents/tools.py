import os
from typing import Any, Dict, List
from google.adk.agents.context import Context

# Simple mock local search databases representing local project repository files
MOCK_LOCAL_REQUIREMENTS = [
    {
        "id": "prd-1",
        "title": "Legacy Authentication Service",
        "content": "The system utilizes standard JWT tokens for session management. Secret key is loaded from Environment.",
        "similarity": 0.92,
    },
    {
        "id": "story-45",
        "title": "OAuth Integration",
        "content": "As a user, I want to log in using Google OAuth so that I don't have to manage another password.",
        "similarity": 0.85,
    }
]

MOCK_LOCAL_CODEBASE_FILES = [
    {
        "filepath": "src/auth/jwt.py",
        "content": "class JWTManager:\n    def generate_token(self, user_id: str) -> str:\n        return 'mock_token'",
        "dependencies": ["src/config.py"]
    },
    {
        "filepath": "src/config.py",
        "content": "JWT_SECRET = 'mock_secret'",
        "dependencies": []
    }
]


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
    issue_id = 100  # Standard mock issue ID
    ctx.state["parent_issue_id"] = issue_id
    ctx.state["user_story_markdown"] = body
    print(f"[Tool: GitHub] Successfully created parent issue #{issue_id}")
    return {"id": issue_id, "title": title, "status": "open"}


def search_local_codebase(query: str, ctx: Context) -> List[Dict[str, Any]]:
    """Search the local codebase for files, classes, functions, and standard packages.

    Args:
        query: SQL or semantic search query for files and dependencies.
    """
    print(f"[Tool: Local Codebase] Searching for '{query}'...")
    return MOCK_LOCAL_CODEBASE_FILES


def add_design_comment(issue_id: int, spec_body: str, ctx: Context) -> Dict[str, Any]:
    """Append the RFC technical specification as a comment to an existing GitHub issue.

    Args:
        issue_id: The ID of the GitHub issue to comment on.
        spec_body: The complete technical design spec body.
    """
    print(f"[Tool: GitHub] Appending design comment to issue #{issue_id}")
    comment_id = 456  # Standard mock comment ID
    ctx.state["tech_design_comment_id"] = comment_id
    ctx.state["tech_design_completed"] = True
    ctx.state["tech_design_markdown"] = spec_body
    print(f"[Tool: GitHub] Successfully added technical design comment #{comment_id} to Issue #{issue_id}")
    return {"id": comment_id, "body": spec_body}
