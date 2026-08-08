from typing import Any


def build_agent_interaction_prompt(
    interaction_type: str,
    content_text: str,
    issue_id: int | None = None,
    raw_payload: dict[str, Any] | None = None,
) -> str:
    """Constructs a structured, injection-resistant prompt for the Vertex AI Reasoning Engine agent.

    Args:
        interaction_type: Canonical interaction type (e.g. 'ISSUE_OPENED', 'COMMENT').
        content_text: Raw human user message or issue description.
        issue_id: Target GitHub issue ID if applicable.
        raw_payload: Raw event payload to extract title or context metadata.
    """
    if not issue_id:
        return (
            f"Received GitHub human interaction event ({interaction_type}):\n\n"
            f"<user_input>\n{content_text}\n</user_input>"
        )

    raw_payload = raw_payload or {}
    issue_data = raw_payload.get("issue", {}) if isinstance(raw_payload, dict) else {}
    issue_title = issue_data.get("title", "") if isinstance(issue_data, dict) else ""

    issue_context_str = f"Issue #{issue_id} ({issue_title})" if issue_title else f"Issue #{issue_id}"

    return (
        f"### GitHub Interaction Event Context\n"
        f"- Target: {issue_context_str}\n"
        f"- Event: {interaction_type}\n\n"
        f"### Human User Input\n"
        f"<user_input>\n{content_text.strip()}\n</user_input>"
    )

