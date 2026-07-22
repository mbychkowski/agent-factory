import argparse
import asyncio
import os
import sys
from dotenv import load_dotenv

from google.genai import types
from google.adk import Runner
from google.adk.sessions.in_memory_session_service import InMemorySessionService
from agents.agent import root_workflow


async def run_workflow(input_path: str, output_path: str):
    # Load .env file
    load_dotenv()

    # Read the raw requirements
    if not os.path.exists(input_path):
        print(f"Error: Input file '{input_path}' not found.", file=sys.stderr)
        sys.exit(1)

    with open(input_path, "r", encoding="utf-8") as f:
        raw_requirements = f.read()

    print(f"Loaded raw requirements from '{input_path}' ({len(raw_requirements)} bytes)")

    # Initialize services
    session_service = InMemorySessionService()
    runner = Runner(
        node=root_workflow,
        session_service=session_service,
        auto_create_session=True
    )

    user_id = "default_user"
    session_id = "default_session"

    # Construct the starting user message
    new_message = types.Content(
        parts=[types.Part(text=f"You are running in automated, non-interactive, single-pass mode. Please refine and plan this product requirement immediately. Do NOT ask any questions or wait for user confirmation. Instead, make reasonable assumptions for any missing details and call the 'create_github_issue' tool directly to finalize the user story on your first turn.\n\nRaw Requirements:\n{raw_requirements}")]
    )

    print("\n--- Starting Sequential Refinement Workflow ---")
    
    # Execute the workflow
    try:
        async for event in runner.run_async(
            user_id=user_id,
            session_id=session_id,
            new_message=new_message
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
    session = await session_service.get_session(app_name=runner.app_name, user_id=user_id, session_id=session_id)
    state = session.state

    # Extract our generated specifications
    user_story = state.get("user_story_markdown", "No user story was generated.")
    tech_design = state.get("tech_design_markdown", "No technical design specification was generated.")
    
    # Extract the final output event from the task planner (the task list)
    task_plan = "No execution plan table was generated."
    for event in reversed(session.events):
        if event.author == "model" and event.content and event.content.parts:
            texts = [p.text for p in event.content.parts if p.text]
            combined_text = "".join(texts)
            if "Execution Plan" in combined_text or "Comprehensive Task Table" in combined_text:
                task_plan = combined_text
                break

    # Compile the final unified specification document
    compiled_spec = f"""# Compiled Product Specification & Execution Plan
*Generated automatically by Spec Deliberator Agent*

---

## Part 1: User Story & Acceptance Criteria
{user_story}

---

## Part 2: RFC Technical Design
{tech_design}

---

## Part 3: Task Breakdown & Execution Plan
{task_plan}
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
    parser.add_argument("-o", "--output", default="specs/refined_spec.md", help="Path to write the finalized spec (Default: specs/refined_spec.md)")
    parser.add_argument("-r", "--max-rounds", type=int, default=10, help="Maximum rounds (Ignored, kept for backward compatibility)")

    args = parser.parse_args()

    asyncio.run(run_workflow(args.input, args.output))


if __name__ == "__main__":
    main()
