# Coding Agent Guide

## Prerequisites

Install the CLI (one-time):
```bash
uv tool install google-agents-cli
```

---

## Development Phases

### Phase 1: Understand Requirements
Before writing any code, understand the project's requirements, constraints, and success criteria.

### Phase 2: Build and Implement
Implement agent logic in `app/`. Use `agents-cli playground` for interactive testing. Iterate based on user feedback.

### Phase 3: The Evaluation Loop (Main Iteration Phase)
Start with 1-2 eval cases, run `agents-cli eval generate`, then `agents-cli eval grade`, iterate by making changes and rerunning both commands until satisfied. Expect 5-10+ iterations. Once you have a baseline, reach for `agents-cli eval compare` (regression diffs), `agents-cli eval analyze` (cluster failure modes), and `agents-cli eval optimize` (auto-tune prompts). See the **Evaluation Guide** for metrics, dataset schema, LLM-as-judge config, and common gotchas.

### Phase 4: Pre-Deployment Tests
Run `uv run pytest tests/unit tests/integration`. Fix issues until all tests pass.

### Phase 5: Deploy to Dev
**Requires explicit human approval.** Run `agents-cli deploy` only after user confirms. See the **Deployment Guide** for details.

### Phase 6: Production Deployment
Ask the user: Option A (simple single-project) or Option B (full CI/CD pipeline with `agents-cli infra cicd`).

## Development Commands

| Command | Purpose |
|---------|---------|
| `agents-cli playground` | Interactive local testing |
| `uv run pytest tests/unit tests/integration` | Run unit and integration tests |
| `agents-cli eval dataset synthesize` | Synthesize multi-turn eval scenarios for your agent |
| `agents-cli eval generate` | Run agent on eval dataset, produce traces |
| `agents-cli eval grade` | Run agent evaluations on the traces |
| `agents-cli eval compare` | Compare two grade-results files (regression check) |
| `agents-cli eval analyze` | Cluster failure modes from grade results |
| `agents-cli eval metric list` | List built-in metrics available in the SDK |
| `agents-cli eval optimize` | Auto-tune agent prompts using eval data |
| `agents-cli lint` | Check code quality |
| `agents-cli infra single-project` | Set up project infrastructure (Terraform) |
| `agents-cli deploy` | Deploy to dev |
| `agents-cli scaffold enhance` | Add deployment target or CI/CD to project |
| `agents-cli scaffold upgrade` | Upgrade project to latest version |

---

## Operational Guidelines for Coding Agents

- **Code preservation**: Only modify code directly targeted by the user's request. Preserve all surrounding code, config values (e.g., `model`), comments, and formatting.
- **NEVER change the model** unless explicitly asked.
- **Model 404 errors**: Fix `DEFAULT_LLM_LOCATION` / `LLM_LOCATION` (e.g., `global` instead of `us-east1`), NOT the model name or `GOOGLE_CLOUD_LOCATION`.
- **Model Inference vs Infrastructure Locations**:
  - **`LLM_LOCATION` / `DEFAULT_LLM_LOCATION`**: **MUST** be used for all Vertex AI Gemini model inference calls and `VertexAiSessionService` sessions (defaults to `global`). Never pass `GOOGLE_CLOUD_LOCATION` to Vertex AI model inference calls.
  - **`GOOGLE_CLOUD_LOCATION`**: **MUST** be used for GCP infrastructure resources (Cloud Run services, Cloud Tasks queues, Artifact Registry, and Reasoning Engine resource paths like `us-east1`).
- **ADK tool imports**: Import the tool instance, not the module: `from google.adk.tools.load_web_page import load_web_page`
- **Run Python with `uv`**: `uv run python script.py`. Run `agents-cli install` first.
- **Stop on repeated errors**: If the same error appears 3+ times, fix the root cause instead of retrying.
- **Terraform conflicts** (Error 409): Use `terraform import` instead of retrying creation.

---

## Environment Variable Guidelines

| Variable Name | Scope / Surface | Purpose & Usage Guidelines | Example Value |
|---------------|-----------------|----------------------------|---------------|
| `GOOGLE_CLOUD_LOCATION` | Infra / Deployment | GCP region for Cloud Infrastructure (Cloud Run, Cloud Tasks queues, Reasoning Engine resource paths). MUST specify a regional location (e.g. `us-east1`, `us-central1`). | `us-east1` |
| `DEFAULT_LLM_LOCATION` | Model Inference | Region for Gemini LLM publisher model inference endpoints. MUST use `global` or `us-central1` for Gemini model calls. | `global` |
| `LLM_LOCATION` | Model Inference | Primary environment variable for Vertex AI Gemini LLM inference and session endpoints. ALWAYS set to `global` for model inference. | `global` |
| `GOOGLE_CLOUD_PROJECT` | All | Target Google Cloud Project ID. | `your-gcp-project-id` |
| `REASONING_ENGINE_ID` | Gateway | Full resource path to the Vertex AI Reasoning Engine instance. | `projects/123456789012/locations/us-central1/reasoningEngines/1234567890123456789` |
| `CLOUD_RUN_GATEWAY_URL` | Gateway / Worker | Public HTTPS endpoint URL of the Cloud Run Gateway service. | `https://gateway-service-xyz-uc.a.run.app` |
| `ENABLE_CLOUD_TASKS` | Gateway | Flag (`true`/`false`) to route webhook events through Cloud Tasks. | `true` |
| `CLOUD_TASKS_QUEUE_ID` | Gateway | Name of the Cloud Tasks execution queue. | `my-agent-queue` |
| `CLOUD_TASKS_LOCATION` | Gateway | GCP region where the Cloud Tasks queue is hosted. | `us-central1` |
| `GITHUB_WEBHOOK_SECRET` | Gateway | Secret used for verifying GitHub Webhook HMAC `X-Hub-Signature-256`. | `your_webhook_secret` |
| `GITHUB_APP_ID` | Gateway / Agent | App ID for GitHub App authentication. | `123456` |
| `GITHUB_APP_INSTALLATION_ID` | Gateway / Agent | Installation ID for target GitHub repository. | `12345678` |
| `GITHUB_REPO` | Gateway / Agent | Target GitHub repository (`owner/repo`). | `owner/repo` |
| `GITHUB_APP_PRIVATE_KEY` | Gateway / Agent | PEM RSA Private Key string for generating GitHub App installation tokens. | `-----BEGIN RSA PRIVATE KEY-----...` |

