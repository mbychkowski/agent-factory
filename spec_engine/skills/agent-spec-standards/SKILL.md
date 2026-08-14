---
name: agent-spec-standards
description: Enterprise standards, 6 Pillars of Agent-Executable Specs, BDD templates, machine verification protocols, and execution guardrails for AI code execution.
---

# Enterprise Standards for Agent-Executable Code Specifications

This document defines the official quality standards, layout, BDD templates, and machine verification protocols for creating technical specifications that downstream AI code execution agents and swarms can execute deterministically.

---

## 1. The 6 Pillars of an Agent-Executable Spec

Unlike specs written solely for human engineers, specifications meant for AI code execution agents must be explicit, machine-verifiable, and spatially anchored to prevent context drift and hallucinations.

```
┌────────────────────────────────────────────────────────────────────────┐
│                        6 Pillars of an Agent Spec                       │
├───────────────────┬───────────────────┬────────────────────────────────┤
│ 1. File & Symbol  │ 2. Executable     │ 3. Explicit                    │
│    Anchoring      │    BDD Criteria   │    Boundaries                  │
├───────────────────┼───────────────────┼────────────────────────────────┤
│ 4. Deterministic  │ 5. Schema & State │ 6. Concrete                    │
│    Verification   │    Contracts      │    Decomposability             │
└───────────────────┴───────────────────┴────────────────────────────────┘
```

1. **File & Symbol Anchoring:** Every requirement must cite explicit file paths (e.g. `spec_engine/agents/agent.py`), target classes, methods, schema definitions, and module imports to eliminate guesswork.
2. **Machine-Verifiable Acceptance Criteria (BDD):** Every scenario must use Given/When/Then structure with concrete inputs, expected HTTP status codes, exact return shapes, or CLI outputs.
3. **Explicit Scope Fencing & Guardrails:** Specs must clearly outline **In-Scope** AND **Explicitly Out-of-Scope** items, as well as forbidden coding anti-patterns, to prevent scope creep and accidental edits to unrelated code.
4. **Deterministic Verification Protocol:** The spec must contain the exact, un-ambiguous commands required to run pre-flight checks, builds, linter checks, and unit/integration test suites (e.g., `uv run pytest tests/unit`).
5. **Schema & State Contracts:** Data mutations, API payloads, database migration schemas, and context state deltas (e.g., `ctx.state`) must be explicitly declared with expected data types.
6. **Granular Decomposability:** Scope must be constrained so that tasks can be executed autonomously within a single agent context window without hitting context saturation or iteration timeouts.

---

## 2. The Adapted INVEST Framework for AI Agents

All specifications generated or reviewed must satisfy the **INVEST** principles adapted for agent execution:

* **I - Independent:** The story must be executable in isolation without blocking on unfinished parallel agent tasks.
* **N - Negotiable:** Captures business intent and value while leaving implementation syntax to the code execution agent within defined boundaries.
* **V - Valuable:** Delivers clear, verifiable functional value or technical capability.
* **E - Estimable / Executable:** Technical context is clear enough for an execution agent to plan exact tool calls without clarifying questions.
* **S - Small:** Sized to fit comfortably within a single agent execution turn or context window (1-3 files modified max per task).
* **T - Testable:** Includes concrete, automated test verification commands.

---

## 3. Standard Specification Layout & Structure

Every technical specification must adhere strictly to the following structure:

# [FEATURE-ID]: [Short, Descriptive Summary]

**Issue Type:** User Story / Feature Spec
**Status:** Ready for Development
**Priority:** [High / Medium / Low]

## 1. Description & Context
**As a** [Persona / Role],
**I want to** [Action / Feature / Goal],
**So that** [Benefit / Value / Reason].

### Codebase Anchors & Target Files
* **Files to Create / Modify:**
  * `path/to/target_file.py`
* **Reference Files & Dependencies:**
  * `path/to/reference_file.py`
* **Target Tools & Runtimes:**
  * e.g., Python 3.11+, `uv run pytest`, `agents-cli lint`

## 2. Business Context & Technical Background
*Concise explanation of why this feature is needed, how it fits into the overall architecture, and relevant existing codebase patterns.*

## 3. Behavior-Driven Development (BDD) Acceptance Criteria
*Each scenario must be independently testable with explicit assertions.*

* **AC1: [Scenario Title - Happy Path]**
  * **Given** [explicit initial system state, database state, or context]
  * **When** [action, API request, function trigger, or CLI invocation]
  * **Then** [expected output, status code, payload schema, or state mutation]

* **AC2: [Scenario Title - Error / Edge Case]**
  * **Given** [precondition with invalid input, timeout, or missing permission]
  * **When** [invalid action / trigger event]
  * **Then** [expected error code, exception raised, or fallback state]

## 4. Technical Constraints, Boundaries & Out of Scope
* **Constraints & NFRs:** [Performance benchmarks (p95 latency), security/auth rules, rate limits]
* **In-Scope:** [Explicit list of components and behaviors to deliver]
* **Out of Scope:** [Explicit non-goals to prevent scope creep]
* **Forbidden Patterns:** [e.g., Do NOT add third-party dependencies, do NOT edit existing DB migrations]

## 5. Machine Verification Protocol & Definition of Done
The code execution agent must execute and pass the following commands before completing:
* [ ] **Build / Lint Check:** `agents-cli lint` (or `uv run ruff check .`)
* [ ] **Unit Tests:** `uv run pytest tests/unit`
* [ ] **Acceptance Criteria Verification:** All BDD Given/When/Then scenarios map 1-to-1 to passing test cases.
* [ ] **Documentation:** Inline docstrings and API specs updated.

---

## 4. Non-Functional Requirements (NFR) & Security Checklist

When refining technical constraints, verify and specify parameters for any that apply:

1. **Security & Authentication:** Auth headers (`Authorization: Bearer <token>`), scope verification, input sanitization, protection against OWASP Top 10.
2. **Performance Targets:** Latency thresholds (e.g., `p95 < 200ms`), memory footprints, query optimization.
3. **Rate Limiting & Resilience:** Throttling limits (e.g., 100 req/min), retry strategies, circuit breakers.
4. **Data Integrity & Schemas:** Strict type hints (Pydantic / dataclasses), database transaction boundaries.
5. **Observability:** Structured logging requirements, tracing markers, and metric emission.
