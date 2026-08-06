import os

# Ensure LLM inference location defaults to global as required for Gemini models
os.environ.setdefault("DEFAULT_LLM_LOCATION", "global")
os.environ.setdefault("LLM_LOCATION", "global")
os.environ.setdefault("LOCATION", "global")


class Config:
    @property
    def default_llm(self) -> str:
        return os.environ.get("DEFAULT_LLM", "gemini-3.6-flash")


config = Config()
