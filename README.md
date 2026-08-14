# Spec Deliberator Multi-Agent System (with Google ADK)

An enterprise-grade, spec-driven multi-agent system built on top of the **Google Agent Development Kit (ADK 2.0)** and managed under the **`uv`** package manager.

This system operates as a **Multi-Tenant GitHub App** that transforms raw ideas or incomplete draft requirements into complete, production-ready development specifications across **any installed GitHub repository** through **cross-role agent peer review** and automated GitHub issue synchronization.

---

## 🏗️ Multi-Tenant GitHub App Vision & Architecture

The Spec Deliberator Agent is built to run as a multi-tenant GitHub App service deployed on Google Cloud Agent Runtime / Cloud Run:

```
  ┌──────────────────────┐  1. GitHub Webhook (Issue #42)   ┌─────────────────────────────┐
  │ Any Target GitHub    ├─────────────────────────────────►│ Surface Gateway Proxy       │
  │ Repository (`owner/repo`)│                              │ (`/webhooks/github`)        │
  └──────────────────────┘                                  └──────────────┬──────────────┘
                                                                           │
                                                                           │ 2. Pre-populates Structured
                                                                           │    Session State
                                                                           ▼
                                                            ┌─────────────────────────────┐
                                                            │ ADK Session Service         │
                                                            │ (`ctx.state`)               │
                                                            └──────────────┬──────────────┘
                                                                           │
                                                                           │ 3. Executes Multi-Agent
                                                                           │    Workflow
                                                                           ▼
                                                            ┌─────────────────────────────┐
                                                            │ ADK Workflow Runner         │
                                                            │ - `directly_responsible_agent`
                                                            │ - `council_reviewers`       │
                                                            └─────────────────────────────┘
```

### Key Architectural Design Principles

1. **Multi-Tenant Repository Agnostic (`search_target_repository`):**
   * The agent does not rely on local container disk code. When processing a webhook from `acme/web-app`, the agent uses the GitHub Code Search API with a scoped Installation Access Token to search the target repository dynamically over HTTPS.
2. **Structured Domain State Model (`ctx.state`):**
   * **`issue`**: Stores target repository metadata (`id`, `title`, `author`, `url`, `repo`).
   * **`specifications`**: Stores current story drafts (`user_story_markdown`), peer review approval status, and audit history (`critique_history`).
   * **`comments`**: Captures delta comments across surfaces (GitHub, Slack, Discord).
3. **Native Google ADK Skills Framework (`SkillToolset`):**
   * Uses ADK's native `load_skill_from_dir` and `SkillToolset` ([`user-story-best-practices/SKILL.md`](spec_engine/skills/user-story-best-practices/SKILL.md)).
   * Instructions are loaded on demand via tool calls (`load_skill`), keeping system prompt context overhead extremely low.

---

## 🔄 Multi-Agent Deliberation Workflow

```mermaid
sequenceDiagram
    autonumber
    actor Human as Human / Stakeholder
    participant GW as GitHub App & Gateway Proxy
    participant REF as User Story Refiner (Product Owner)
    participant SC as Story Critic (Software Architect)

    rect rgb(240, 245, 255)
        note over Human,SC: Automated User Story Refinement & Peer Review
        Human->>GW: Create or Update Issue in Target Repo
        GW->>REF: Pre-load Session State & Trigger Entry Gate
        loop Technical Peer Review Loop (Up to 2 Rounds)
            REF->>SC: Submit Drafted User Story
            SC-->>REF: Request Revisions (if INVEST or BDD Gaps)
        end
        SC->>GW: Story Peer-Reviewed & Certified
        GW->>Human: Update Target Issue Description & Label `agent:completed`
    end
```

---

## 🤖 Specialized Agents & Skills

The system coordinates specialized ADK agents inside `spec_engine/agents`:

1. **Directly Responsible Agent (DRA)** ([`directly_responsible_agent`](spec_engine/agents/directly_responsible_agent/agent.py)):
   Lead Spec Author operating in automated single-pass mode. Refines raw inputs into a Jira/GitLab standardized user story with BDD (Given/When/Then) acceptance criteria and technical specifications.
2. **Council Review Panel** ([`council/`](spec_engine/agents/council/)):
   Panel of reviewers including Product Reviewer (`product_reviewer`), Tech Architect Reviewer (`tech_reviewer`), Security Reviewer (`security_reviewer`), and Council Chair (`council_chair`) that evaluate and refine specification drafts.
3. **Native ADK SkillToolset** ([`user-story-best-practices`](spec_engine/skills/user-story-best-practices/SKILL.md)):
   Enterprise quality standard skill defining INVEST criteria, BDD Given/When/Then scenario structures, Non-Functional Requirements (NFR) checklists, and Definition of Done.

---

## 📁 Repository Directory Layout

```
agent-factory/
├── spec_engine/                    # Service 1: Core ADK Multi-Agent System
│   ├── agents/                     #   - Specialized ADK agents & prompts
│   │   ├── directly_responsible_agent/ #  • Lead Spec Author (DRA)
│   │   ├── council/                #     • Council panel (Product, Tech, Security, Chair)
│   │   │   ├── product_reviewer/   #     • Product Manager reviewer
│   │   │   ├── tech_reviewer/      #     • Technical Architect reviewer
│   │   │   ├── security_reviewer/  #     • Security Lead reviewer
│   │   │   └── council_chair/      #     • Council Chair aggregator
│   │   └── tools.py                #     • Multi-tenant GitHub API & search tools
│   ├── skills/                     #   - Native ADK Skills
│   │   ├── skills.py               #     • Native SkillToolset loader
│   │   └── user-story-best-practices/ #  • SKILL.md with YAML frontmatter
│   ├── app/                        #   - ADK FastAPI app & A2A endpoints
│   ├── run.py                      #   - Engine runner CLI
│   ├── Dockerfile                  #   - Agent Runtime container build
│   ├── agents-cli-manifest.yaml    #   - ADK deployment manifest (target: agent_runtime)
│   └── deployment_metadata.json    #   - Agent Runtime deployment output metadata
├── gateway/                        # Service 2: Transient Webhook Proxy
│   ├── app/                        #   - Routes, adapters, services, and schemas
│   │   ├── adapters/               #   - Surface adapters (GitHub HMAC, etc.)
│   │   ├── routes/                 #   - POST /webhooks/github & /tasks/execute-agent-turn
│   │   ├── services/               #   - Event publisher (Pub/Sub & direct HTTP)
│   │   └── utils/                  #   - Security & bot self-loop filtering
│   ├── Dockerfile                  #   - Dedicated Cloud Run Gateway container build
│   └── main.py                     #   - Gateway FastAPI entrypoint
├── tests/                          # Test suites (unit & integration)
│   ├── unit/                       #   - Fast unit tests for agents & gateway
│   └── integration/                #   - Integration tests for ADK & A2A
```

---

## 🛠️ Installation & Testing

Ensure you have `uv` installed. If not, follow instructions at [astral.sh/uv](https://astral.sh/uv).

### 1. Monorepo Workspace Installation (Recommended)
`uv` automatically manages the root workspace defined in [`pyproject.toml`](pyproject.toml) and synchronizes all dependencies across workspace members ([`agent_engine/`](agent_engine) and [`gateway/`](gateway)):

```bash
# Initialize venv & sync dependencies across all workspace sub-services
uv venv
uv sync

# Run unit tests across all agents & gateway proxy
uv run pytest tests/unit
```

### 2. Standalone / Per-Directory Installation
If working directly within a specific service directory, you can also install and test within that directory:

```bash
# Agent Engine Service
(
  cd agent_engine
  set -a && source .env && set +a
  uv sync
)

# Gateway Proxy Service
(
  cd gateway
  set -a && source .env && set +a
  uv sync
)
```

---

## 🚀 Running the Workflow (Local CLI Mode)

Run the graph workflow system using `uv run python run.py` and supply a raw requirements draft as the input:

```bash
uv run python agent_engine/run.py drafts/raw_spec.md --output specs/refined_spec.md
```

### CLI Arguments:
* `input`: Path to raw spec draft or user prompt file (Required).
* `-o`, `--output`: Path to write the finalized spec (Default: `specs/refined_spec.md`).

---

## 🤖 Creating & Configuring Your GitHub App

To integrate your multi-agent system with GitHub under a dedicated bot identity (e.g., `@spec-deliberator[bot]`), follow these steps:

### 1. Register the GitHub App on GitHub
1. Go to github.com ➔ Click your profile icon ➔ **Settings** (or Organization Settings) ➔ **Developer Settings** ➔ **GitHub Apps** ➔ Click **New GitHub App**.
2. **Basic Information:**
   * **GitHub App Name:** `Spec Deliberator` (or your preferred bot name)
   * **Homepage URL:** `https://your-domain.com` (or temporary placeholder URL)
   * **Webhook URL:** `https://spec-deliberator-gateway-xxx.a.run.app/webhooks/github` *(Updated after Cloud Run deploy)*
   * **Webhook Secret:** Enter a strong secret string (e.g., `my_app_webhook_secret_123`).

### 2. Set Permissions
Under **Repository Permissions**:
* **Issues:** Select **Read & Write**
* **Metadata:** **Read-only** *(automatically selected)*

### 3. Subscribe to Webhook Events
Under **Subscribe to events**, check:
* ✅ **Issues**
* ✅ **Issue comment**
* ✅ **Discussion**
* ✅ **Discussion comment**

### 4. Generate Private Key & Install
1. Click **Create GitHub App**.
2. Scroll to the bottom of the App settings page and click **Generate a private key**.
3. Save the downloaded `.pem` file as `github_app_private_key.pem` in your project root.
4. Click **Install App** in the left sidebar ➔ Select your target repository ➔ Click **Install**.

### 5. Extract Credentials for `.env`
Note down the following parameters for your `.env` configuration:
```bash
GITHUB_APP_ID=123456                        # Found on App Settings General page (App ID)
GITHUB_APP_INSTALLATION_ID=98765432         # Found in URL: github.com/settings/installations/{ID}
GITHUB_APP_PRIVATE_KEY_PATH=./github_app_private_key.pem
GITHUB_WEBHOOK_SECRET=my_app_webhook_secret_123
```

> **📌 Note on Private Key Options:**
> * **Option A (File Path)**: `GITHUB_APP_PRIVATE_KEY_PATH=./github_app_private_key.pem` *(Convenient for local development)*.
> * **Option B (Raw String Variable)**: `GITHUB_APP_PRIVATE_KEY="-----BEGIN RSA PRIVATE KEY-----\n..."` *(Recommended for GCP Secret Manager / Cloud Run deployment so no `.pem` file needs to be committed or mounted inside the container)*.

---

## ☁️ End-to-End Deployment Guide (Gemini Enterprise Agent Runtime & Cloud Run)

This guide provides a step-by-step walkthrough for deploying the core Spec Deliberator Multi-Agent Engine to **Gemini Enterprise Agent Runtime** and the transient Webhook Proxy (`gateway/`) to **GCP Cloud Run**.

### Prerequisites & Assumptions
* **GCP Project:** `your-gcp-project-id`
* **Region:** `us-east1`
* **Deployment Target:** Agent Runtime (Vertex AI) + Cloud Run (Gateway Proxy)

---

### Step 1: Enable Google Cloud APIs

Source environment variables from [`agent_engine/.env`](agent_engine/.env) and run this command in your terminal to enable all required GCP APIs:

```bash
(
  cd agent_engine
  set -a && source .env && set +a
  gcloud services enable \
    aiplatform.googleapis.com \
    cloudbuild.googleapis.com \
    cloudtasks.googleapis.com \
    secretmanager.googleapis.com \
    run.googleapis.com \
    artifactregistry.googleapis.com \
    --project="${GOOGLE_CLOUD_PROJECT}"
)
```

---

### Step 2: Deploy Core Spec Engine to Agent Runtime

Deploy the multi-agent system directly onto **Gemini Enterprise Agent Runtime** from [`agent_engine/`](agent_engine):

```bash
(
  cd agent_engine
  set -a && source .env && set +a
  agents-cli deploy \
    --project "${GOOGLE_CLOUD_PROJECT}" \
    --region "${GOOGLE_CLOUD_LOCATION:-us-east1}" \
    --no-confirm-project
)
```

> ⏱️ **Note:** Agent Runtime container builds from [`agent_engine/Dockerfile`](agent_engine/Dockerfile) and provisions the engine server-side. This takes **5–8 minutes**. When finished, `agents-cli` writes [`agent_engine/deployment_metadata.json`](agent_engine/deployment_metadata.json) containing your deployed `remote_agent_runtime_id`.

---

### Step 3: Create Cloud Tasks Queue & IAM Permissions

1. **Extract the deployed Reasoning Engine resource ID from deployment metadata:**
   ```bash
   export REASONING_ENGINE_ID=$(jq -r '.remote_agent_runtime_id' agent_engine/deployment_metadata.json)
   echo "Deployed Reasoning Engine ID: ${REASONING_ENGINE_ID}"
   ```

2. **Create the Cloud Tasks queue used by the Gateway with rate limiting:**
   ```bash
   (
     cd gateway
     set -a && source .env && set +a
     gcloud tasks queues create github-agent-queue \
       --location="${GOOGLE_CLOUD_LOCATION:-us-east1}" \
       --max-concurrent-dispatches=5 \
       --max-dispatches-per-second=2 \
       --max-attempts=3 \
       --project="${GOOGLE_CLOUD_PROJECT}"
   )
   ```

3. **Grant Cloud Tasks Enqueuer role to the Compute default service account:**
   ```bash
   (
     cd gateway
     set -a && source .env && set +a
     PROJECT_NUMBER=$(gcloud projects describe "${GOOGLE_CLOUD_PROJECT}" --format="value(projectNumber)")
     gcloud projects add-iam-policy-binding "${GOOGLE_CLOUD_PROJECT}" \
       --member="serviceAccount:${PROJECT_NUMBER}-compute@developer.gserviceaccount.com" \
       --role="roles/cloudtasks.enqueuer"
   )
   ```

---

### Step 4: Deploy Gateway Proxy to Cloud Run

Deploy the transient proxy to Cloud Run from [`gateway/`](gateway) with an extended **15-minute timeout** and configured Cloud Tasks service account:

```bash
(
  cd gateway
  set -a && source .env && set +a
  PROJECT_NUMBER=$(gcloud projects describe "${GOOGLE_CLOUD_PROJECT}" --format="value(projectNumber)")
  gcloud run deploy spec-deliberator-gateway \
    --source . \
    --timeout=15m \
    --concurrency=80 \
    --set-env-vars GOOGLE_CLOUD_PROJECT="${GOOGLE_CLOUD_PROJECT}",ENABLE_CLOUD_TASKS=true,CLOUD_TASKS_QUEUE_ID=github-agent-queue,CLOUD_TASKS_LOCATION="${GOOGLE_CLOUD_LOCATION:-us-east1}",CLOUD_TASKS_SERVICE_ACCOUNT="${PROJECT_NUMBER}-compute@developer.gserviceaccount.com",GITHUB_WEBHOOK_SECRET="${GITHUB_WEBHOOK_SECRET}",GITHUB_APP_ID="${GITHUB_APP_ID}",GITHUB_APP_INSTALLATION_ID="${GITHUB_APP_INSTALLATION_ID}",GITHUB_REPO="${GITHUB_REPO}",REASONING_ENGINE_ID="${REASONING_ENGINE_ID}" \
    --allow-unauthenticated \
    --region "${GOOGLE_CLOUD_LOCATION:-us-east1}" \
    --project "${GOOGLE_CLOUD_PROJECT}"
)
```


---

### Step 5: Get Live Webhook URL & Wire to GitHub App

1. **Retrieve your live Cloud Run Gateway URL:**
   ```bash
   (
     cd gateway
     set -a && source .env && set +a
     gcloud run services describe spec-deliberator-gateway \
       --region "${GOOGLE_CLOUD_LOCATION:-us-east1}" \
       --project "${GOOGLE_CLOUD_PROJECT}" \
       --format 'value(status.url)'
   )
   ```

2. **Verify Gateway Health:**
   ```bash
   (
     cd gateway
     set -a && source .env && set +a
     curl $(gcloud run services describe spec-deliberator-gateway --region "${GOOGLE_CLOUD_LOCATION:-us-east1}" --project "${GOOGLE_CLOUD_PROJECT}" --format 'value(status.url)')/health
   )
   ```
   *Expected response:* `{"status":"healthy","service":"spec-deliberator-gateway"}`

3. **Paste Webhook URL in GitHub App Settings:**
   Copy the URL above and append `/webhooks/github`:
   `https://spec-deliberator-gateway-xxx.a.run.app/webhooks/github`

---

### Step 6: Test & Observe Deployed Agents

1. **Trigger an initial spec generation:**
   ```bash
   uv run python agent_engine/run.py drafts/raw_spec.md
   ```
2. **Observe Logs on Google Cloud Console:**
   ```bash
   # View Gateway Logs
   gcloud logging read "resource.type=cloud_run_revision AND resource.labels.service_name=spec-deliberator-gateway" \
     --project="${GOOGLE_CLOUD_PROJECT}" --limit=20 --format="table(timestamp,severity,textPayload)"

   # View Agent Runtime Logs
   gcloud logging read "resource.type=aiplatform.googleapis.com/ReasoningEngine" \
     --project="${GOOGLE_CLOUD_PROJECT}" --limit=20
   ```
3. **Comment on the GitHub Issue** created by the bot to verify the human gate approval!
