import os


class Config:
    @property
    def default_llm(self) -> str:
        return os.environ.get("DEFAULT_LLM", "gemini-3.6-flash")


config = Config()
