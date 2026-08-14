import unittest
from unittest.mock import AsyncMock, MagicMock, patch

from google.adk.agents.context import Context

from spec_engine.agents.agent import council_loop_router, council_review_gate


class TestCouncilGate(unittest.TestCase):

    @patch("spec_engine.agents.agent._run_agent_helper", new_callable=AsyncMock)
    def test_council_review_gate_execution(self, mock_run_helper) -> None:
        # Side effects for 4 agent runs: product, tech, security, council_chair
        mock_run_helper.side_effect = [
            "Product feedback",
            "Tech feedback",
            "Security feedback",
            "Consolidated revision guide",
        ]

        ctx = MagicMock(spec=Context)
        ctx.state = {
            "user_story_markdown": "# Draft Spec",
            "product_review_result": {"invest_score": 90, "is_approved": True},
            "critique_result": {"score": 8, "is_approved": True},
            "security_review_result": {"security_score": 95, "is_approved": True},
            "specifications": {"council_review_rounds": 0},
            "council_review": [],
        }

        event = asyncio_run(council_review_gate("Draft Spec", ctx))

        self.assertEqual(event.output, "Consolidated revision guide")
        self.assertEqual(ctx.state["specifications"]["council_review_rounds"], 1)
        self.assertEqual(
            ctx.state["specifications"]["council_scores"],
            {"product": 90, "tech": 8, "security": 95},
        )
        self.assertEqual(ctx.state["specifications"]["council_notes_summarized"], "Consolidated revision guide")
        self.assertEqual(len(ctx.state["council_review"]), 1)
        self.assertEqual(
            ctx.state["council_review"][0]["council_scores"],
            {"product": 90, "tech": 8, "security": 95},
        )
        self.assertEqual(ctx.state["council_review"][0]["council_notes"]["product"], "Product feedback")
        self.assertEqual(ctx.state["council_review"][0]["council_notes"]["tech"], "Tech feedback")
        self.assertEqual(ctx.state["council_review"][0]["council_notes"]["security"], "Security feedback")

    def test_council_loop_router_two_round_limit(self) -> None:
        ctx = MagicMock(spec=Context)

        ctx.state = {"specifications": {"council_review_rounds": 0}}
        event1 = council_loop_router(ctx)
        self.assertEqual(event1.actions.route, "loop_again")

        ctx.state = {"specifications": {"council_review_rounds": 1}}
        event2 = council_loop_router(ctx)
        self.assertEqual(event2.actions.route, "loop_again")

        ctx.state = {"specifications": {"council_review_rounds": 2}}
        event3 = council_loop_router(ctx)
        self.assertEqual(event3.actions.route, "publish")


def asyncio_run(coro):
    import asyncio
    return asyncio.run(coro)


if __name__ == "__main__":
    unittest.main()
