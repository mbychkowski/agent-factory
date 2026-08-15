from pathlib import Path

from google.adk.skills import load_skill_from_dir
from google.adk.tools.skill_toolset import SkillToolset

SKILLS_DIR = Path(__file__).parent
agent_spec_standards_skill = load_skill_from_dir(SKILLS_DIR / "agent-spec-standards")
github_markdown_formatting_skill = load_skill_from_dir(
    SKILLS_DIR / "github-markdown-formatting"
)

agent_spec_skill_toolset = SkillToolset(
    skills=[
        agent_spec_standards_skill,
        github_markdown_formatting_skill,
    ]
)
