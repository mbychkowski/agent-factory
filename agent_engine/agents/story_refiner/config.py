import os

class Config:
    @property
    def default_llm(self) -> str:
        # Defaulting to gemini-2.5-flash which is standard in Google ADK
        return os.environ.get("DEFAULT_LLM", "gemini-3.6-flash")

config = Config()
