from collections.abc import Awaitable, Callable
from typing import Any

from google.adk.agents.callback_context import CallbackContext
from google.genai import types

from spec_engine.agents.state import ensure_session_state


def create_review_callbacks(
    output_key: str,
    history_key: str,
    transform_fn: Callable[[dict[str, Any]], dict[str, Any]] | None = None,
) -> tuple[
    Callable[[CallbackContext], Awaitable[None]],
    Callable[[CallbackContext], Awaitable[types.Content | None]],
]:
    """Creates a pair of (before_agent_callback, after_agent_callback) for council agents.

    Args:
        output_key: The state key where the agent's output schema result is stored.
        history_key: The key inside `state['specifications']` where historical review entries are appended.
        transform_fn: Optional function to format/sanitize the dict before appending to history.

    Returns:
        A tuple of (before_agent_callback, after_agent_callback).
    """

    async def before_agent_callback(callback_context: CallbackContext) -> None:
        """Callback executed before agent runs to initialize default state variables."""
        ensure_session_state(callback_context.state)

    async def after_agent_callback(
        callback_context: CallbackContext,
    ) -> types.Content | None:
        """Callback executed after agent runs to store review results into specifications history."""
        raw_data = callback_context.state.get(output_key, {})

        if hasattr(raw_data, "model_dump"):
            data = raw_data.model_dump()
        elif isinstance(raw_data, dict):
            data = raw_data
        else:
            data = {}

        if not data:
            return None

        if transform_fn is not None:
            entry = transform_fn(data)
        else:
            entry = data

        ensure_session_state(callback_context.state)
        specifications = callback_context.state["specifications"]

        existing_history = specifications.get(history_key)
        history = list(existing_history) if isinstance(existing_history, list) else []
        history.append(entry)

        # Re-assign top-level state key with new dict and new list reference so ADK registers state mutations
        callback_context.state["specifications"] = {
            **specifications,
            history_key: history,
        }

        return None

    return before_agent_callback, after_agent_callback
