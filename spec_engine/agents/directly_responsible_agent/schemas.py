from pydantic import BaseModel, Field


class SpecOutput(BaseModel):
    full_spec_markdown: str = Field(
        description="Finalized, comprehensive specification formatted in Markdown adhering strictly to INVEST and BDD standards."
    )
