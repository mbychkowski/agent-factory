# Spec Deliberator Multi-Agent System (with Google ADK)

An enterprise-grade, spec-driven multi-agent system built on top of the **Google Agent Development Kit (ADK 2.0)** and managed under the **`uv`** package manager.

This system automates the process of transforming raw ideas or incomplete draft requirements into complete, production-ready development specifications through **cross-role agent peer review** and **milestone human approval gates** on GitHub.

---

## 🔄 Multi-Agent Deliberation Architecture

```mermaid
sequenceDiagram
    autonumber
    actor Human as Human / Stakeholder
    participant GW as GitHub & Gateway Proxy
    participant FAC as Deliberation Facilitator
    participant REF as User Story Refiner (PM)
    participant SC as Story Critic (Architect)
    participant DES as Technical Designer (Architect)
    participant DC as Design Critic (Lead)
    participant PLN as Task Planner (Lead)

    rect rgb(240, 245, 255)
        note over Human,SC: Phase 1: User Story Refinement & Gate 1
        Human->>GW: Raw Requirements / Input
        GW->>FAC: Trigger Facilitator Gate
        alt Fresh Spec Creation
            FAC->>REF: Pass Raw Spec Requirements
        else Multi-Human Collaboration Turn
            FAC->>FAC: Triage & Synthesize Delta
            FAC-->>Human: Direct Response (if Noise / Meta-Q&A)
            FAC->>REF: Pass Synthesized Delta
        end
        loop Peer Review Loop
            REF->>SC: Submit Draft User Story
            SC-->>REF: Request Revisions (if Gaps/NFRs Missing)
        end
        SC->>GW: Story Approved -> Publish Parent Issue (Milestone 1)
        GW-->>Human: Prompt for Human Gate 1 Approval
    end

    rect rgb(245, 250, 240)
        note over Human,DC: Phase 2: Technical Design RFC & Gate 2
        Human->>GW: Approve Milestone 1 Issue
        GW->>DES: Trigger Technical Design Phase
        loop Peer Review Loop
            DES->>DC: Submit Draft RFC Technical Design
            DC-->>DES: Request Revisions (if Unclear Contracts/Gaps)
        end
        DC->>GW: RFC Approved -> Publish RFC Comment (Milestone 2)
        GW-->>Human: Prompt for Human Gate 2 Approval
    end

    rect rgb(255, 245, 240)
        note over Human,PLN: Phase 3: Task Breakdown
        Human->>GW: Approve Milestone 2 RFC
        GW->>PLN: Trigger Task Planning
        PLN->>GW: Create Developer Sub-Issues on GitHub
        GW-->>Human: Final Developer Sub-Tasks Ready
    end
```

---

## 🤖 Specialized Agents

The system coordinates 6 specialized ADK agents inside `agent_engine/agents`:

1. **Deliberation Facilitator Agent** ([`deliberation_facilitator`](file:///home/mbychkowski/Code/agent-factory/agent_engine/agents/deliberation_facilitator/agent.py)):
   Acts as a shock absorber between human channels (GitHub/Slack) and core spec agents. Triages messages, drops off-topic noise, answers meta-questions, and synthesizes clean spec deltas.
2. **User Story Refiner Agent** ([`user_story_refiner`](file:///home/mbychkowski/Code/agent-factory/agent_engine/agents/story_refiner/agent.py)):
   Product Owner persona that refines draft requirements into a Jira/GitLab standardized user story with BDD (Given/When/Then) acceptance criteria.
3. **Story Critic Agent** ([`story_critic`](file:///home/mbychkowski/Code/agent-factory/agent_engine/agents/critique/story_critic.py)):
   Software Architect persona that peer-reviews User Story drafts for technical feasibility, NFR completeness, security, and testability before GitHub publishing.
4. **Technical Designer Agent** ([`technical_designer`](file:///home/mbychkowski/Code/agent-factory/agent_engine/agents/technical_designer/agent.py)):
   Software Architect persona that drafts the system architecture, database schemas, API contracts, and Mermaid diagrams into an RFC document.
5. **Design Critic Agent** ([`design_critic`](file:///home/mbychkowski/Code/agent-factory/agent_engine/agents/critique/design_critic.py)):
   Engineering Lead persona that peer-reviews RFC Technical Designs for actionability, API clarity, and task breakdown readiness before GitHub comment publishing.
6. **Task Planner Agent** ([`task_planner`](file:///home/mbychkowski/Code/agent-factory/agent_engine/agents/task_planner/agent.py)):
   Engineering Lead persona that analyzes the approved RFC design and breaks it down into discrete developer sub-issues on GitHub.

---

## 📁 Repository Directory Layout

```
agent-factory/
├── agent_engine/                   # Service 1: Core ADK Multi-Agent System
│   ├── agents/                     #   - All 6 specialized ADK agents & prompts
│   │   ├── deliberation_facilitator/
│   │   ├── story_refiner/
│   │   ├── technical_designer/
│   │   ├── task_planner/
│   │   └── critique/
│   ├── app/                        #   - ADK FastAPI app & A2A endpoints
│   ├── run.py                      #   - Engine runner CLI
│   ├── Dockerfile                  #   - Agent Runtime container build
│   ├── agents-cli-manifest.yaml    #   - ADK deployment manifest (target: agent_runtime)
│   └── deployment_metadata.json    #   - Agent Runtime deployment output metadata
├── gateway/                        # Service 2: Transient Webhook Proxy
│   ├── app/                        #   - Routes, adapters, services, and schemas
│   │   ├── adapters/               #   - Surface adapters (GitHub HMAC, etc.)
│   │   ├── routes/                 #   - POST /webhooks/github & /health
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

```bash
# 1. Initialize venv & sync dependencies
uv venv
uv sync

# 2. Run unit tests
uv run python -m unittest discover -s tests/unit
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
* **GCP Project:** `prj-goron-village-dev`
* **Region:** `us-east1`
* **Deployment Target:** Agent Runtime (Vertex AI) + Cloud Run (Gateway Proxy)

---

### Step 1: Enable Google Cloud APIs

Source your `.env` file first, then run this command in your terminal to enable all required GCP APIs:

```bash
# Source environment variables from .env
set -a && source .env && set +a

gcloud services enable \
  aiplatform.googleapis.com \
  cloudbuild.googleapis.com \
  secretmanager.googleapis.com \
  run.googleapis.com \
  pubsub.googleapis.com \
  artifactregistry.googleapis.com \
  --project="${GOOGLE_CLOUD_PROJECT}"
```

---

### Step 2: Deploy Core Spec Engine to Agent Runtime

Navigate to `agent_engine/` (where `agents-cli-manifest.yaml` and `Dockerfile` are located) and deploy the multi-agent system directly onto **Gemini Enterprise Agent Runtime**:

```bash
cd agent_engine

agents-cli deploy \
  --project "${GOOGLE_CLOUD_PROJECT}" \
  --region "${DEFAULT_GOOGLE_CLOUD_LOCATION:-us-east1}" \
  --no-confirm-project

cd ..
```

> ⏱️ **Note:** Agent Runtime container builds from `agent_engine/Dockerfile` and provisions the engine server-side. This takes **5–8 minutes**. When finished, `agents-cli` writes `agent_engine/deployment_metadata.json` and prints your deployed Agent Runtime resource ID.

---

### Step 3: Create Cloud Pub/Sub Topic, IAM Permissions & Push Subscription

1. **Create the messaging topic used by the Gateway to queue human interaction events:**
   ```bash
   gcloud pubsub topics create github-human-events \
     --project="${GOOGLE_CLOUD_PROJECT}"
   ```

2. **Grant Pub/Sub Publisher permission to the Gateway Cloud Run service account:**
   ```bash
   PROJECT_NUMBER=$(gcloud projects describe "${GOOGLE_CLOUD_PROJECT}" --format="value(projectNumber)")

   gcloud projects add-iam-policy-binding "${GOOGLE_CLOUD_PROJECT}" \
     --member="serviceAccount:${PROJECT_NUMBER}-compute@developer.gserviceaccount.com" \
     --role="roles/pubsub.publisher"
   ```

3. **Create a Pub/Sub Push Subscription to forward authenticated events to the Agent Engine:**
   ```bash
   # Retrieve your Agent Engine API base URL and create push subscription targeting /pubsub/push with OIDC auth
   AGENT_ENDPOINT="https://${DEFAULT_GOOGLE_CLOUD_LOCATION:-us-east1}-aiplatform.googleapis.com/v1/${AGENT_RUNTIME_ID}/api/pubsub/push"

   gcloud pubsub subscriptions create github-human-events-sub \
     --topic=github-human-events \
     --push-endpoint="${AGENT_ENDPOINT}" \
     --push-auth-service-account="${PROJECT_NUMBER}-compute@developer.gserviceaccount.com" \
     --project="${GOOGLE_CLOUD_PROJECT}"
   ```

---

### Step 4: Deploy Gateway Proxy to Cloud Run

Navigate to `gateway/` (where its `Dockerfile` and service files are located) and deploy the transient proxy to Cloud Run using the sourced environment variables:

```bash
cd gateway

gcloud run deploy spec-deliberator-gateway \
  --source . \
  --set-env-vars GOOGLE_CLOUD_PROJECT="${GOOGLE_CLOUD_PROJECT}",ENABLE_PUBSUB=true,GITHUB_WEBHOOK_SECRET="${GITHUB_WEBHOOK_SECRET}" \
  --allow-unauthenticated \
  --region "${DEFAULT_GOOGLE_CLOUD_LOCATION:-us-east1}" \
  --project "${GOOGLE_CLOUD_PROJECT}"

cd ..
```

---

### Step 5: Get Live Webhook URL & Wire to GitHub App

1. **Retrieve your live Cloud Run Gateway URL:**
   ```bash
   gcloud run services describe spec-deliberator-gateway \
     --region "${DEFAULT_GOOGLE_CLOUD_LOCATION:-us-east1}" \
     --project "${GOOGLE_CLOUD_PROJECT}" \
     --format 'value(status.url)'
   ```

2. **Verify Gateway Health:**
   ```bash
   curl $(gcloud run services describe spec-deliberator-gateway --region "${DEFAULT_GOOGLE_CLOUD_LOCATION:-us-east1}" --project "${GOOGLE_CLOUD_PROJECT}" --format 'value(status.url)')/health
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
