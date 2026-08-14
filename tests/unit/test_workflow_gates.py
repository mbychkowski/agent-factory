import unittest
from unittest.mock import MagicMock

from google.adk.agents.context import Context

from spec_engine.agents.agent import gate_set_session_state
from spec_engine.agents.directly_responsible_agent.agent import save_user_story_callback


class TestWorkflowGates(unittest.TestCase):

    def test_gate_set_session_state_initializes_defaults(self) -> None:
        ctx = MagicMock(spec=Context)
        ctx.state = {}

        event = asyncio_run(gate_set_session_state("Raw input", ctx))
        self.assertEqual(event.output, "Raw input")
        self.assertEqual(ctx.state["latest_critique_score"], 0)
        self.assertEqual(ctx.state["latest_critique_is_approved"], False)

    def test_save_user_story_callback_populates_state(self) -> None:
        ctx = MagicMock(spec=Context)
        ctx.state = {"user_story_result": {"user_story_markdown": "As a user, I want tests."}}

        asyncio_run(save_user_story_callback(ctx))
        self.assertEqual(ctx.state["user_story_markdown"], "As a user, I want tests.")


def asyncio_run(coro):
    import asyncio
    return asyncio.run(coro)


if __name__ == "__main__":
    unittest.main()
