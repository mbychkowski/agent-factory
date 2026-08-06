---
name: user-story-best-practices
description: Enterprise quality standards, INVEST criteria, BDD templates, and NFR checklists for User Story creation and peer review.
---

# Enterprise User Story Best Practices & Quality Standard

This document defines the official quality standards, BDD formatting guidelines, and evaluation criteria for User Story creation and peer review across the engineering team.

---

## 1. The INVEST Framework
All User Stories must satisfy the **INVEST** quality principles:

* **I - Independent:** The story should be self-contained so that it can be developed and delivered without hard dependencies on incomplete parallel work items.
* **N - Negotiable:** The story captures intent and value rather than rigid implementation details, leaving room for technical design choices.
* **V - Valuable:** Delivers clear, measurable value to a specific user persona or system stakeholder.
* **E - Estimable:** Scope and technical requirements must be clear enough for engineers to estimate effort accurately.
* **S - Small:** Sized to fit comfortably within a single sprint iteration (1-2 weeks). Large features must be broken down.
* **T - Testable:** Accompanied by concrete, verifiable Acceptance Criteria.

---

## 2. Standard Structure & Formatting

Every User Story must adhere strictly to the following Markdown layout:

# [Short, descriptive summary of the feature]

**Issue Type:** User Story
**Status:** Ready for Development
**Priority:** [High / Medium / Low]

## 1. Description
**As a** [Persona / Role],
**I want to** [Action / Feature / Goal],
**So that** [Benefit / Value / Reason].

## 2. Business Context & Background
*Concise summary of why this feature is needed and its strategic alignment.*

## 3. Acceptance Criteria
*Use Behavior-Driven Development (BDD) format (Given / When / Then).*

* **AC1: [Title of Scenario 1]**
  * **Given** [precondition / initial state]
  * **When** [action / trigger event]
  * **Then** [expected outcome / system state]

* **AC2: [Title of Scenario 2 (Error Handling or Edge Case)]**
  * **Given** [precondition]
  * **When** [invalid action / trigger event]
  * **Then** [expected error response / fallback state]

## 4. Technical Constraints & Out of Scope
* **Constraints:** [NFRs, performance targets, rate limits, security requirements]
* **Out of Scope:** [Explicitly state non-goals to prevent scope creep]

## 5. Definition of Done (DoD)
* [ ] Code is peer-reviewed and approved.
* [ ] Unit and integration tests are written and passing.
* [ ] Acceptance Criteria are verified against test cases.
* [ ] Relevant documentation (API docs, user guides) is updated.
* [ ] Feature is deployable without breaking existing functionality.

---

## 3. Behavior-Driven Development (BDD) Guidelines

1. **Concrete Scenarios:** Avoid generic statements like "Then it works correctly". State explicit HTTP status codes, UI state changes, or database mutations.
2. **Cover Edge Cases:** Always include at least one negative / edge case scenario (e.g., rate limit exceeded, invalid input payload, network timeout).
3. **Unambiguous Language:** Use clear, declarative terms (`shall`, `must`, `return`) rather than passive phrases.

---

## 4. Non-Functional Requirements (NFR) Checklist

When refining technical constraints, verify if any of the following apply:

* **Security & Auth:** Authentication requirements, permission scopes, data encryption in transit and at rest.
* **Rate Limiting & Throttling:** Maximum request thresholds per minute/hour to prevent API abuse.
* **Performance Benchmarks:** Target response times (e.g. `p95 latency < 200ms`).
* **Error Handling:** Graceful degradation and standard error payloads.
* **Observability:** Structured log metrics and tracing requirements.
