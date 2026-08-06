import os
from pydantic import BaseModel, Field


class StoryCriticConfig(BaseModel):
    default_llm: str = Field(
        default_factory=lambda: os.environ.get("DEFAULT_LLM", "gemini-3.6-flash")
    )


config = StoryCriticConfig()
