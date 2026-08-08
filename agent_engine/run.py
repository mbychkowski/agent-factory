import argparse
import asyncio
import os
import sys

from dotenv import load_dotenv
from google.adk import Runner
from google.adk.sessions.in_memory_session_service import InMemorySessionService
from google.genai import types

from agent_engine.agents.agent import root_workflow


async def run_workflow(input_path: str, output_path: str):
    # Read the raw requirements
    if not os.path.exists(input_path):
        print(f"Error: Input file '{input_path}' not found.", file=sys.stderr)
        sys.exit(1)

    with open(input_path, "r", encoding="utf-8") as f:
        raw_requirements = f.read()

    print(
        f"Loaded raw requirements from '{input_path}' ({len(raw_requirements)} bytes)"
    )

    # Initialize services
    session_service = InMemorySessionService()
    runner = Runner(
        node=root_workflow, session_service=session_service, auto_create_session=True
    )

    user_id = "default_user"
    session_id = "default_session"

    # Pre-create session state for single pass batch execution
    session = await session_service.get_session(
        app_name=runner.app_name, user_id=user_id, session_id=session_id
    )
    if not session:
        session = await session_service.create_session(
            app_name=runner.app_name, user_id=user_id, session_id=session_id
        )

    # Construct the starting user message
    new_message = types.Content(
        parts=[
            types.Part(
                text=f"You are running in automated, non-interactive, single-pass mode. Please refine and plan this product requirement into a high-quality User Story with acceptance criteria and technical considerations. Do NOT ask any questions or wait for user confirmation. Make reasonable assumptions for any missing details.\n\nRaw Requirements:\n{raw_requirements}"
            )
        ]
    )

    print("\n--- Starting Sequential Refinement Workflow ---")

    # Execute the workflow
    try:
        async for event in runner.run_async(
            user_id=user_id, session_id=session_id, new_message=new_message
        ):
            # Print streaming thoughts/text from agents
            if event.content and event.content.parts:
                for part in event.content.parts:
                    if part.text:
                        print(part.text, end="", flush=True)

            # Print errors if any are emitted in events
            if event.error_message:
                print(f"\n[Error Event] {event.error_message}", file=sys.stderr)

    except Exception as e:
        print(f"\nExecution failed: {e}", file=sys.stderr)
        sys.exit(1)

    print("\n--- Workflow Execution Completed ---")

    # Fetch the final session state
    session = await session_service.get_session(
        app_name=runner.app_name, user_id=user_id, session_id=session_id
    )
    state = session.state

    # Extract our generated user story
    user_story = state.get("user_story_markdown", "No user story was generated.")

    # Compile the final specification document
    compiled_spec = f"""# Certified User Story & Specification
*Generated automatically by Spec Deliberator Agent*

---

{user_story}
"""

    # Write output to file
    parent_dir = os.path.dirname(output_path)
    if parent_dir:
        os.makedirs(parent_dir, exist_ok=True)

    with open(output_path, "w", encoding="utf-8") as f:
        f.write(compiled_spec)

    print(f"\nSuccessfully compiled and wrote final specification to '{output_path}'")


def main():
    parser = argparse.ArgumentParser(description="Spec Deliberator Agent runner")
    parser.add_argument("input", help="Path to raw requirements draft or prompt file")
    parser.add_argument(
        "-o",
        "--output",
        default="specs/refined_spec.md",
        help="Path to write the finalized spec (Default: specs/refined_spec.md)",
    )

    args = parser.parse_args()

    asyncio.run(run_workflow(args.input, args.output))


if __name__ == "__main__":
    main()
