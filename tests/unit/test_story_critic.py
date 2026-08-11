from unittest.mock import MagicMock

from agent_engine.agents.agent import loop_router, root_workflow
from agent_engine.agents.story_critic.agent import story_critic_agent
from agent_engine.agents.story_refiner.prompt import get_prompt as get_refiner_prompt


def test_story_critic_configuration():
    # Verify story_critic only considers latest user_story_markdown in context
    assert story_critic_agent.include_contents == "none"
    assert "{user_story_markdown}" in story_critic_agent.instruction


def test_story_refiner_prompt_critique_placeholders():
    prompt = get_refiner_prompt()
    assert "{latest_critique_score}" in prompt
    assert "{latest_critique_is_approved}" in prompt
    assert "{latest_critique_notes}" in prompt
    assert "{latest_missing_elements}" in prompt


def test_loop_router_logic():
    ctx = MagicMock()

    # Case 1: Less than 3 rounds -> route back to story_refiner
    ctx.state = {"specifications": {"story_review_rounds": 1}}
    event1 = loop_router(ctx)
    assert event1.actions.route == "loop_again"

    ctx.state = {"specifications": {"story_review_rounds": 2}}
    event2 = loop_router(ctx)
    assert event2.actions.route == "loop_again"

    # Case 2: 3 or more rounds -> route to publish gate
    ctx.state = {"specifications": {"story_review_rounds": 3}}
    event3 = loop_router(ctx)
    assert event3.actions.route == "publish"


def test_graph_workflow_wiring():
    assert root_workflow.name == "agile_github_planning_app"
