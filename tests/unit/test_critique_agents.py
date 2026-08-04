import unittest
from agent_engine.agents.critique.story_critic import story_critic_agent
from agent_engine.agents.critique.design_critic import design_critic_agent
from agent_engine.agents.critique.schemas import CritiqueResult


class TestCritiqueAgents(unittest.TestCase):

    def test_story_critic_agent_initialization(self) -> None:
        self.assertEqual(story_critic_agent.name, "story_critic")
        self.assertEqual(story_critic_agent.output_schema, CritiqueResult)

    def test_design_critic_agent_initialization(self) -> None:
        self.assertEqual(design_critic_agent.name, "design_critic")
        self.assertEqual(design_critic_agent.output_schema, CritiqueResult)

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


if __name__ == "__main__":
    unittest.main()
