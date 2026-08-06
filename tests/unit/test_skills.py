import unittest

from agent_engine.skills.skills import (
    github_markdown_formatting_skill,
    user_story_best_practices_skill,
    user_story_skill_toolset,
)


class TestSkills(unittest.TestCase):

    def test_skills_loaded(self) -> None:
        self.assertEqual(user_story_best_practices_skill.frontmatter.name, "user-story-best-practices")
        self.assertEqual(github_markdown_formatting_skill.frontmatter.name, "github-markdown-formatting")

    def test_skill_toolset_contains_both_skills(self) -> None:
        self.assertIsNotNone(user_story_skill_toolset)
        # Check that both skills are bound in the toolset
        skill_names = [s.frontmatter.name if hasattr(s, "frontmatter") else str(s) for s in user_story_skill_toolset._skills]
        self.assertIn("user-story-best-practices", skill_names)
        self.assertIn("github-markdown-formatting", skill_names)



if __name__ == "__main__":
    unittest.main()
