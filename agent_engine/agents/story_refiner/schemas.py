from pydantic import BaseModel, Field


class UserStoryOutput(BaseModel):
    user_story_markdown: str = Field(
        description="Finalized, comprehensive User Story formatted in Markdown adhering strictly to INVEST and BDD standards."
    )
