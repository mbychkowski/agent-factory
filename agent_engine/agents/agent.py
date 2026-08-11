import asyncio
from typing import Any

from google.adk import Event, Workflow
from google.adk.agents.context import Context
from google.adk.events.event_actions import EventActions
from google.adk.workflow import START

from agent_engine.agents.story_critic.agent import (
    story_critic_agent,
)
from agent_engine.agents.story_refiner.agent import (
    root_agent as agent_user_story_refiner,
)
from agent_engine.agents.tools import (
    update_github_issue,
)


def _get_issue_id(ctx: Any) -> int | None:
    state = getattr(ctx, "state", {}) if hasattr(ctx, "state") else {}
    val = state.get("parent_issue_id") or (state.get("issue", {}).get("id") if isinstance(state.get("issue"), dict) else None)
    return int(val) if val is not None else None


def _get_user_story(ctx: Any) -> str:
    state = getattr(ctx, "state", {}) if hasattr(ctx, "state") else {}
    return str(state.get("user_story_markdown") or "")


async def gate_set_session_state(node_input: Any, ctx: Context) -> Event:
    """Entry gate that receives input and initializes session state variables."""
    print("Entry Gate: Initializing session state and starting deliberation flow...")
    initial_state_delta = {
        "latest_critique_notes": "N/A (Initial Pass)",
        "latest_missing_elements": "None",
        "latest_critique_score": 0,
        "latest_critique_is_approved": False,
        "user_story_markdown": "",
        "specifications": {"story_review_rounds": 0},
    }
    if hasattr(ctx, "state") and isinstance(ctx.state, dict):
        for k, v in initial_state_delta.items():
            ctx.state.setdefault(k, v)

    return Event(output=node_input, actions=EventActions(state_delta=initial_state_delta))


def loop_router(ctx: Context) -> Event:
    """Graph router node that detects how many review loops have occurred by referencing state.

    If less than 3 loops have completed, routes back to story_refiner ('loop_again').
    Otherwise, routes to gate_publish_user_story ('publish').
    """
    state = getattr(ctx, "state", {}) if hasattr(ctx, "state") else {}
    specifications = state.get("specifications", {}) if isinstance(state.get("specifications"), dict) else {}
    rounds = int(specifications.get("story_review_rounds", 0))

    print(f"[Loop Router] Completed review round {rounds} / 3.")

    if rounds < 3:
        print(f"[Loop Router] Round {rounds} < 3: Routing back to User Story Refiner for revision...")
        return Event(actions=EventActions(route="loop_again"))

    print(f"[Loop Router] Round {rounds} >= 3: Required 3 review loops completed. Routing to Publish Gate...")
    return Event(actions=EventActions(route="publish"))


async def gate_publish_user_story(ctx: Context) -> Event:
    """Updates main issue description on GitHub with the refined user story."""
    await asyncio.sleep(4)

    parent_id = _get_issue_id(ctx)
    if not parent_id:
        print("Gate Evaluating: Parent Issue ID not found. Finishing turn.")
        return Event()

    user_story = _get_user_story(ctx)
    if not user_story:
        raise ValueError("User Story content missing from session state when attempting to publish to GitHub.")

    try:
        update_github_issue(issue_id=int(parent_id), body=user_story, ctx=ctx)
        print(
            f"[Story Refiner Gate] Automatically updated main GitHub Issue #{parent_id} description with certified User Story."
        )
    except Exception as e:
        print(f"[Story Refiner Gate Warning] Could not auto-update issue #{parent_id}: {e}")

    return Event(output=f"User Story Issue #{parent_id} refined.")


root_workflow = Workflow(
    name="agile_github_planning_app",
    edges=[
        (START, gate_set_session_state),
        (gate_set_session_state, agent_user_story_refiner),
        (agent_user_story_refiner, story_critic_agent),
        (story_critic_agent, loop_router),
        (loop_router, {
            "loop_again": agent_user_story_refiner,
            "publish": gate_publish_user_story
          }
        ),
    ],
)

