from typing import Any, Dict, List, Optional, Union

from google.adk.agents.context import Context


def get_issue_id(ctx: Context) -> int | None:
    """Retrieves issue ID from structured state or legacy parent_issue_id."""
    issue = ctx.state.get("issue")
    if isinstance(issue, dict) and issue.get("id"):
        return int(issue["id"])
    parent_id = ctx.state.get("parent_issue_id")
    if parent_id is not None:
        return int(parent_id)
    return None


def set_issue_metadata(
    ctx: Context,
    issue_id: int | None = None,
    title: str | None = None,
    author: str | None = None,
    url: str | None = None,
    labels: list[str] | None = None,
) -> None:
    """Populates or updates structured issue metadata in ctx.state."""
    issue = ctx.state.setdefault("issue", {})
    if issue_id is not None:
        issue["id"] = issue_id
        ctx.state["parent_issue_id"] = issue_id
    if title is not None:
        issue["title"] = title
    if author is not None:
        issue["author"] = author
    if url is not None:
        issue["url"] = url
    if labels is not None:
        issue["labels"] = labels


def get_user_story(ctx: Context) -> str:
    """Retrieves generated user story markdown from specifications domain or root."""
    specs = ctx.state.get("specifications")
    if isinstance(specs, dict) and specs.get("user_story_markdown"):
        return specs["user_story_markdown"]
    return ctx.state.get("user_story_markdown", "")


def set_user_story(ctx: Context, markdown: str) -> None:
    """Sets generated user story markdown in both specifications domain and root for compatibility."""
    specs = ctx.state.setdefault("specifications", {})
    specs["user_story_markdown"] = markdown
    ctx.state["user_story_markdown"] = markdown


def is_story_peer_reviewed(ctx: Context) -> bool:
    """Checks if user story has passed peer review."""
    specs = ctx.state.get("specifications")
    if isinstance(specs, dict) and "story_peer_reviewed" in specs:
        return bool(specs["story_peer_reviewed"])
    return bool(ctx.state.get("story_peer_reviewed", False))


def set_story_peer_reviewed(ctx: Context, reviewed: bool) -> None:
    """Sets story peer review status."""
    specs = ctx.state.setdefault("specifications", {})
    specs["story_peer_reviewed"] = reviewed
    ctx.state["story_peer_reviewed"] = reviewed


def get_story_review_rounds(ctx: Context) -> int:
    """Retrieves story review round count."""
    specs = ctx.state.get("specifications")
    if isinstance(specs, dict) and "story_review_rounds" in specs:
        return int(specs["story_review_rounds"])
    return int(ctx.state.get("story_review_rounds", 0))


def increment_story_review_rounds(ctx: Context) -> int:
    """Increments review round count by 1 and returns new count."""
    current = get_story_review_rounds(ctx)
    new_count = current + 1
    specs = ctx.state.setdefault("specifications", {})
    specs["story_review_rounds"] = new_count
    ctx.state["story_review_rounds"] = new_count
    return new_count


def record_critique_result(
    ctx: Context,
    is_approved: bool,
    critique_notes: str,
    score: int | None = None,
    missing_elements: list[str] | None = None,
) -> None:
    """Records critique history audit record in specifications domain."""
    specs = ctx.state.setdefault("specifications", {})
    history = specs.setdefault("critique_history", [])
    history.append({
        "round": get_story_review_rounds(ctx),
        "is_approved": is_approved,
        "score": score,
        "notes": critique_notes,
        "missing_elements": missing_elements or [],
    })


def append_comment(
    ctx: Context,
    body: str,
    author: str = "unknown",
    source: str = "github",
    comment_id: int | str | None = None,
    timestamp: str | None = None,
) -> None:
    """Appends a comment delta to ctx.state['comments']."""
    comments = ctx.state.setdefault("comments", [])
    comments.append({
        "comment_id": comment_id,
        "source": source,
        "author": author,
        "body": body,
        "timestamp": timestamp,
    })


def get_comments(ctx: Context) -> list[dict[str, Any]]:
    """Retrieves comments list from ctx.state."""
    return ctx.state.get("comments", [])
