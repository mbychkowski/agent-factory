from unittest.mock import MagicMock

from spec_engine.agents.agent import council_loop_router, root_workflow
from spec_engine.agents.directly_responsible_agent.prompt import get_prompt as get_dra_prompt
from spec_engine.agents.story_critic.agent import story_critic_agent


def test_story_critic_configuration():
    # Verify story_critic only considers latest user_story_markdown in context
    assert story_critic_agent.include_contents == "none"
    assert "{user_story_markdown}" in story_critic_agent.instruction


def test_dra_prompt_critique_placeholders():
    prompt = get_dra_prompt()
    assert "{latest_critique_score}" in prompt
    assert "{latest_critique_is_approved}" in prompt
    assert "{latest_critique_notes}" in prompt
    assert "{latest_missing_elements}" in prompt


def test_council_loop_router_logic():
    ctx = MagicMock()

    # Case 1: Less than 2 rounds -> route back to directly_responsible_agent
    ctx.state = {"specifications": {"council_review_rounds": 0}}
    event1 = council_loop_router(ctx)
    assert event1.actions.route == "loop_again"

    ctx.state = {"specifications": {"council_review_rounds": 1}}
    event2 = council_loop_router(ctx)
    assert event2.actions.route == "loop_again"

    # Case 2: 2 or more rounds -> route to publish gate
    ctx.state = {"specifications": {"council_review_rounds": 2}}
    event3 = council_loop_router(ctx)
    assert event3.actions.route == "publish"


def test_graph_workflow_wiring():
    assert root_workflow.name == "agile_github_planning_app"
