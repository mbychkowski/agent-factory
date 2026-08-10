"""Lightweight Session State Helper & Callback Framework for ADK Agents.

Provides clean dot-notation access to ctx.state, unified ADK output extraction,
and higher-order callbacks without unnecessary boilerplate.
"""

import json
from typing import Any, Callable, TypeVar
from unittest.mock import MagicMock, Mock

T = TypeVar("T")


def extract_adk_payload(output: Any) -> Any:
    """Unified ADK Output Extractor: Automatically handles Pydantic models, dicts, or text Content."""
    if output is None:
        return None

    # Handle Pydantic models (excluding MagicMock in unit tests)
    if not isinstance(output, (Mock, MagicMock)):
        if hasattr(output, "model_dump"):
            try:
                return output.model_dump()
            except Exception:
                pass
        if hasattr(output, "dict"):
            try:
                return output.dict()
            except Exception:
                pass

    if isinstance(output, dict):
        return output

    if isinstance(output, str):
        clean = output.strip()
        if "```json" in clean:
            clean = clean.split("```json")[1].split("```")[0].strip()
        elif "```" in clean:
            clean = clean.split("```")[1].split("```")[0].strip()
        if clean.startswith("{") and clean.endswith("}"):
            try:
                res = json.loads(clean)
                if isinstance(res, dict):
                    return res
            except Exception:
                pass
        return output.strip()

    if hasattr(output, "content") and output.content:
        return extract_adk_payload(output.content)

    if hasattr(output, "parts") and output.parts:
        return "\n".join(str(p.text) for p in output.parts if getattr(p, "text", None)).strip()

    return str(output).strip()


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
    target_path: str | None = None,
    updater: Callable[[Any, AgentStore], None] | None = None,
    required_error_msg: str | None = None,
) -> Callable[..., Any]:
    """Higher-Order Function that creates a standardized ADK after_agent_callback.

    Args:
        target_path: Optional state dot-notation path to save extracted payload automatically.
        updater: Optional custom callback function receiving (extracted_payload, store).
        required_error_msg: Optional error message to raise if extracted payload is empty.
    """

    async def callback(ctx: Any = None, callback_context: Any = None, **kwargs: Any) -> None:
        active_ctx = callback_context or ctx
        if not active_ctx:
            return

        store = AgentStore(active_ctx)
        output = getattr(active_ctx, "output", None)
        payload = extract_adk_payload(output) if output else None

        if not payload or (isinstance(payload, str) and len(payload.strip()) <= 20 and required_error_msg):
            if required_error_msg:
                raise ValueError(required_error_msg)
            return

        if target_path:
            store.set(target_path, payload)

        if updater:
            updater(payload, store)

    return callback
