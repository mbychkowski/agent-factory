import asyncio
from google.adk import Workflow, Event
from google.adk.agents.context import Context
from google.adk.events.event_actions import EventActions
from google.adk.workflow import START

from typing import Any

# Import the agents
from agents.story_refiner.agent import root_agent as user_story_refiner
from agents.technical_designer.agent import root_agent as technical_designer
from agents.task_planner.agent import root_agent as task_planner


async def routing_gate(node_input: Any, ctx: Context) -> Event:
    """Routes the incoming user turn to the correct node based on the current state."""
    parent_id = ctx.state.get("parent_issue_id")
    tech_design_id = ctx.state.get("tech_design_comment_id")

    if not parent_id:
        print(f"Routing Gate: No issue found. Routing to User Story Refiner with input: {node_input}")
        return Event(
            output=node_input,
            actions=EventActions(route="user_story_refiner")
        )
    elif not tech_design_id:
        print("Routing Gate: Issue found, but no tech design comment. Routing to Technical Designer.")
        user_story = ctx.state.get("user_story_markdown", "")
        guided_input = (
            "You are working on the technical design phase. "
            f"The active User Story is:\n{user_story}"
        )
        return Event(
            output=guided_input,
            actions=EventActions(route="technical_designer")
        )
    else:
        print("Routing Gate: Tech design comment found. Routing to Task Planner.")
        tech_design = ctx.state.get("tech_design_markdown", "")
        return Event(
            output=tech_design,
            actions=EventActions(route="task_planner")
        )


async def gate_after_story_refiner(ctx: Context) -> Event:
    """Evaluates whether the user story refiner successfully created the issue."""
    # Introduce a short cooling-off period to prevent Vertex AI / Gemini API 429 rate limits
    print("Cooling down for 6 seconds to manage API rate limits...")
    await asyncio.sleep(6)

    parent_id = ctx.state.get("parent_issue_id")
    user_story = ctx.state.get("user_story_markdown", "")

    if parent_id:
        print(f"Gate Passed: Parent Issue #{parent_id} confirmed. Proceeding to Technical Design.")
        ctx.route = "technical_designer"
        
        # Guide the technical designer to call the publish tool in automated single-pass mode
        guided_input = (
            "You are running in an automated, non-interactive, single-pass pipeline. "
            "Please analyze the user story below, formulate your technical design, "
            f"and immediately invoke your native `add_design_comment` function tool (with issue_id={parent_id}) "
            "to publish your finalized RFC technical design comment on your first turn.\n"
            "CRITICAL: Do NOT write python code, print statements, or try to run scripts to call the tool. "
            "You must trigger it using your native function-calling/tool-calling block.\n\n"
            f"User Story:\n{user_story}"
        )
        return Event(
            output=guided_input,
            actions=EventActions(route="technical_designer")
        )

    # In interactive chat mode, pause execution for this turn so the user can respond to the refiner
    print("Gate Evaluating: Parent Issue ID not found in state. Pausing execution to wait for user collaboration.")
    return Event()


async def gate_after_technical_designer(ctx: Context) -> Event:
    """Evaluates whether the technical designer successfully published the design comment."""
    # Introduce a short cooling-off period to prevent Vertex AI / Gemini API 429 rate limits
    print("Cooling down for 6 seconds to manage API rate limits...")
    await asyncio.sleep(6)

    tech_design_id = ctx.state.get("tech_design_comment_id")
    tech_design = ctx.state.get("tech_design_markdown", "")

    if ctx.state.get("tech_design_completed") and tech_design_id:
        print(f"Gate 2 Passed: Design spec comment #{tech_design_id} verified on GitHub.")
        ctx.route = "task_planner"
        return Event(
            output=tech_design,
            actions=EventActions(route="task_planner")
        )

    # In interactive chat mode, pause execution for this turn so the user can respond to the designer
    print("Gate 2 Evaluating: Design spec comment not found on GitHub. Pausing execution to wait for user collaboration.")
    return Event()


root_workflow = Workflow(
    name="agile_github_planning_app",
    edges=[
        (START, routing_gate),
        (routing_gate, {
            "user_story_refiner": user_story_refiner,
            "technical_designer": technical_designer,
            "task_planner": task_planner,
        }),
        (user_story_refiner, gate_after_story_refiner),
        (gate_after_story_refiner, {
            "technical_designer": technical_designer,
        }),
        (technical_designer, gate_after_technical_designer),
        (gate_after_technical_designer, {
            "task_planner": task_planner,
        }),
    ]
)