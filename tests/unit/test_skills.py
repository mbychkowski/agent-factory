import unittest

from spec_engine.skills.skills import (
    agent_spec_skill_toolset,
    agent_spec_standards_skill,
    github_markdown_formatting_skill,
)


class TestSkills(unittest.TestCase):

    def test_skills_loaded(self) -> None:
        self.assertEqual(agent_spec_standards_skill.frontmatter.name, "agent-spec-standards")
        self.assertEqual(github_markdown_formatting_skill.frontmatter.name, "github-markdown-formatting")

    def test_skill_toolset_contains_both_skills(self) -> None:
        self.assertIsNotNone(agent_spec_skill_toolset)
        # Check that both skills are bound in the toolset
        skill_names = [s.frontmatter.name if hasattr(s, "frontmatter") else str(s) for s in agent_spec_skill_toolset._skills]
        self.assertIn("agent-spec-standards", skill_names)
        self.assertIn("github-markdown-formatting", skill_names)


if __name__ == "__main__":
    unittest.main()
