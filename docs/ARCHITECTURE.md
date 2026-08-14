# Agent Factory Architecture: Dual-Loop Multi-Agent System

This document outlines the architecture for **Agent Factory**, a multi-agent platform designed to transform high-level feature requests into production-grade software through two primary execution loops: **Spec-Driven Planning (Google ADK)** and **Code Execution (Antigravity SDK)**.

---

## 🏗️ Core Architecture Overview

The system consists of **2 Big Loops** containing **6 Sub-Loops** total, with clear human-in-the-loop approval gates between phases.

```mermaid
flowchart TD
    subgraph BIG_LOOP_1 ["Big Loop 1: Spec-Driven Planning (Google ADK on Agent Platform)"]
        style BIG_LOOP_1 fill:#e8f0fe,stroke:#1a73e8,stroke-width:2px

        subgraph STAGE_1 ["Stage 1: Council-Refined Design Loop (Fixed 2 Rounds)"]
            style STAGE_1 fill:#ffffff,stroke:#4285f4,stroke-width:1px
            A1["Directly Responsible Agent (DRA)"] -->|Draft Spec| P1["Product Reviewer"]
            A1 -->|Draft Spec| P2["Tech Architect Reviewer"]
            A1 -->|Draft Spec| P3["Security Reviewer"]

            subgraph C_PANEL ["Council Review Panel (Parallel)"]
                P1
                P2
                P3
            end

            P1 -->|Reviews| C_AGG["Council Chair Aggregator"]
            P2 -->|Reviews| C_AGG
            P3 -->|Reviews| C_AGG

            C_AGG -->|Consolidated Feedback| A1
            C_AGG -->|Certified Spec| G1["Human Gate 1: Spec Review & Approval"]
        end

        subgraph STAGE_2 ["Stage 2: Swarm Task Decomposition"]
            style STAGE_2 fill:#ffffff,stroke:#34a853,stroke-width:1px
            G1 -->|Approved Spec| ORCH["Swarm Orchestrator"]

            ORCH -->|Dynamic Agent Factory| W1["Frontend Task Worker"]
            ORCH -->|Dynamic Agent Factory| W2["Backend API Task Worker"]
            ORCH -->|Dynamic Agent Factory| W3["DB/Schema Task Worker"]

            subgraph SWARM ["Decomposition Swarm (Parallel)"]
                W1
                W2
                W3
            end

            W1 -->|Task Batches| B_CRITIC["Breakdown Critic"]
            W2 -->|Task Batches| B_CRITIC
            W3 -->|Task Batches| B_CRITIC

            B_CRITIC -->|Verified Task Manifest| G2["Human Gate 2: Task Manifest Approval"]
        end
    end

    G2 -->|GitHub Epic & Task Manifest| D1

    subgraph BIG_LOOP_2 ["Big Loop 2: Code Execution (Antigravity SDK Engine)"]
        style BIG_LOOP_2 fill:#fce8e6,stroke:#ea4335,stroke-width:2px

        subgraph L21 ["2.1 SWE Implementation Sub-Loop"]
            style L21 fill:#ffffff,stroke:#ea4335,stroke-width:1px
            D1["SWE Developer Agent"] -->|Generate Code & Unit Tests| D2["Code Static Analyzer"]
            D2 -->|Syntax or Lint Errors| D1
        end

        subgraph L22 ["2.2 QA/QC Review Sub-Loop"]
            style L22 fill:#ffffff,stroke:#ff6d01,stroke-width:1px
            D2 -->|Clean Syntax| E1["Automated Test Runner"]
            E1 -->|Test Tracebacks| D1
            E1 -->|All Tests Green| G3["Gate: Draft Pull Request"]
        end

        subgraph L23 ["2.3 Code Review Sub-Loop"]
            style L23 fill:#ffffff,stroke:#a142f4,stroke-width:1px
            G3 --> F1["PR Code Reviewer Agent"]
            F1 -->|Security or Refactoring Feedback| D1
            F1 -->|Approved PR| G4["Gate: Merge & Deploy"]
        end
    end
```

---

## 🏛️ Big Loop 1: Spec-Driven Planning (Google ADK)

Hosted on **Gemini Enterprise Agent Platform / Cloud Run**, Big Loop 1 uses the **Google Agent Development Kit (ADK 2.0)** to deliberate, refine, and decompose software specs.

### 1. Council Review Panel (Product + Tech + Security)
* **Directly Responsible Agent (DRA)**: Takes raw user prompts or issue descriptions and drafts a unified specification document (User Story + BDD scenarios + Technical Architecture + API Contracts + Security NFRs).
* **Council Review Panel**: Concurrently evaluates the draft across three distinct personas:
  1. **Product Reviewer**: Evaluates INVEST criteria, business goals, and user value.
  2. **Tech Architect Reviewer**: Evaluates API completeness, data model integrity, and system complexity.
  3. **Security Reviewer**: Evaluates testability, OWASP vulnerability risks, and error resilience.
* **Council Chair Aggregator**: Merges all three review streams into a single, actionable list of revision instructions for the DRA.
* **Fixed Round Limit**: Enforces a strict 2-round cap to guarantee convergence and fast response times.

### 2. Swarm Task Decomposition
* **Swarm Orchestrator**: Inspects the Council-certified specification and identifies independent subsystems (e.g. Frontend UI, Backend API, Database Migrations).
* **Dynamic Agent Factory**: Instantiates specialized `LlmAgent` instances on the fly using ADK 2.0.
* **Parallel Task Workers**: The swarm workers break down each subsystem into atomic tasks with independent acceptance criteria concurrently.
* **Breakdown Critic**: Validates that all tasks form a valid Directed Acyclic Graph (DAG) without circular dependencies or missing requirements.

---

## 💻 Big Loop 2: Code Execution (Antigravity SDK Engine)

Big Loop 2 runs in local workspace / execution environments using the **Antigravity SDK**, taking the atomic tasks produced in Big Loop 1 and implementing them through three sub-loops:

1. **2.1 SWE Implementation Loop**: Developer agent writes functional code and unit tests.
2. **2.2 QA/QC Review Loop**: Automated test runner executes pytest/jest/build commands. Any tracebacks or failures are fed directly back into the developer agent until all tests pass cleanly.
3. **2.3 Code Review Loop**: PR Critic performs automated code review, security scanning, and architectural sanity checks before approving the Pull Request.

---

## 📚 Related Documentation
* [Human-in-the-Loop (HITL) Multi-Surface Guide](HUMAN_IN_THE_LOOP.md)
* [ADK Planning Engine Implementation Guide](PLANNING_ENGINE_GUIDE.md)
