import asyncio
import unittest
from unittest.mock import MagicMock

from google.adk.agents.context import Context

from agent_engine.agents.store import AgentStore, create_agent_state_callback


class TestAgentStoreFramework(unittest.TestCase):

    def test_store_dot_notation_get_set(self) -> None:
        ctx = MagicMock(spec=Context)
        ctx.state = {}
        store = AgentStore(ctx)

        store.set("specifications.user_story_markdown", "As a developer...")
        self.assertEqual(store.get("specifications.user_story_markdown"), "As a developer...")
        self.assertEqual(ctx.state["specifications"]["user_story_markdown"], "As a developer...")

    def test_use_state_hook(self) -> None:
        ctx = MagicMock(spec=Context)
        ctx.state = {}
        store = AgentStore(ctx)

        story, set_story = store.use_state("specifications.user_story_markdown", default="Initial")
        self.assertEqual(story, "Initial")

        set_story("Updated story via hook")
        self.assertEqual(store.get("specifications.user_story_markdown"), "Updated story via hook")

    def test_higher_order_agent_callback(self) -> None:
        ctx = MagicMock(spec=Context)
        ctx.state = {}
        ctx.output = "As a user, I want feature X."

        def dummy_extractor(out):
            return str(out) if out else None

        def dummy_updater(payload, store):
            store.set("user_story_markdown", payload)

        callback = create_agent_state_callback(
            extractor=dummy_extractor,
            updater=dummy_updater
        )
        asyncio.run(callback(ctx))

        self.assertEqual(ctx.state["user_story_markdown"], "As a user, I want feature X.")


if __name__ == "__main__":
    unittest.main()
