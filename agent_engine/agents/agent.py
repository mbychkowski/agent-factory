import asyncio
import json
from typing import Any

from agent_engine.agents.state import (
    get_issue_id,
    get_story_review_rounds,
    get_user_story,
    increment_story_review_rounds,
    is_story_peer_reviewed,
    record_critique_result,
    set_story_peer_reviewed,
)

# Import Peer Review Critique Agents
from agent_engine.agents.story_critic import story_critic_agent as agent_story_critic

# Import Core Spec Agents
from agent_engine.agents.story_refiner.agent import (
    root_agent as agent_user_story_refiner,
)

# Import Tools
from agent_engine.agents.tools import (
    sync_github_issue_labels,
    update_github_issue,
)
from google.adk import Event, Workflow
from google.adk.agents.context import Context
from google.adk.events.event_actions import EventActions
from google.adk.workflow import START


import re


async def gate_entry(node_input: Any, ctx: Context) -> Event:
    """Evaluates incoming human input and routes directly to agent_user_story_refiner."""
    parent_id = get_issue_id(ctx)
    if not parent_id and node_input:
        match = re.search(r"Issue #(\d+)", str(node_input))
        if match:
            parsed_id = int(match.group(1))
            from agent_engine.agents.state import set_issue_metadata
            set_issue_metadata(ctx, issue_id=parsed_id)
            parent_id = parsed_id

    if parent_id:
        try:
            current_phase = "phase:user-story"
            sync_github_issue_labels(
                int(parent_id), "agent:in-progress", current_phase, ctx=ctx
            )
        except Exception as e:
            print(f"[Entry Gate Label Sync Warning] {e}")

    print("Entry Gate: Routing directly to User Story Refiner...")
    return Event(output=node_input, actions=EventActions(route="agent_user_story_refiner"))


async def gate_evaluate_critic_review(node_input: Any, ctx: Context) -> Event:
    """Evaluates agent_story_critic output. If approved, marks peer_reviewed=True.

    If rejected, sends critique back to agent_user_story_refiner for revision (up to 3 rounds).
    """
    raw_output = node_input if isinstance(node_input, str) else str(node_input)
    is_approved = False
    score = None
    critique_notes = ""
    missing_elements = []

    try:
        data = node_input if isinstance(node_input, dict) else None
        if not data and isinstance(raw_output, str):
            clean_json = raw_output.strip()
            if "```json" in clean_json:
                clean_json = clean_json.split("```json")[1].split("```")[0].strip()
            elif "```" in clean_json:
                clean_json = clean_json.split("```")[1].split("```")[0].strip()
            data = json.loads(clean_json)

        if isinstance(data, dict):
            is_approved = bool(data.get("is_approved", False))
            score = data.get("score")
            critique_notes = data.get("critique_notes", "")
            missing_elements = data.get("missing_elements", [])
    except Exception as e:
        print(f"[Gate Critic Parse Warning] {e}")

    review_rounds = get_story_review_rounds(ctx)
    record_critique_result(
        ctx,
        is_approved=is_approved,
        critique_notes=critique_notes,
        score=score,
        missing_elements=missing_elements,
    )

    if is_approved:
        print(
            f"Story Peer Review Approved on round {review_rounds}. Marking as peer-reviewed."
        )
        set_story_peer_reviewed(ctx, True)
        return Event(actions=EventActions(route="gate_publish_user_story"))

    if review_rounds >= 3:
        print(
            f"Story Peer Review reached max rounds ({review_rounds}) without approval. Proceeding to GitHub update with peer_reviewed=False."
        )
        set_story_peer_reviewed(ctx, False)
        return Event(actions=EventActions(route="gate_publish_user_story"))

    new_rounds = increment_story_review_rounds(ctx)
    print(
        f"Story Peer Review Requesting Revision (Round {new_rounds}): {critique_notes}"
    )
    revision_prompt = (
        f"The Technical Architect reviewed your drafted User Story and requested the following improvements:\n"
        f"{critique_notes}\n\n"
        "Please revise the User Story to address these gaps."
    )
    return Event(
        output=revision_prompt, actions=EventActions(route="agent_user_story_refiner")
    )


async def gate_publish_user_story(ctx: Context) -> Event:
    """Updates main issue description on GitHub and marks status as completed or needs-human-lgtm."""
    print("Cooling down for 4 seconds to manage API rate limits...")
    await asyncio.sleep(4)

    parent_id = get_issue_id(ctx)
    user_story = get_user_story(ctx)

    if parent_id and user_story:
        try:
            update_github_issue(issue_id=int(parent_id), body=user_story, ctx=ctx)
            print(
                f"[Story Refiner Gate] Automatically updated main GitHub Issue #{parent_id} description with certified User Story."
            )
        except Exception as e:
            print(
                f"[Story Refiner Gate Warning] Could not auto-update issue #{parent_id}: {e}"
            )

        # Label status: 'agent:completed' if approved by architect critic, else 'agent:needs-human-lgtm'
        status_label = (
            "agent:completed"
            if is_story_peer_reviewed(ctx)
            else "agent:needs-human-lgtm"
        )

        try:
            sync_github_issue_labels(
                int(parent_id), status_label, "phase:user-story", ctx=ctx
            )
        except Exception as e:
            print(f"[Story Refiner Gate Label Sync Warning] {e}")

        return Event(
            output=f"User Story Issue #{parent_id} refined (status='{status_label}')."
        )

    print("Gate Evaluating: Parent Issue ID not found or story empty. Finishing turn.")
    return Event()


root_workflow = Workflow(
    name="agile_github_planning_app",
    edges=[
        (START, gate_entry),
        (gate_entry, agent_user_story_refiner),
        (agent_user_story_refiner, agent_story_critic), # Direct agent-to-agent edge via after_agent_callback!
        (agent_story_critic, gate_evaluate_critic_review),
        (
            gate_evaluate_critic_review,
            {
                "agent_user_story_refiner": agent_user_story_refiner,
                "gate_publish_user_story": gate_publish_user_story,
            },
        ),
    ],
)
