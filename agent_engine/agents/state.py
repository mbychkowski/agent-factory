"""Domain State Access API for Spec Deliberator Agent.

Provides semantic domain helper functions backed by AgentStore.
"""

from typing import Any

from agent_engine.agents.store import AgentStore


def get_issue_id(ctx: Any) -> int | None:
    """Retrieves issue ID from structured state or legacy parent_issue_id."""
    store = AgentStore(ctx)
    issue_id = store.get("issue.id")
    if issue_id is not None:
        return int(issue_id)
    parent_id = store.get("parent_issue_id")
    if parent_id is not None:
        return int(parent_id)
    return None


def set_issue_metadata(
    ctx: Any,
    issue_id: int | None = None,
    title: str | None = None,
    author: str | None = None,
    url: str | None = None,
    labels: list[str] | None = None,
) -> None:
    """Populates or updates structured issue metadata in session state."""
    store = AgentStore(ctx)
    if issue_id is not None:
        store.set("issue.id", issue_id)
        store.set("parent_issue_id", issue_id)
    if title is not None:
        store.set("issue.title", title)
    if author is not None:
        store.set("issue.author", author)
    if url is not None:
        store.set("issue.url", url)
    if labels is not None:
        store.set("issue.labels", labels)


def get_user_story(ctx: Any) -> str:
    """Retrieves generated user story markdown from specifications domain or root."""
    store = AgentStore(ctx)
    story = store.get("specifications.user_story_markdown")
    if story:
        return str(story)
    return str(store.get("user_story_markdown", ""))


def set_user_story(ctx: Any, markdown: str) -> None:
    """Sets generated user story markdown in both specifications domain and root."""
    store = AgentStore(ctx)
    store.set("specifications.user_story_markdown", markdown)
    store.set("user_story_markdown", markdown)


def is_story_peer_reviewed(ctx: Any) -> bool:
    """Checks if user story has passed peer review."""
    store = AgentStore(ctx)
    reviewed = store.get("specifications.story_peer_reviewed")
    if reviewed is not None:
        return bool(reviewed)
    return bool(store.get("story_peer_reviewed", False))


def set_story_peer_reviewed(ctx: Any, reviewed: bool) -> None:
    """Sets story peer review status."""
    store = AgentStore(ctx)
    store.set("specifications.story_peer_reviewed", reviewed)
    store.set("story_peer_reviewed", reviewed)


def get_story_review_rounds(ctx: Any) -> int:
    """Retrieves story review round count."""
    store = AgentStore(ctx)
    rounds = store.get("specifications.story_review_rounds")
    if rounds is not None:
        return int(rounds)
    return int(store.get("story_review_rounds", 0))


def increment_story_review_rounds(ctx: Any) -> int:
    """Increments review round count by 1 and returns new count."""
    current = get_story_review_rounds(ctx)
    new_count = current + 1
    store = AgentStore(ctx)
    store.set("specifications.story_review_rounds", new_count)
    store.set("story_review_rounds", new_count)
    return new_count


def record_critique_result(
    ctx: Any,
    is_approved: bool,
    critique_notes: str,
    score: int | None = None,
    missing_elements: list[str] | None = None,
) -> None:
    """Records critique history audit record in specifications domain and root state."""
    store = AgentStore(ctx)
    rounds = get_story_review_rounds(ctx)
    specs = store.raw_state.setdefault("specifications", {})
    history = specs.setdefault("critique_history", [])

    entry = {
        "round": rounds,
        "is_approved": is_approved,
        "score": score,
        "notes": critique_notes,
        "missing_elements": missing_elements or [],
    }
    history.append(entry)

    root_history = store.raw_state.setdefault("critique_history", [])
    root_history.append(entry)

    store.set("specifications.story_peer_reviewed", is_approved)
    store.set("latest_critique_notes", critique_notes)
    store.set("latest_critique_score", score)
    store.set("is_story_approved", is_approved)
