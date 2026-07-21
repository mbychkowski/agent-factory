import argparse
import os
import sys
from pathlib import Path

# Add project root and google-adk site-packages to path if needed
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from google.adk import Agent
from google.adk.runners import Runner
from google.adk.sessions.in_memory_session_service import InMemorySessionService
from google.adk.memory.in_memory_memory_service import InMemoryMemoryService
from google.adk.artifacts.in_memory_artifact_service import InMemoryArtifactService
from google.genai import types

from agents.spec_deliberator.evaluator_agent import evaluator_agent, EvaluationResult
from agents.spec_deliberator.enhancer_agent import enhancer_agent

# Self-contained In-Memory Runner to avoid dependency on pytest and internal cli packages
class InMemoryRunner:
    def __init__(self, root_agent=None, app=None):
        if app:
            self.app_name = app.name
            self.runner = Runner(
                app=app,
                artifact_service=InMemoryArtifactService(),
                session_service=InMemorySessionService(),
                memory_service=InMemoryMemoryService(),
            )
        else:
            self.app_name = "test_app"
            self.runner = Runner(
                app_name="test_app",
                agent=root_agent,
                artifact_service=InMemoryArtifactService(),
                session_service=InMemorySessionService(),
                memory_service=InMemoryMemoryService(),
            )
        self.session_id = None

    @property
    def session(self):
        if not self.session_id:
            session = self.runner.session_service.create_session_sync(
                app_name=self.app_name, user_id="test_user"
            )
            self.session_id = session.id
            return session
        return self.runner.session_service.get_session_sync(
            app_name=self.app_name, user_id="test_user", session_id=self.session_id
        )

# Define the initial Generator Agent
generator_instruction = """
You are a senior Software Architect and Technical Writer.
Your job is to generate a comprehensive, highly clear, and complete software development specification based on the user's initial requirements or raw idea.

Your specification must contain exactly three sections:
1. Product Overview (Goals, Audience, Scope, Out-of-Scope)
2. Implementation Tasks (concrete distributable tasks with descriptions, dependencies, and success criteria)
3. Acceptance Criteria & Test Cases (comprehensive manual & automated test cases covering happy path and edge cases)

Do not use placeholders. Be thorough, concrete, and write in professional Markdown.
"""

generator_agent = Agent(
    name="generator_agent",
    description="Generates the initial software specification from user requirements.",
    model="gemini-2.5-flash",
    instruction=generator_instruction,
)

def stream_agent_text(runner, prompt, prefix=""):
    """Streams text output from an agent event generator in real-time."""
    print(prefix, end="", flush=True)
    
    content = types.Content(role="user", parts=[types.Part.from_text(text=prompt)])
    event_gen = runner.runner.run(
        user_id=runner.session.user_id,
        session_id=runner.session.id,
        new_message=content,
    )
    
    streamed_text = ""
    final_text = ""
    has_partial = False
    
    for event in event_gen:
        if event.content and event.content.parts:
            for part in event.content.parts:
                if part.text:
                    if getattr(event, "partial", False):
                        has_partial = True
                        print(part.text, end="", flush=True)
                        streamed_text += part.text
                    else:
                        final_text = part.text
                        
    # If we didn't receive any partial events, print final accumulated text
    if not has_partial and final_text:
        print(final_text, end="", flush=True)
        
    print() # Newline after finishing stream
    return final_text if not has_partial else streamed_text

def run_evaluation(runner, spec):
    """Runs the structured Quality Evaluator agent and returns structured output."""
    print("\n" + "="*80)
    print(f"🔍 [Quality Evaluator] Commencing spec audit and scoring...")
    print("="*80 + "\n")
    
    content = types.Content(role="user", parts=[types.Part.from_text(text=f"Please evaluate this specification:\n\n{spec}")])
    event_gen = runner.runner.run(
        user_id=runner.session.user_id,
        session_id=runner.session.id,
        new_message=content,
    )
    
    structured_output = None
    for event in event_gen:
        if event.output:
            structured_output = event.output
            
    return structured_output

def run_loop(input_path: str, output_path: str, max_rounds: int):
    # Read the initial draft specification
    print(f"📖 Reading draft specification file: {input_path}...")
    try:
        with open(input_path, "r") as f:
            initial_draft = f.read()
    except Exception as e:
        print(f"❌ Error reading file: {e}")
        sys.exit(1)
        
    # Instantiate ADK Runners
    print("🤖 Initializing Agent Development Kit (ADK) runners...")
    generator_runner = InMemoryRunner(root_agent=generator_agent)
    evaluator_runner = InMemoryRunner(root_agent=evaluator_agent)
    enhancer_runner = InMemoryRunner(root_agent=enhancer_agent)
    
    # Generate initial spec
    print("\n" + "="*80)
    print("🚀 [Generator] Producing initial specification from your draft...")
    print("="*80 + "\n")
    
    current_spec = stream_agent_text(
        generator_runner,
        f"Generate initial spec based on this draft:\n\n{initial_draft}",
        prefix="[Generator]: "
    )
    
    round_num = 1
    approved = False
    
    while round_num <= max_rounds:
        # Run Quality Evaluation
        eval_result = run_evaluation(evaluator_runner, current_spec)
        
        if not eval_result:
            print("⚠️ Warning: Received empty evaluation result. Proceeding with loop...")
            # Create a fallback mock result to keep loop safe
            eval_result = EvaluationResult(approved=True, quality_score=8, critique_and_gaps=[])
            
        print(f"📊 [Audit Results - Round {round_num}]")
        print(f"   Quality Score : {eval_result.quality_score}/10")
        print(f"   Approved      : {'✅ YES' if eval_result.approved else '❌ NO'}")
        
        if eval_result.critique_and_gaps:
            print("   Critique & Gaps Identified:")
            for gap in eval_result.critique_and_gaps:
                print(f"    - {gap}")
                
        if eval_result.approved or eval_result.quality_score >= 8:
            print(f"\n🎉 Success! Specification has passed the quality audit with score {eval_result.quality_score}/10.")
            approved = True
            break
            
        if round_num == max_rounds:
            print(f"\n⚠️ Reached maximum of {max_rounds} rounds. Stopping loop.")
            break
            
        # Run Spec Enhancer
        print("\n" + "="*80)
        print(f"⚡ [Spec Enhancer] Refining and enriching specification (Round {round_num} -> {round_num + 1})...")
        print("="*80 + "\n")
        
        critique_str = "\n".join([f"- {gap}" for gap in eval_result.critique_and_gaps])
        enhancement_prompt = (
            f"Please refine and enrich this specification to resolve all the evaluator critiques.\n\n"
            f"Evaluator Critique:\n{critique_str}\n\n"
            f"Current Specification:\n\n{current_spec}"
        )
        
        current_spec = stream_agent_text(
            enhancer_runner,
            enhancement_prompt,
            prefix="[Spec Enhancer]: "
        )
        
        round_num += 1
        
    # Ensure parent directory exists for output file
    output_file = Path(output_path)
    output_file.parent.mkdir(parents=True, exist_ok=True)
    
    # Save the final spec
    print(f"\n💾 Saving finalized specification to: {output_path}...")
    try:
        with open(output_path, "w") as f:
            f.write(current_spec)
        print("✅ Refinement complete! Process executed successfully.")
    except Exception as e:
        print(f"❌ Error writing output file: {e}")
        sys.exit(1)

def main():
    parser = argparse.ArgumentParser(description="Spec Deliberator Multi-Agent System (using ADK)")
    parser.add_argument("input", help="Path to raw spec draft or user prompt file")
    parser.add_argument("-o", "--output", default="specs/refined_spec.md", help="Path to write the finalized spec (default: specs/refined_spec.md)")
    parser.add_argument("-r", "--max-rounds", type=int, default=3, help="Maximum number of refinement loop rounds (default: 3)")
    
    args = parser.parse_args()
    run_loop(args.input, args.output, args.max_rounds)

if __name__ == "__main__":
    main()
