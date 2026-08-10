import unittest
from unittest.mock import MagicMock

from google.adk.agents.context import Context

from agent_engine.agents.story_critic import CritiqueResult, story_critic_agent
from agent_engine.agents.story_critic.agent import extract_critique_data, save_critique_callback


class TestCritiqueAgents(unittest.TestCase):

    def test_story_critic_agent_initialization(self) -> None:
        self.assertEqual(story_critic_agent.name, "story_critic")
        self.assertEqual(story_critic_agent.output_schema, CritiqueResult)
        self.assertIsNotNone(story_critic_agent.after_agent_callback)

    def test_critique_result_schema(self) -> None:
        res = CritiqueResult(
            is_approved=False,
            score=6,
            critique_notes="Missing rate-limiting strategy and BDD Given conditions.",
            missing_elements=["Rate limiting NFR", "BDD Given conditions"]
        )
        self.assertFalse(res.is_approved)
        self.assertEqual(res.score, 6)
        self.assertEqual(len(res.missing_elements), 2)

    def test_extract_critique_data_pydantic_model(self) -> None:
        res = CritiqueResult(
            is_approved=True,
            score=9,
            critique_notes="Excellent user story.",
            missing_elements=[]
        )
        extracted = extract_critique_data(res)
        self.assertIsNotNone(extracted)
        self.assertTrue(extracted["is_approved"])
        self.assertEqual(extracted["score"], 9)

    def test_extract_critique_data_json_string(self) -> None:
        json_str = '```json\n{"is_approved": false, "score": 5, "critique_notes": "Needs work.", "missing_elements": ["NFR"]}\n```'
        extracted = extract_critique_data(json_str)
        self.assertIsNotNone(extracted)
        self.assertFalse(extracted["is_approved"])
        self.assertEqual(extracted["score"], 5)

    def test_save_critique_callback_updates_state(self) -> None:
        ctx = MagicMock(spec=Context)
        ctx.state = {}
        res = CritiqueResult(
            is_approved=True,
            score=9,
            critique_notes="Approved story.",
            missing_elements=[]
        )
        ctx.output = res

        import asyncio
        asyncio.run(save_critique_callback(ctx))

        self.assertTrue(ctx.state.get("is_story_approved", True))
        self.assertEqual(ctx.state["latest_critique_score"], 9)
        self.assertEqual(ctx.state["latest_critique_notes"], "Approved story.")


if __name__ == "__main__":
    unittest.main()

