import asyncio
from typing import Any

from google.adk import Event, Workflow
from google.adk.agents.context import Context
from google.adk.events.event_actions import EventActions
from google.adk.workflow import START

from spec_engine.agents.council import (
    council_chair_agent,
    product_reviewer_agent,
    security_reviewer_agent,
    tech_reviewer_agent,
)
from spec_engine.agents.directly_responsible_agent import (
    directly_responsible_agent,
    dra_agent,
)
from spec_engine.agents.tools import (
    update_github_issue,
)


def _get_issue_id(ctx: Any) -> int | None:
    state = getattr(ctx, "state", {}) if hasattr(ctx, "state") else {}
    val = state.get("parent_issue_id") or (
        state.get("issue", {}).get("id") if isinstance(state.get("issue"), dict) else None
    )
    return int(val) if val is not None else None


def _get_user_story(ctx: Any) -> str:
    state = getattr(ctx, "state", {}) if hasattr(ctx, "state") else {}
    return str(state.get("user_story_markdown") or "")


async def _run_agent_helper(agent: Any, input_text: str, ctx: Context) -> str:
    """Helper to run an ADK agent asynchronously and return final output string."""
    last_output = ""
    async for event in agent.run_async(input_text, ctx=ctx):
        if hasattr(event, "output") and event.output:
            last_output = str(event.output)
    return last_output


async def gate_set_session_state(node_input: Any, ctx: Context) -> Event:
    """Entry gate that receives input and initializes session state variables."""
    print("Entry Gate: Initializing session state and starting deliberation flow...")
    initial_state_delta = {
        "latest_critique_notes": "N/A (Initial Pass)",
        "latest_missing_elements": "None",
        "latest_critique_score": 0,
        "latest_critique_is_approved": False,
        "user_story_markdown": "",
        "council_review": [],
        "specifications": {
            "full_spec_markdown": "",
            "revision_summary": "",
            "story_review_rounds": 0,
            "council_review_rounds": 0,
            "council_scores": {
                "product_score": 0,
                "tech_score": 0,
                "security_score": 0,
            },
            "council_notes": "",
            "latest_council_feedback": "",
            "council_approved": False,
        },
    }
    if hasattr(ctx, "state") and isinstance(ctx.state, dict):
        for k, v in initial_state_delta.items():
            ctx.state.setdefault(k, v)

    return Event(output=node_input, actions=EventActions(state_delta=initial_state_delta))


async def council_review_gate(node_input: Any, ctx: Context) -> Event:
    """Executes Product, Tech Architect, and Security Reviewers in parallel, then aggregates feedback via Council Chair."""
    state = getattr(ctx, "state", {}) if hasattr(ctx, "state") else {}
    specifications = state.setdefault("specifications", {}) if isinstance(state.get("specifications"), dict) else {}

    spec_draft = (
        state.get("user_story_markdown")
        or specifications.get("full_spec_markdown")
        or str(node_input)
    )

    print("[Council Review Gate] Executing Product, Tech, and Security Reviewers in parallel...")
    product_out, tech_out, security_out = await asyncio.gather(
        _run_agent_helper(product_reviewer_agent, spec_draft, ctx=ctx),
        _run_agent_helper(tech_reviewer_agent, spec_draft, ctx=ctx),
        _run_agent_helper(security_reviewer_agent, spec_draft, ctx=ctx),
    )

    # Extract structured results from state
    product_data = state.get("product_review_result", {}) if isinstance(state.get("product_review_result"), dict) else {}
    tech_data = state.get("critique_result", {}) if isinstance(state.get("critique_result"), dict) else {}
    security_data = state.get("security_review_result", {}) if isinstance(state.get("security_review_result"), dict) else {}

    product_score = int(product_data.get("invest_score", 0))
    tech_score = int(tech_data.get("score", 0))
    security_score = int(security_data.get("security_score", 0))

    council_payload = f"""
### Product Reviewer Feedback:
- INVEST Score: {product_score}/100
- Approved: {product_data.get('is_approved', False)}
- User Value Rating: {product_data.get('user_value_rating', 'N/A')}
- Scope Feedback: {product_data.get('scope_feedback', 'None')}
- Recommendations: {product_data.get('recommendations', [])}
- Details: {product_out}

### Technical Architect Reviewer Feedback:
- Tech Score: {tech_score}/10
- Approved: {tech_data.get('is_approved', False)}
- Critique Notes: {tech_data.get('critique_notes', 'None')}
- Missing Elements: {tech_data.get('missing_elements', [])}
- Details: {tech_out}

### Security & Compliance Reviewer Feedback:
- Security Score: {security_score}/100
- Approved: {security_data.get('is_approved', False)}
- Vulnerability Concerns: {security_data.get('vulnerability_concerns', [])}
- Compliance Notes: {security_data.get('compliance_notes', 'None')}
- Recommendations: {security_data.get('recommendations', [])}
- Details: {security_out}
"""

    print("[Council Review Gate] Synthesizing parallel reviews via Council Chair...")
    chair_output = await _run_agent_helper(council_chair_agent, council_payload, ctx=ctx)

    rounds = int(specifications.get("council_review_rounds", 0)) + 1

    # Record historical round in council_review list
    history_entry = {
        "council_scores": {
            "product_score": product_score,
            "tech_score": tech_score,
            "security_score": security_score,
        },
        "product_review": product_out,
        "tech_review": tech_out,
        "security_review": security_out,
        "council_notes": chair_output,
    }

    council_history = state.setdefault("council_review", [])
    if isinstance(council_history, list):
        council_history.append(history_entry)

    # Update active snapshot state adhering to Data State Schema in PLANNING_ENGINE_GUIDE.md
    specifications["council_review_rounds"] = rounds
    specifications["full_spec_markdown"] = spec_draft
    specifications["council_notes"] = chair_output
    specifications["latest_council_feedback"] = chair_output
    specifications["council_scores"] = {
        "product_score": product_score,
        "tech_score": tech_score,
        "security_score": security_score,
    }

    # Re-assign top level state for DRA prompt placeholders & state update tracking
    state["latest_critique_notes"] = chair_output
    state["latest_critique_score"] = tech_score
    state["latest_critique_is_approved"] = False
    state["specifications"] = dict(specifications)

    print(
        f"[Council Review Gate] Round {rounds} complete. Scores -> Product: {product_score}/100, Tech: {tech_score}/10, Security: {security_score}/100"
    )

    return Event(
        output=chair_output,
        actions=EventActions(
            state_delta={
                "latest_critique_notes": chair_output,
                "latest_critique_score": tech_score,
                "specifications": dict(specifications),
                "council_review": list(council_history),
            }
        ),
    )


def council_loop_router(ctx: Context) -> Event:
    """Routes back to DRA if rounds < 2, otherwise routes to gate_publish_user_story ('publish')."""
    state = getattr(ctx, "state", {}) if hasattr(ctx, "state") else {}
    specifications = state.get("specifications", {}) if isinstance(state.get("specifications"), dict) else {}
    rounds = int(specifications.get("council_review_rounds", 0))

    print(f"[Council Router] Completed council review round {rounds} / 2.")

    if rounds < 2:
        print(f"[Council Router] Round {rounds} < 2: Routing back to Directly Responsible Agent for revision...")
        return Event(actions=EventActions(route="loop_again"))

    print(f"[Council Router] Fixed 2 rounds completed. Routing to Publish Gate...")
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
            f"[DRA Gate] Automatically updated main GitHub Issue #{parent_id} description with certified User Story."
        )
    except Exception as e:
        print(f"[DRA Gate Warning] Could not auto-update issue #{parent_id}: {e}")

    return Event(output=f"User Story Issue #{parent_id} refined.")


# Backwards compatibility alias for loop_router
loop_router = council_loop_router

root_workflow = Workflow(
    name="agile_github_planning_app",
    edges=[
        (START, gate_set_session_state),
        (gate_set_session_state, directly_responsible_agent),
        (directly_responsible_agent, council_review_gate),
        (council_review_gate, council_loop_router),
        (
            council_loop_router,
            {
                "loop_again": directly_responsible_agent,
                "publish": gate_publish_user_story,
            },
        ),
    ],
)
