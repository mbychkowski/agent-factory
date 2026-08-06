import unittest
from unittest.mock import MagicMock
from google.adk.agents.context import Context
from agent_engine.agents.agent import gate_entry
from agent_engine.agents.story_refiner.agent import save_user_story_callback


class TestWorkflowGates(unittest.TestCase):

    def test_gate_entry_initial_start(self) -> None:
        ctx = MagicMock(spec=Context)
        ctx.state = {}

        event = asyncio_run(gate_entry("Raw requirement input", ctx))
        self.assertEqual(event.actions.route, "agent_user_story_refiner")

    def test_gate_entry_subsequent_turn(self) -> None:
        ctx = MagicMock(spec=Context)
        ctx.state = {"parent_issue_id": 100, "user_story_markdown": "As a user..."}

        event = asyncio_run(gate_entry("Some human comment", ctx))
        self.assertEqual(event.actions.route, "agent_user_story_refiner")

    def test_save_user_story_callback_populates_state(self) -> None:
        ctx = MagicMock(spec=Context)
        ctx.state = {}
        raw_story_text = "As a user, I want to authenticate via JWT token so that my session is secure."
        ctx.output = raw_story_text

        asyncio_run(save_user_story_callback(ctx))
        self.assertEqual(ctx.state["specifications"]["user_story_markdown"], raw_story_text)


def asyncio_run(coro):
    import asyncio
    return asyncio.run(coro)


if __name__ == "__main__":
    unittest.main()
