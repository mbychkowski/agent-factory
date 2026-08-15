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
)
from spec_engine.agents.state import AgentSessionState, ensure_session_state
from spec_engine.agents.tools import update_github_issue


def _extract_dict(val: Any) -> dict[str, Any]:
    """Safely extracts a dictionary from a Pydantic model or dict."""
    if hasattr(val, "model_dump"):
        return val.model_dump()
    if isinstance(val, dict):
        return val
    return {}


def _get_issue_id(ctx: Any) -> int | None:
    state = getattr(ctx, "state", {}) if hasattr(ctx, "state") else {}
    issue_dict = state.get("issue")
    val = state.get("parent_issue_id") or (
        issue_dict.get("id") if isinstance(issue_dict, dict) else None
    )
    return int(val) if val is not None else None


def _get_spec(ctx: Any) -> str:
    state = getattr(ctx, "state", {}) if hasattr(ctx, "state") else {}
    spec = state.get("specifications")
    specifications = spec if isinstance(spec, dict) else {}
    return str(specifications.get("full_spec_markdown") or "")


from google.genai import types


async def _run_agent_helper(agent: Any, input_text: str, parent_ctx: Any = None) -> str:
    """Helper to run an ADK agent asynchronously and return final output string."""
    last_output = ""
    if parent_ctx and hasattr(parent_ctx, "model_copy"):
        user_content = (
            types.Content(parts=[types.Part(text=input_text)])
            if isinstance(input_text, str)
            else input_text
        )
        sub_ctx = parent_ctx.model_copy(update={"user_content": user_content})
        async for event in agent.run_async(sub_ctx):
            if hasattr(event, "output") and event.output:
                last_output = str(event.output)
            elif hasattr(event, "content") and event.content and event.content.parts:
                for part in event.content.parts:
                    if part.text:
                        last_output += part.text
    return last_output


async def gate_set_session_state(node_input: Any, ctx: Context) -> Event:
    """Entry gate that receives input and initializes session state variables."""
    print("Entry Gate: Initializing session state and starting deliberation flow...")
    initial_state_delta = AgentSessionState().model_dump()
    if hasattr(ctx, "state") and isinstance(ctx.state, dict):
        ensure_session_state(ctx.state)

    return Event(
        output=node_input, actions=EventActions(state_delta=initial_state_delta)
    )


async def council_review_gate(node_input: Any, ctx: Context) -> Event:
    """Executes Product, Tech Architect, and Security Reviewers in parallel, then aggregates feedback via Council Chair."""
    state = getattr(ctx, "state", {}) if hasattr(ctx, "state") else {}
    ensure_session_state(state)
    specifications = state.get("specifications", {})
    if not isinstance(specifications, dict):
        specifications = {}

    raw_spec = specifications.get("full_spec_markdown")
    if not raw_spec and hasattr(node_input, "full_spec_markdown"):
        raw_spec = node_input.full_spec_markdown
    elif not raw_spec and isinstance(node_input, dict):
        raw_spec = node_input.get("full_spec_markdown")

    spec_draft = str(raw_spec or node_input or "")

    print(
        "[Council Review Gate] Executing Product, Tech, and Security Reviewers in parallel..."
    )
    product_out, tech_out, security_out = await asyncio.gather(
        _run_agent_helper(product_reviewer_agent, spec_draft, parent_ctx=ctx),
        _run_agent_helper(tech_reviewer_agent, spec_draft, parent_ctx=ctx),
        _run_agent_helper(security_reviewer_agent, spec_draft, parent_ctx=ctx),
    )

    council_payload = f"""
### Product Reviewer Feedback:
{product_out}

### Technical Architect Reviewer Feedback:
{tech_out}

### Security & Compliance Reviewer Feedback:
{security_out}
"""

    print("[Council Review Gate] Synthesizing parallel reviews via Council Chair...")
    chair_output = await _run_agent_helper(
        council_chair_agent, council_payload, parent_ctx=ctx
    )

    # Extract structured results safely supporting Pydantic outputs
    product_data = _extract_dict(state.get("product_review_result"))
    tech_data = _extract_dict(state.get("tech_review_result"))
    security_data = _extract_dict(state.get("security_review_result"))
    chair_data = _extract_dict(state.get("council_chair_result"))

    product_score = int(product_data.get("invest_score", 0))
    tech_score = int(tech_data.get("tech_score") or tech_data.get("score") or 0)
    security_score = int(security_data.get("security_score", 0))
    council_approved = bool(chair_data.get("overall_approved", False))

    rounds = int(specifications.get("council_review_rounds", 0)) + 1

    history_entry = {
        "council_scores": {
            "product": product_score,
            "tech": tech_score,
            "security": security_score,
        },
        "council_notes": {
            "product": product_out,
            "tech": tech_out,
            "security": security_out,
        },
    }

    council_history = list(state.get("council_review", []))
    council_history.append(history_entry)

    updated_specifications = {
        **specifications,
        "council_review_rounds": rounds,
        "full_spec_markdown": spec_draft,
        "council_notes_summarized": chair_output,
        "council_scores": {
            "product": product_score,
            "tech": tech_score,
            "security": security_score,
        },
        "council_approved": council_approved,
    }

    state["specifications"] = updated_specifications
    state["council_review"] = council_history

    print(
        f"[Council Review Gate] Round {rounds} complete. Scores -> Product: {product_score}/100, Tech: {tech_score}/100, Security: {security_score}/100"
    )

    return Event(
        output=chair_output,
        actions=EventActions(
            state_delta={
                "specifications": updated_specifications,
                "council_review": council_history,
            }
        ),
    )


def council_loop_router(node_input: Any, ctx: Context) -> Event:
    """Routes back to DRA if rounds < 2, otherwise routes to gate_publish_spec ('publish')."""
    state = getattr(ctx, "state", {}) if hasattr(ctx, "state") else {}
    spec = state.get("specifications")
    specifications = spec if isinstance(spec, dict) else {}
    rounds = int(specifications.get("council_review_rounds", 0))

    print(f"[Council Router] Completed council review round {rounds} / 2.")

    if rounds < 2:
        print(
            f"[Council Router] Round {rounds} < 2: Routing back to Directly Responsible Agent for revision..."
        )
        return Event(actions=EventActions(route="loop_again"))

    print("[Council Router] Fixed 2 rounds completed. Routing to Publish Gate...")
    return Event(actions=EventActions(route="publish"))


async def gate_publish_spec(node_input: Any, ctx: Context) -> Event:
    """Updates main issue description on GitHub with the refined specification."""
    parent_id = _get_issue_id(ctx)
    if not parent_id:
        print("Gate Evaluating: Parent Issue ID not found. Finishing turn.")
        return Event()

    spec_markdown = _get_spec(ctx)
    if not spec_markdown:
        raise ValueError(
            "Specification content missing from session state when attempting to publish to GitHub."
        )

    try:
        update_github_issue(issue_id=int(parent_id), body=spec_markdown, ctx=ctx)
        print(
            f"[DRA Gate] Automatically updated main GitHub Issue #{parent_id} description with certified Specification."
        )
    except Exception as e:  # noqa: BLE001
        print(f"[DRA Gate Warning] Could not auto-update issue #{parent_id}: {e}")

    return Event(output=f"Specification Issue #{parent_id} refined.")


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
                "publish": gate_publish_spec,
            },
        ),
    ],
)
