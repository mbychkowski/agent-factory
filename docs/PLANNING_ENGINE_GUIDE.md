# ADK Planning Engine Implementation Guide

This guide covers the technical implementation of **Big Loop 1 Stage 1 (Council-Refined Planning)** inside the `agent_engine` service using **Google Agent Development Kit (ADK 2.0)**.

---

## 📁 Agent Directory Structure & Roles

In Stage 1, the **Directly Responsible Agent (DRA)** owns and drafts the specification document, while the **Council Panel** (Product, Tech, Security) reviews it concurrently in parallel and the **Council Chair** synthesizes the feedback:

```
agent_engine/agents/
├── directly_responsible_agent/ # Lead Spec Author (DRA) - Drafts & refines the spec
│   ├── agent.py
│   ├── prompt.py
│   └── schemas.py
├── council/
│   ├── product_reviewer/       # Council Member: Product Manager (INVEST, user value, scope)
│   │   ├── agent.py
│   │   ├── prompt.py
│   │   └── schemas.py
│   ├── tech_reviewer/          # Council Member: Tech Architect (APIs, schemas, complexity)
│   │   ├── agent.py
│   │   ├── prompt.py
│   │   └── schemas.py
│   ├── security_reviewer/      # Council Member: Security Lead (OWASP, auth, compliance)
│   │   ├── agent.py
│   │   ├── prompt.py
│   │   └── schemas.py
│   └── council_chair/          # Council Chair: Synthesizes 3 reviews into 1 revision guide
│       ├── agent.py
│       ├── prompt.py
│       └── schemas.py
├── task_decomposer/            # Stage 2: Swarm Task Orchestrator
│   ├── agent.py
│   ├── prompt.py
│   └── schemas.py
├── agent.py                    # Core ADK Workflow Definition
└── tools.py                    # Multi-Tenant GitHub API & Search Tools
```

---

## 🔄 ADK Parallel Council Gate Code (`agent_engine/agents/agent.py`)

In ADK, the Council Review is implemented as a parallel execution gate using Python's `asyncio.gather` inside an ADK gate function:

```python
import asyncio
from google.adk import Event, Workflow
from google.adk.agents.context import Context
from google.adk.events.event_actions import EventActions
from google.adk.workflow import START, END

# Import Council Agents
from agent_engine.agents.directly_responsible_agent import directly_responsible_agent
from agent_engine.agents.council.product_reviewer import product_reviewer_agent
from agent_engine.agents.council.tech_reviewer import tech_reviewer_agent
from agent_engine.agents.council.security_reviewer import security_reviewer_agent
from agent_engine.agents.council.council_chair import council_chair_agent


async def council_review_gate(node_input: str, ctx: Context) -> Event:
    """Executes Product, Tech Architect, and Security Reviewers in parallel, then aggregates feedback."""
    spec_draft = ctx.state.get("specifications", {}).get(
        "full_spec_markdown", node_input
    )

    # 1. Run all 3 Council Members concurrently in parallel via asyncio.gather
    product_res, tech_res, security_res = await asyncio.gather(
        product_reviewer_agent.run(spec_draft, ctx=ctx),
        tech_reviewer_agent.run(spec_draft, ctx=ctx),
        security_reviewer_agent.run(spec_draft, ctx=ctx),
    )

    # 2. Package all 3 reviews for the Council Chair Aggregator
    council_payload = f"""
    ### Product Reviewer Feedback:
    {product_res.output}

    ### Technical Architect Reviewer Feedback:
    {tech_res.output}

    ### Security & Compliance Reviewer Feedback:
    {security_res.output}
    """

    # 3. Council Chair synthesizes feedback into a single actionable revision document
    chair_response = await council_chair_agent.run(council_payload, ctx=ctx)

    # 4. Increment review round counter & update state
    rounds = (
        ctx.state.setdefault("specifications", {}).get("council_review_rounds", 0) + 1
    )
    ctx.state["specifications"]["council_review_rounds"] = rounds
    ctx.state["specifications"]["council_notes_summarized"] = chair_response.output

    return Event(
        output=chair_response.output,
        actions=EventActions(
            state_delta={"council_notes_summarized": chair_response.output}
        ),
    )


def council_loop_router(ctx: Context) -> Event:
    """Routes back to DRA if rounds < 2, otherwise routes to Human Approval Gate."""
    rounds = ctx.state.get("specifications", {}).get("council_review_rounds", 0)

    if rounds < 2:
        print(
            f"[Council Router] Round {rounds} < 2: Routing back to DRA for revision..."
        )
        return Event(actions=EventActions(route="loop_again"))

    print(f"[Council Router] Fixed 2 rounds completed. Routing to Human Gate 1...")
    return Event(actions=EventActions(route="proceed_to_human_gate"))


root_workflow = Workflow(
    name="agile_spec_planning_app",
    edges=[
        # Phase 1: Directly Responsible Agent drafts initial spec
        (START, gate_set_session_state),
        (gate_set_session_state, directly_responsible_agent),
        # Phase 2: Parallel Council Review Loop
        (directly_responsible_agent, council_review_gate),
        (council_review_gate, council_loop_router),
        (
            council_loop_router,
            {
                "loop_again": directly_responsible_agent,
                "proceed_to_human_gate": human_spec_approval_gate,
            },
        ),
        # Phase 3: Human Gate 1 (Pause for Human Review)
        (
            human_spec_approval_gate,
            {"pause_for_human": END, "proceed_to_swarm": swarm_orchestrator_gate},
        ),
        # Phase 4: Swarm Task Decomposition
        (swarm_orchestrator_gate, breakdown_critic),
        (breakdown_critic, gate_publish_github_epic),
    ],
)
```

---

## 🧠 Architectural Principle: Stateless Council vs. Stateful DRA

1. **Council Members are 100% Stateless Blind Reviewers (`include_contents="none"`)**:
   - Each Council agent (Product, Tech, Security, Council Chair) evaluates the draft specification purely on its present content, as if viewing it for the very first time.
   - They do not retain conversation history or bias from prior rounds. This guarantees objective, repeatable evaluations.

2. **The Directly Responsible Agent (DRA) is Stateful**:
   - The Lead Spec Author (DRA) retains session history and reads `specifications["council_notes"]` and `specifications["revision_summary"]`.
   - The DRA uses this context to address feedback, fill gaps, and log its revision changelog across rounds.

---

## 🛠️ Data State Schema (`ctx.state`)

ADK session state stores structured domain data throughout the planning lifecycle:

```json
{
  "issue": {
    "id": 42,
    "repo": "acme/web-app",
    "title": "Implement OAuth2 Authentication",
    "url": "https://github.com/acme/web-app/issues/42"
  },
  "specifications": {
    "full_spec_markdown": "# FEATURE-101: Implement OAuth2 Authentication\n\n...",
    "revision_summary": "Added OAuth refresh token BDD scenarios, rate limiting NFRs, and CSRF state parameter validation.",
    "council_scores": {
      "product": 92,
      "tech": 88,
      "security": 95
    },
    "council_notes_summarized": "All council members approved with minor recommendations on token expiry NFRs.",
    "council_review_rounds": 2,
    "council_approved": true
  },
  "council_review": [
    {
      "council_scores": {
        "product": 75,
        "tech": 70,
        "security": 80
      },
      "council_notes": {
        "product": "Missing explicit user persona acceptance scenario for token refresh.",
        "tech": "Missing NFR targets for rate limiting and token revocation latency.",
        "security": "Need explicit OAuth state parameter validation to prevent CSRF."
      }
    },
    {
      "council_scores": {
        "product": 92,
        "tech": 88,
        "security": 95
      },
      "council_notes": {
        "product": "All user scenarios clear and testable.",
        "tech": "Architecture grounded with file anchors.",
        "security": "Security controls and OWASP checks satisfied."
      }
    }
  ],
  "task_manifest": [
    {
      "task_id": "TASK-1",
      "title": "Create User & Token DB Migrations",
      "subsystem": "database",
      "status": "pending",
      "acceptance_criteria": [
        "Given PostgreSQL database, When migration 001 runs, Then users and tokens tables exist."
      ],
      "dependencies": []
    }
  ]
}
```
