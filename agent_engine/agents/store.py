"""Lightweight Session State Helper & Callback Framework for ADK Agents.

Provides clean dot-notation access to ctx.state and higher-order callbacks
without unnecessary boilerplate.
"""

from typing import Any, Callable, TypeVar

T = TypeVar("T")


class AgentStore:
    """Lightweight Session State Store wrapping ADK Context (ctx.state).

    Provides dot-notation getters/setters and a useState-style hook.
    """

    def __init__(self, ctx: Any) -> None:
        self.ctx = ctx

    @property
    def raw_state(self) -> dict[str, Any]:
        """Direct access to underlying ctx.state dictionary."""
        if hasattr(self.ctx, "state") and isinstance(self.ctx.state, dict):
            return self.ctx.state
        if hasattr(self.ctx, "context") and hasattr(self.ctx.context, "state"):
            return self.ctx.context.state
        return {}

    def get(self, path: str, default: Any = None) -> Any:
        """Retrieves state value using dot-notation path (e.g. 'specifications.user_story_markdown')."""
        parts = path.split(".")
        current = self.raw_state
        for p in parts[:-1]:
            if not isinstance(current, dict):
                return default
            current = current.get(p, {})
        if isinstance(current, dict):
            return current.get(parts[-1], default)
        return default

    def set(self, path: str, value: Any) -> None:
        """Sets state value using dot-notation path (e.g. 'specifications.user_story_markdown')."""
        parts = path.split(".")
        current = self.raw_state
        for p in parts[:-1]:
            current = current.setdefault(p, {})
            if not isinstance(current, dict):
                return
        current[parts[-1]] = value

    def use_state(self, path: str, default: T = None) -> tuple[T, Callable[[T], None]]:
        """React-inspired useState hook helper.

        Returns a tuple of (current_value, state_setter_function).

        Example:
            story, set_story = store.use_state('specifications.user_story_markdown', default='')
            set_story('New story content...')
        """
        current_val = self.get(path, default)

        def set_state_val(new_val: T) -> None:
            self.set(path, new_val)

        return current_val, set_state_val


def create_agent_state_callback(
    extractor: Callable[[Any], Any],
    updater: Callable[[Any, AgentStore], None],
    required_error_msg: str | None = None,
) -> Callable[..., Any]:
    """Higher-Order Function that creates a standardized ADK after_agent_callback.

    Args:
        extractor: Function that extracts target payload from agent output context.
        updater: Callback function receiving (extracted_payload, store) to mutate state.
        required_error_msg: Optional error message to raise if extracted payload is empty.
    """

    async def callback(ctx: Any = None, callback_context: Any = None, **kwargs: Any) -> None:
        active_ctx = callback_context or ctx
        if not active_ctx:
            return

        store = AgentStore(active_ctx)
        output = getattr(active_ctx, "output", None)
        payload = extractor(output) if output else None

        if not payload:
            if required_error_msg:
                raise ValueError(required_error_msg)
            return

        updater(payload, store)

    return callback
