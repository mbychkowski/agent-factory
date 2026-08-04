import asyncio
import json
from typing import Any
from google.adk import Workflow, Event
from google.adk.agents.context import Context
from google.adk.events.event_actions import EventActions
from google.adk.workflow import START

# Import Core Spec Agents
from agent_engine.agents.deliberation_facilitator.agent import root_agent as deliberation_facilitator
from agent_engine.agents.story_refiner.agent import root_agent as user_story_refiner
from agent_engine.agents.technical_designer.agent import root_agent as technical_designer
from agent_engine.agents.task_planner.agent import root_agent as task_planner

# Import Peer Review Critique Agents
from agent_engine.agents.critique.story_critic import story_critic_agent as story_critic
from agent_engine.agents.critique.design_critic import design_critic_agent as design_critic


async def facilitator_gate(node_input: Any, ctx: Context) -> Event:
    """
    Evaluates incoming human input using the deliberation_facilitator.
    Filters noise, answers meta-questions, asks clarifying questions on conflicts,
    and passes clean synthesized deltas to downstream spec agents.
    """
    parent_id = ctx.state.get("parent_issue_id")
    if parent_id:
        try:
            from agent_engine.agents.tools import sync_github_issue_labels
            current_phase = "phase:user-story"
            if ctx.state.get("tech_design_completed"):
                current_phase = "phase:task-planning"
            elif ctx.state.get("human_story_approved"):
                current_phase = "phase:technical-design"
            sync_github_issue_labels(int(parent_id), "agent:in-progress", current_phase, ctx=ctx)
        except Exception as e:
            print(f"[Facilitator Gate Label Sync Warning] {e}")

    is_initial_start = not parent_id and not ctx.state.get("user_story_markdown")

    if is_initial_start:
        print("Facilitator Gate: Initial spec creation detected. Proceeding to User Story Refiner...")
        return Event(
            output=node_input,
            actions=EventActions(route="user_story_refiner")
        )

    print("Facilitator Gate: Multi-human turn detected. Invoking deliberation_facilitator for input triage...")
    return Event(
        output=node_input,
        actions=EventActions(route="deliberation_facilitator")
    )


async def gate_after_facilitator(node_input: Any, ctx: Context) -> Event:
    """
    Processes the Facilitator Agent's triage output and decides whether to route
    to downstream spec agents or return a direct response to the human channel.
    """
    raw_output = node_input if isinstance(node_input, str) else str(node_input)
    print(f"\n--- Facilitator Triage Output ---\n{raw_output}\n---------------------------------\n")

    classification = "ACTIONABLE_SPEC_FEEDBACK"
    target_phase = "NONE"
    synthesized_delta = raw_output
    human_response = None

    try:
        if isinstance(node_input, dict):
            triage_data = node_input
        else:
            triage_data = json.loads(raw_output)

        classification = triage_data.get("classification", "ACTIONABLE_SPEC_FEEDBACK")
        target_phase = triage_data.get("target_phase", "NONE")
        synthesized_delta = triage_data.get("synthesized_delta", raw_output)
        human_response = triage_data.get("human_response")

        if triage_data.get("is_gate_approval"):
            # Mark human approval in state based on current phase
            if not ctx.state.get("human_story_approved"):
                ctx.state["human_story_approved"] = True
                print("Facilitator: Human approval confirmed for User Story (Milestone 1).")
            elif not ctx.state.get("human_design_approved"):
                ctx.state["human_design_approved"] = True
                print("Facilitator: Human approval confirmed for Technical Design (Milestone 2).")

    except Exception:
        classification = "ACTIONABLE_SPEC_FEEDBACK"

    if classification == "NOISE_OFF_TOPIC":
        print("Facilitator: Message classified as NOISE_OFF_TOPIC. Suppressing downstream agent execution.")
        return Event(output=human_response or "Message acknowledged (classified as non-spec noise).")

    elif classification == "META_QUESTION":
        print("Facilitator: Message classified as META_QUESTION. Responding directly to human.")
        return Event(output=human_response or "Status query answered.")

    elif classification == "UNRESOLVED_DISCUSSION":
        print("Facilitator: Message classified as UNRESOLVED_DISCUSSION. Prompting human channel for clarification.")
        return Event(output=human_response or "Please clarify consensus before updating spec.")

    # ACTIONABLE_SPEC_FEEDBACK
    print(f"Facilitator: Actionable spec feedback detected. Target phase: {target_phase}.")
    ctx.state["synthesized_feedback"] = synthesized_delta or raw_output

    if target_phase == "USER_STORY":
        return Event(output=synthesized_delta, actions=EventActions(route="user_story_refiner"))
    elif target_phase == "TECHNICAL_DESIGN":
        return Event(output=synthesized_delta, actions=EventActions(route="technical_designer"))
    elif target_phase == "TASK_PLANNING":
        return Event(output=synthesized_delta, actions=EventActions(route="task_planner"))
    else:
        return Event(output=synthesized_delta, actions=EventActions(route="routing_gate"))


async def gate_story_peer_review(node_input: Any, ctx: Context) -> Event:
    """
    Triggers story_critic to review the drafted User Story before publishing to GitHub.
    """
    user_story = ctx.state.get("user_story_markdown", "")
    if not user_story:
        print("Story Peer Review: No user story found in state yet. Returning.")
        return Event(output=node_input)

    # Check if already peer reviewed
    if ctx.state.get("story_peer_reviewed"):
        print("Story Peer Review: Already peer-reviewed and approved. Proceeding to GitHub publish gate.")
        return Event(output=user_story, actions=EventActions(route="gate_after_story_refiner"))

    print("Story Peer Review: Routing story draft to story_critic (Technical Architect) for review...")
    review_prompt = f"Please perform a technical peer review on this drafted User Story:\n\n{user_story}"
    return Event(output=review_prompt, actions=EventActions(route="story_critic"))


async def gate_after_story_critic(node_input: Any, ctx: Context) -> Event:
    """
    Evaluates story_critic output. If approved, marks peer_reviewed=True.
    If rejected, sends critique back to user_story_refiner for revision (up to 2 rounds).
    """
    raw_output = node_input if isinstance(node_input, str) else str(node_input)
    is_approved = True
    critique_notes = ""

    try:
        data = node_input if isinstance(node_input, dict) else json.loads(raw_output)
        is_approved = data.get("is_approved", True)
        critique_notes = data.get("critique_notes", "")
    except Exception:
        is_approved = True

    review_rounds = ctx.state.get("story_review_rounds", 0)

    if is_approved or review_rounds >= 2:
        print(f"Story Peer Review Passed (Score / Rounds: {review_rounds}). Proceeding to GitHub Issue Creation.")
        ctx.state["story_peer_reviewed"] = True
        return Event(actions=EventActions(route="gate_after_story_refiner"))
    else:
        ctx.state["story_review_rounds"] = review_rounds + 1
        print(f"Story Peer Review Requesting Revision (Round {review_rounds + 1}): {critique_notes}")
        revision_prompt = (
            f"The Technical Architect reviewed your drafted User Story and requested the following improvements:\n"
            f"{critique_notes}\n\n"
            "Please revise the User Story to address these gaps."
        )
        return Event(output=revision_prompt, actions=EventActions(route="user_story_refiner"))


async def gate_after_story_refiner(ctx: Context) -> Event:
    """
    Milestone 1 Gate: Verifies Parent Issue creation, updates main issue description on GitHub, and checks for Human Approval.
    """
    print("Cooling down for 4 seconds to manage API rate limits...")
    await asyncio.sleep(4)

    parent_id = ctx.state.get("parent_issue_id")
    user_story = ctx.state.get("user_story_markdown", "")

    if parent_id and user_story:
        try:
            from agent_engine.agents.tools import update_github_issue
            update_github_issue(issue_id=int(parent_id), body=user_story, ctx=ctx)
            print(f"[Milestone 1 Gate] Automatically updated main GitHub Issue #{parent_id} description with certified User Story.")
        except Exception as e:
            print(f"[Milestone 1 Gate Warning] Could not auto-update issue #{parent_id}: {e}")

    # Check for Human Approval (or single-pass mode override)
    human_approved = ctx.state.get("human_story_approved", False) or ctx.state.get("single_pass_mode", False)

    if parent_id and human_approved:
        print(f"Milestone 1 Passed: Parent Issue #{parent_id} confirmed & Human Approved. Proceeding to Technical Design.")
        try:
            from agent_engine.agents.tools import sync_github_issue_labels
            sync_github_issue_labels(int(parent_id), "agent:in-progress", "phase:technical-design", ctx=ctx)
        except Exception as e:
            print(f"[Milestone 1 Gate Label Sync Warning] {e}")

        guided_input = (
            "The User Story has been peer-reviewed and signed off by the human on GitHub. "
            f"Please formulate your RFC Technical Design for Issue #{parent_id}.\n\n"
            f"User Story:\n{user_story}"
        )
        return Event(output=guided_input, actions=EventActions(route="technical_designer"))

    elif parent_id:
        print(f"Milestone 1 Gate: Parent Issue #{parent_id} updated on GitHub. WAITING FOR HUMAN APPROVAL on GitHub.")
        try:
            from agent_engine.agents.tools import sync_github_issue_labels
            sync_github_issue_labels(int(parent_id), "agent:awaiting-human-lgtm", "phase:user-story", ctx=ctx)
        except Exception as e:
            print(f"[Milestone 1 Gate Label Sync Warning] {e}")

        return Event(output=f"User Story Issue #{parent_id} updated with certified spec. Awaiting human approval on GitHub before drafting RFC.")

    print("Gate Evaluating: Parent Issue ID not found. Pausing execution.")
    return Event()


async def gate_design_peer_review(node_input: Any, ctx: Context) -> Event:
    """
    Triggers design_critic to review the drafted RFC Technical Design before publishing comment.
    """
    tech_design = ctx.state.get("tech_design_markdown", "")
    if not tech_design:
        return Event(output=node_input)

    if ctx.state.get("design_peer_reviewed"):
        print("Design Peer Review: Already peer-reviewed and approved. Proceeding to GitHub Comment gate.")
        return Event(output=tech_design, actions=EventActions(route="gate_after_technical_designer"))

    print("Design Peer Review: Routing RFC Technical Design draft to design_critic (Engineering Lead) for review...")
    review_prompt = f"Please perform a feasibility peer review on this RFC Technical Design draft:\n\n{tech_design}"
    return Event(output=review_prompt, actions=EventActions(route="design_critic"))


async def gate_after_design_critic(node_input: Any, ctx: Context) -> Event:
    """
    Evaluates design_critic output. If approved, marks peer_reviewed=True.
    If rejected, sends critique back to technical_designer for revision (up to 2 rounds).
    """
    raw_output = node_input if isinstance(node_input, str) else str(node_input)
    is_approved = True
    critique_notes = ""

    try:
        data = node_input if isinstance(node_input, dict) else json.loads(raw_output)
        is_approved = data.get("is_approved", True)
        critique_notes = data.get("critique_notes", "")
    except Exception:
        is_approved = True

    review_rounds = ctx.state.get("design_review_rounds", 0)

    if is_approved or review_rounds >= 2:
        print(f"Design Peer Review Passed (Rounds: {review_rounds}). Proceeding to GitHub RFC Comment Publishing.")
        ctx.state["design_peer_reviewed"] = True
        return Event(actions=EventActions(route="gate_after_technical_designer"))
    else:
        ctx.state["design_review_rounds"] = review_rounds + 1
        print(f"Design Peer Review Requesting Revision (Round {review_rounds + 1}): {critique_notes}")
        revision_prompt = (
            f"The Engineering Lead reviewed your RFC Technical Design and requested the following improvements:\n"
            f"{critique_notes}\n\n"
            "Please revise the RFC Technical Design to address these architectural gaps."
        )
        return Event(output=revision_prompt, actions=EventActions(route="technical_designer"))


async def gate_after_technical_designer(ctx: Context) -> Event:
    """
    Milestone 2 Gate: Verifies RFC Comment publishing and checks for Human Approval sign-off.
    """
    print("Cooling down for 4 seconds to manage API rate limits...")
    await asyncio.sleep(4)

    tech_design_id = ctx.state.get("tech_design_comment_id")
    parent_id = ctx.state.get("parent_issue_id")
    tech_design = ctx.state.get("tech_design_markdown", "")
    human_approved = ctx.state.get("human_design_approved", False) or ctx.state.get("single_pass_mode", False)

    if ctx.state.get("tech_design_completed") and tech_design_id and human_approved:
        print(f"Milestone 2 Passed: RFC Comment #{tech_design_id} confirmed & Human Approved. Proceeding to Task Planner.")
        if parent_id:
            try:
                from agent_engine.agents.tools import sync_github_issue_labels
                sync_github_issue_labels(int(parent_id), "agent:in-progress", "phase:task-planning", ctx=ctx)
            except Exception as e:
                print(f"[Milestone 2 Gate Label Sync Warning] {e}")

        return Event(output=tech_design, actions=EventActions(route="task_planner"))

    elif tech_design_id:
        print(f"Milestone 2 Gate: RFC Design Comment #{tech_design_id} published on GitHub. WAITING FOR HUMAN APPROVAL on GitHub.")
        if parent_id:
            try:
                from agent_engine.agents.tools import sync_github_issue_labels
                sync_github_issue_labels(int(parent_id), "agent:awaiting-human-lgtm", "phase:technical-design", ctx=ctx)
            except Exception as e:
                print(f"[Milestone 2 Gate Label Sync Warning] {e}")

        return Event(output=f"RFC Design Comment #{tech_design_id} published. Awaiting human approval on GitHub before creating task sub-issues.")

    print("Gate 2 Evaluating: Design spec comment not found. Pausing execution.")
    return Event()


async def gate_after_task_planner(node_input: Any, ctx: Context) -> Event:
    """
    Milestone 3 Gate: Marks the workflow and parent issue labels as completed after Task Planner finishes.
    """
    parent_id = ctx.state.get("parent_issue_id")
    if parent_id:
        try:
            from agent_engine.agents.tools import sync_github_issue_labels
            sync_github_issue_labels(int(parent_id), "agent:completed", "phase:task-planning", ctx=ctx)
            print(f"[Milestone 3 Gate] Marked GitHub Issue #{parent_id} as agent:completed!")
        except Exception as e:
            print(f"[Milestone 3 Gate Label Sync Warning] {e}")

    return Event(output=node_input)


async def routing_gate(node_input: Any, ctx: Context) -> Event:
    """Routes the incoming user turn based on current workflow state."""
    parent_id = ctx.state.get("parent_issue_id")
    tech_design_id = ctx.state.get("tech_design_comment_id")

    if not parent_id:
        return Event(output=node_input, actions=EventActions(route="user_story_refiner"))
    elif not tech_design_id:
        user_story = ctx.state.get("user_story_markdown", "")
        return Event(output=f"User Story:\n{user_story}", actions=EventActions(route="technical_designer"))
    else:
        tech_design = ctx.state.get("tech_design_markdown", "")
        return Event(output=tech_design, actions=EventActions(route="task_planner"))


root_workflow = Workflow(
    name="agile_github_planning_app",
    edges=[
        (START, facilitator_gate),
        (facilitator_gate, {
            "routing_gate": routing_gate,
            "deliberation_facilitator": deliberation_facilitator,
            "user_story_refiner": user_story_refiner,
        }),
        (deliberation_facilitator, gate_after_facilitator),
        (gate_after_facilitator, {
            "routing_gate": routing_gate,
            "user_story_refiner": user_story_refiner,
            "technical_designer": technical_designer,
            "task_planner": task_planner,
        }),
        (user_story_refiner, gate_story_peer_review),
        (gate_story_peer_review, {
            "story_critic": story_critic,
            "gate_after_story_refiner": gate_after_story_refiner,
        }),
        (story_critic, gate_after_story_critic),
        (gate_after_story_critic, {
            "user_story_refiner": user_story_refiner,
            "gate_after_story_refiner": gate_after_story_refiner,
        }),
        (gate_after_story_refiner, {
            "technical_designer": technical_designer,
        }),
        (technical_designer, gate_design_peer_review),
        (gate_design_peer_review, {
            "design_critic": design_critic,
            "gate_after_technical_designer": gate_after_technical_designer,
        }),
        (design_critic, gate_after_design_critic),
        (gate_after_design_critic, {
            "technical_designer": technical_designer,
            "gate_after_technical_designer": gate_after_technical_designer,
        }),
        (gate_after_technical_designer, {
            "task_planner": task_planner,
        }),
        (task_planner, gate_after_task_planner),
        (routing_gate, {
            "user_story_refiner": user_story_refiner,
            "technical_designer": technical_designer,
            "task_planner": task_planner,
        }),
    ]
)