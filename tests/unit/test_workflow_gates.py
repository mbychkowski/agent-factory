import unittest
from unittest.mock import MagicMock
from google.adk.agents.context import Context
from agent_engine.agents.agent import facilitator_gate, gate_after_facilitator


class TestWorkflowGates(unittest.TestCase):

    def test_facilitator_gate_initial_start(self) -> None:
        # Mock context with empty state
        ctx = MagicMock(spec=Context)
        ctx.state = {}

        event = asyncio_run(facilitator_gate("Raw requirement input", ctx))
        self.assertEqual(event.actions.route, "user_story_refiner")

    def test_facilitator_gate_subsequent_turn(self) -> None:
        # Mock context with existing spec state
        ctx = MagicMock(spec=Context)
        ctx.state = {"parent_issue_id": 100, "user_story_markdown": "As a user..."}

        event = asyncio_run(facilitator_gate("Some human comment", ctx))
        self.assertEqual(event.actions.route, "deliberation_facilitator")

    def test_gate_after_facilitator_noise_filtering(self) -> None:
        ctx = MagicMock(spec=Context)
        ctx.state = {}

        noise_output = {
            "classification": "NOISE_OFF_TOPIC",
            "human_response": "Ignored banter."
        }

        event = asyncio_run(gate_after_facilitator(noise_output, ctx))
        self.assertEqual(event.output, "Ignored banter.")
        self.assertIsNone(event.actions.route)

    def test_gate_after_facilitator_actionable_routing(self) -> None:
        ctx = MagicMock(spec=Context)
        ctx.state = {}

        actionable_output = {
            "classification": "ACTIONABLE_SPEC_FEEDBACK",
            "target_phase": "TECHNICAL_DESIGN",
            "synthesized_delta": "Use Spanner DB instead of Postgres."
        }

        event = asyncio_run(gate_after_facilitator(actionable_output, ctx))
        self.assertEqual(event.actions.route, "technical_designer")
        self.assertEqual(ctx.state["synthesized_feedback"], "Use Spanner DB instead of Postgres.")


def asyncio_run(coro):
    import asyncio
    return asyncio.run(coro)


if __name__ == "__main__":
    unittest.main()
