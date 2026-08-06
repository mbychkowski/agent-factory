from pathlib import Path

from google.adk.skills import load_skill_from_dir
from google.adk.tools.skill_toolset import SkillToolset

SKILLS_DIR = Path(__file__).parent
user_story_best_practices_skill = load_skill_from_dir(SKILLS_DIR / "user-story-best-practices")
github_markdown_formatting_skill = load_skill_from_dir(SKILLS_DIR / "github-markdown-formatting")

user_story_skill_toolset = SkillToolset(
    skills=[
        user_story_best_practices_skill,
        github_markdown_formatting_skill,
    ]
)

