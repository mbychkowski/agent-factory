import os

class Config:
    @property
    def default_llm(self) -> str:
        return os.environ.get("DEFAULT_LLM", "gemini-2.5-flash")

config = Config()
