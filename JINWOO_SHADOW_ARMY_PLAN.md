# JINWOO AI — SHADOW ARMY
## Complete Detailed Master Plan — Final Compiled Version

**Status:** Authoritative active plan
**Primary target:** Local-first desktop application, Windows first
**Initial delivery:** Three delivery phases over the V1 roadmap
**Brand direction:** Original Shadow Army-inspired command-center experience

> This plan merges the latest hierarchy decision with the provider, local-AI,
> privacy, desktop and implementation requirements. Earlier 10-team/20-agent
> numbers are superseded by the final **3 sub-departments × 10 agents** model.

---

## 1. Main Vision

**Jinwoo AI** ek **Local-First Desktop AI Command Center** hai. User natural
language mein command dega aur Jinwoo visible, safe aur scalable Shadow Army
workflow ke through task complete karega.

Example requests:

```text
“Mera project analyze karo.”
“Is bug ka solution do.”
“Market research report banao.”
“Local AI models compare karo.”
“Mere system ki health check karo.”
“Is file ka summary banao.”
```

### Execution flow

```text
User Command
    ↓
Jinwoo Boss (Shadow Monarch)
    ↓
Bellion (Grand Marshal)
    ↓
Correct Commander
    ↓
Sub-Department → selected Agents
    ↓
Planner + Executor + Verifier
    ↓
Approval Gate, agar zarurat ho
    ↓
Result + Logs + Memory
```

### V1 outcome

- Jinwoo Army HQ dashboard;
- local and optional cloud AI chat;
- visible mission plans, queue and history;
- 15 commander roles with scalable agents;
- Igris development and Tank research as first real departments;
- local memory and Memory Vault;
- explicit approval and audit trail for impactful actions;
- Electron desktop shell after the local app is stable.

---

## 2. Core Philosophy and Hard Rules

```text
Local-first by default
Cloud only with explicit user permission
User privacy absolute
No hidden actions
No uncontrolled terminal execution
No risky task without approval
No API keys in frontend
No automatic repo merge
No automatic model download
No automatic sending, uploading or deleting
```

Sensitive workspace data user ki clear permission ke baghair cloud provider ko
nahi bheja jayega. Jinwoo plan, tool, result aur important permission state
user ko screen par clearly dikhayega.

---

## 3. Final Hierarchy

```text
Jinwoo Boss — Shadow Monarch
        ↓
Bellion — Grand Marshal (Controller)
        ↓
15 Commander Roles
        ↓
Har Commander ke paas → 3 Sub-Departments
        ↓
Har Sub-Department mein → 10 Logical Agents
        ↓
Har selected Agent ke paas → Planner + Executor + Verifier
```

### Capacity calculation

```text
15 commanders × 3 sub-departments × 10 agents = 450 logical agents
450 logical agents × 3 worker roles = 1,350 logical worker slots
```

Yeh visual/organizational capacity hai. App 450 ya 1,350 LLM requests ek saath
run nahi karega. Runtime par mission ke liye sirf required workers spawn honge,
for example one Planner, one Executor aur one Verifier.

### Scaling rule

- Base hierarchy fixed aur easy-to-understand rahegi.
- Extra sub-departments ya agents config/data se add ho sakenge.
- Concurrency, token budget, provider budget aur queue limits enforced honge.
- Koi worker infinite loop ya background hidden process nahi banega.

---

## 4. Fifteen Commanders

| No. | Commander | Title | Department | V1 responsibility |
|---:|---|---|---|---|
| 1 | Jinwoo | Shadow Monarch | Supreme Command | user request, final decision, mission answer |
| 2 | Bellion | Grand Marshal | Controller | routing, queue, commander coordination |
| 3 | Igris | Blood-Red Commander | Development | code, architecture, tests, safe patches |
| 4 | Beru | Ant King | Managers | task distribution, workflow and maintenance |
| 5 | Tusk | High Orc Warlock | Features | creative features, UI, animation, media briefs |
| 6 | Iron | Shield Bearer | Business | business plan, marketing drafts, MVP scope |
| 7 | Tank | Ice Bear | Researchers | public research, data and reports |
| 8 | Kaisel | Shadow Dragon | Upgrading | tool discovery, upgrade proposal, version review |
| 9 | Jima | Shadow Scribe | Scribes | documentation, knowledge and reports |
| 10 | Greed | Shadow Guardian | Security | defensive security, privacy and secret hygiene |
| 11 | Shadow | Error Hunter | Quality Assurance | tests, bugs and regression checks |
| 12 | Fang | Link Phantom | Integration | APIs, service connections and module contracts |
| 13 | Blades | Mind Forger | Training | evaluation, prompts and approved training experiments |
| 14 | Nox | Night Executor | Operations | opt-in schedules, resources and health monitoring |
| 15 | Ashborn | Future Specter | Innovation | sandbox experiments and future research |

---

## 5. Three Sub-Departments per Commander

| Commander | Sub-department 1 | Sub-department 2 | Sub-department 3 |
|---|---|---|---|
| Jinwoo | Mission Control | Final Decision | User Interface Layer |
| Bellion | Routing and Queue | Commander Coordination | Mission Monitoring |
| Igris | Core Engine | Intelligence Layer | Delivery and Safety |
| Beru | Task Distribution | Workflow Management | Update and Maintenance |
| Tusk | Creative Production | Editing and Tools | Agent Factory |
| Iron | Business Planning | Marketing and Growth | MVP and Expansion |
| Tank | Public Research | Data Extraction | Report Generation |
| Kaisel | Tool Discovery | Safe Integration | Version Management |
| Jima | Documentation | Knowledge Base | Report Writing |
| Greed | Privacy Guard | Secret Scanner | Policy Enforcer |
| Shadow | Testing | Bug Hunting | Regression |
| Fang | API Linking | Service Connection | Module Integration |
| Blades | Model Evaluation | Prompt Engineering | Agent Training |
| Nox | Scheduling | Resource Management | Health Monitoring |
| Ashborn | Experimentation | Future Research | Prototype Development |

### Igris implementation focus

Igris ke pehle agent templates honge:

```text
Architecture Analyst
Code Generator
Bug Crusher
Test Designer
API Forge
Database Shadow
Performance Optimizer
Security Code Reviewer
Release Planner
Documentation Handoff
```

Inmein se task ke mutabiq only selected roles run honge.

---

## 6. Worker Model

Har selected agent ke neeche three internal worker roles:

| Worker | Responsibility |
|---|---|
| **Planner** | task breakdown, risk analysis, success criteria and allowed tools |
| **Executor** | safe draft, research result or approved action proposal |
| **Verifier** | output quality, evidence, policy and completion validation |

Worker contract:

```text
Role
Prompt/instructions
Input schema
Output schema
Allowed tools
Workspace/data scope
Risk class
Token/time budget
Audit event
Tests
```

Worker ka goal arbitrary “100 lines of code” nahi hoga. Quality measure hoga:
correctness, tests, clear interface, rollback, documentation aur security.

---

## 7. Core Technical Stack

### Languages

| Technology | Role |
|---|---|
| **Python** | primary backend, orchestration, FastAPI, tools and local-AI adapters |
| **TypeScript + React** | Army HQ UI, chat, typed contracts and dashboard state |
| **Electron** | desktop shell, tray, secure storage and desktop IPC boundary |
| **Rust** | optional high-performance indexing/parsing sidecar after profiling |
| **Go** | optional fast local service after a measured concurrency need |

Python is the main brain. Rust and Go are not added just for language count;
they are added only when a measured bottleneck needs them.

### Frontend

```text
React
TypeScript
Vite initially, Next.js-compatible architecture where needed
Tailwind CSS / Shadcn UI when source integration begins
Electron desktop shell
```

### Local backend

```text
FastAPI
Uvicorn
Typed JSON API
Optional gRPC for Python ↔ Rust/Go sidecars
```

---

## 8. Local AI and LLM Stack

### Local providers

| Component | Role |
|---|---|
| Ollama | default local model runtime |
| LM Studio | easy local model management and local compatible endpoint |
| llama.cpp | lightweight GGUF/CPU-friendly local models |
| vLLM | advanced high-throughput GPU profile |
| Hugging Face Transformers | offline embeddings, reranking, classification and approved local models |
| LangGraph | supporting graph/state workflow primitives |
| LangChain | optional tool/provider helpers |
| LlamaIndex | local document ingestion and knowledge retrieval |

### Supported model families

```text
Llama 3.1 / 3.2
Qwen 2.5
Mistral / Mixtral
DeepSeek
Gemma 2
Phi-3 / Phi-4
```

The Settings screen will recommend a model based on CPU, RAM, GPU and task type.
Models never download automatically without user confirmation.

### Local profiles

```text
Lite profile
→ SQLite + Ollama or llama.cpp + local logs

Standard profile
→ SQLite + LanceDB/Chroma + Ollama or LM Studio + desktop shell

Power profile
→ PostgreSQL + Redis + vLLM + optional Grafana

Developer profile
→ Docker Compose + mock providers + tests + observability
```

---

## 9. Multi-Agent Framework Strategy

The requested frameworks are included, but they will not all execute the same
mission at the same time. One mission must have one canonical, auditable state
machine.

```text
Jinwoo Native Mission Engine
├── Swarms adapter        → hierarchical worker/specialist patterns
├── Agency-Swarm adapter  → organisation-style handoffs where compatible
└── Ruflo bridge          → optional TypeScript/MCP meta-harness integration
```

### Framework responsibilities

| Framework | Jinwoo role |
|---|---|
| Swarms | optional worker-swarm patterns for selected multi-agent missions |
| Agency-Swarm | optional role/organisation handoff adapter |
| Ruflo | optional MCP/developer swarm, adaptive memory and evaluation bridge |
| Jinwoo mission engine | source of truth for policy, approvals, mission state and audit logs |

Rules:

- Framework integration is feature-flagged and version-pinned after tests.
- A framework may propose actions but cannot bypass Jinwoo approval policy.
- Ruflo, Swarms and Agency-Swarm are integrations, not a reason to duplicate
  memory, queues or worker state.
- V1 starts with Jinwoo’s native deterministic mission engine; framework
  adapters are added one by one after a working baseline.

---

## 10. AI Provider Gateway

```text
Desktop UI / Electron
        ↓
Python FastAPI backend
        ↓
Provider Gateway + Model Router
        ↓
Local Providers or Optional Cloud Providers
```

### Cloud providers

| Provider | Intended use |
|---|---|
| Claude API | complex planning, coding, verification, long documents and tool-use reasoning |
| GLM / Z.ai API | general/coding alternative and configurable fallback |
| Hugging Face API | hosted inference, embeddings, reranking and approved model experiments |
| Mem0 API | optional cloud memory sync if “memo API” means Mem0 |
| OpenAI/Groq/Gemini/OpenRouter/DeepSeek | optional adapters, not a separate app rewrite |

### Provider router rules

```text
Task requirements
→ local/cloud preference
→ model capability check
→ privacy/data boundary check
→ token/cost/time budget
→ provider health check
→ selected provider
```

Example:

```text
Local coding draft      → Ollama / LM Studio
Hard architecture task  → Claude, only if cloud use is enabled
Coding fallback         → GLM
Document retrieval      → local HF embeddings / LanceDB
Long-term memory        → SQLite first, Mem0 only if enabled
```

### API security

```text
No key in browser code
No key in Git
No key in localStorage
Development keys in ignored .env
Release keys in OS secure storage/keychain
Provider calls happen in backend/main process only
```

The current project includes provider configuration/adapters for Ollama, LM
Studio, Claude, GLM and Hugging Face. Demo mode sends no external request.

---

## 11. Data and Memory System

### Three memory layers

1. **Short-term mission memory**
   - current chat, plan, workers, tool results and temporary context.

2. **Project memory**
   - per-workspace architecture, approved conventions, known bugs and reports.

3. **User preference memory**
   - language, response style, preferred provider and explicitly saved choices.

### Storage

```text
SQLite                    default local app database
LanceDB or ChromaDB       local vector/document retrieval
PostgreSQL                optional advanced local profile
Redis                     optional worker queue/cache
DuckDB                    local analytics and reporting
Mem0                      optional opt-in remote memory adapter
```

### Memory rules

```text
User can view, edit, export and delete memory
Sensitive secrets are filtered
No memory is sent to cloud without provider consent
Local SQLite remains available when cloud memory is disabled
Memory never overrides current user instruction or safety policy
```

---

## 12. Safety System and Workspace Guard

### Low-risk actions — allowed to prepare automatically

```text
File read inside selected workspace
Code analysis
Research plan
Summary generation
Draft report/document
Local diagnostics readout
```

### Explicit approval required

```text
File write, delete or rename
Terminal command
Package install/uninstall
External upload/send/publish
Desktop mouse/keyboard action
System setting change
Android-device action
```

### Hard blocked

```text
Credential stealing
Keylogging
Spyware
Hidden recording
PIN/password bypass
Unauthorized system changes
Unauthorised scanning/exploitation
```

### Workspace confinement

All V1 file and coding actions are restricted to a user-selected **workspace
folder**. The backend resolves canonical paths and rejects paths escaping that
folder. System-wide work is a separate, explicit future capability; it is not
silently granted by enabling Jinwoo.

---

## 13. Department Boundaries

### Tusk — Features

May create design briefs, UI drafts, approved images/video workflows and media
plans. `yt-dlp` and `ffmpeg` are optional local media tools, limited to content
the user owns or is permitted to process, and actions remain approval-gated.

### Tank — Researchers

Uses public websites, approved APIs, user-provided documents and legal data
sources. It does not crawl private, hidden or unauthorised systems.

### Greed — Security

Defensive only:

```text
Secret exposure checks
Dependency review
Privacy configuration
Workspace security reports
Encryption/backup recommendations
```

### Kaisel — Upgrading

Never auto-merges a repository. Upgrade pipeline:

```text
Discover candidate
→ licence/dependency/security review
→ sandbox test
→ compatibility report
→ user approval
→ isolated integration branch
→ regression tests
→ release/canary
→ rollback option
```

---

## 14. User Interface

### Main screens

1. **Onboarding**
   - user name, language, local/cloud mode, provider setup and privacy choice.

2. **Command Center**
   - chat, attachments, selected commander, mission plan, live worker state,
     approval cards and result.

3. **Army HQ**
   - animated Shadow Gate, 15 commander cards, task queue, active missions,
     provider status, memory health and system summary.

4. **Mission Detail**
   - user request, plan, worker roles, evidence, tool calls, approval history,
     logs and exportable report.

5. **Approvals Center**
   - approve once, approve for mission, modify, reject and category settings.

6. **Memory Vault**
   - local memories, search, edit, delete, export and Mem0 status.

7. **Settings**
   - local models, cloud providers, routing preference, workspace, privacy,
     diagnostics and developer mode.

### Important components

```text
src/data/army.ts
src/components/ShadowGate.tsx
src/components/ArmyHQ.tsx
src/components/CommanderCard.tsx
src/components/MissionPanel.tsx
src/components/ProviderPanel.tsx
src/components/FrameworkPanel.tsx
src/components/ApprovalPanel.tsx
src/components/MemoryVault.tsx
```

---

## 15. Local DevOps, Monitoring and Security

```text
Docker + Docker Compose      optional profile-based services
Git                          local-first source control
GitHub                       optional and user-approved
uv                           preferred Python environment manager
Makefile/Taskfile            developer commands
Structured logs              default V1 observability
Prometheus + Grafana         optional local monitoring profile
Self-hosted Sentry           optional error monitoring
JWT                          only where a local API boundary needs identity
Firewall rules               host/user configuration, services loopback by default
```

Useful commands:

```bash
make dev
make test
make build
make desktop
make local-model
make doctor
make up
make down
```

---

## 16. Three Delivery Phases

### Phase A — Foundation and Intelligence (Weeks 1–3)

```text
Phase 0: source audit, project setup, repository cleanup
Phase 1: core chat, local demo mode, Ollama/LM Studio route
Phase 2: Bellion routing, mission system, provider gateway
```

**Output:** Local app opens, user can chat, create missions, select providers
and see a safe plan.

### Phase B — Army and Safe Development (Weeks 4–6)

```text
Phase 3: Army HQ UI and all 15 commander cards
Phase 4: Igris as first real development commander
Phase 5: approval gate, workspace guard, audit logs
```

**Output:** Army HQ is real, Igris can analyse selected code and propose safe
changes, while write/terminal actions require approval.

### Phase C — Knowledge, Research and Desktop Release (Weeks 7–10)

```text
Phase 6: Tank research and cited report workflows
Phase 7: Memory Vault, vector retrieval, polish and tests
Phase 8: Electron packaging, Windows testing and release checklist
```

**Output:** Local desktop V1 with memory, research, testing and packaging
foundation.

---

## 17. Detailed V1 Roadmap

| Phase | Focus | Target |
|---:|---|---|
| 0 | Foundation and source audit | Week 1 |
| 1 | Core chat and local AI | Week 2 |
| 2 | Bellion and mission system | Week 3 |
| 3 | Army HQ with 15 commanders | Week 4 |
| 4 | Igris first real department | Week 5 |
| 5 | Approval gate and safety | Week 6 |
| 6 | Tank research workflows | Week 7 |
| 7 | Memory Vault and polish | Week 8 |
| 8 | Desktop packaging and testing | Weeks 9–10 |

### Strict V1 scope

```text
Local AI chat
15 commander cards
450 logical agents in configuration
Dynamic mission system
Approval gate
Igris + Tank as first real departments
Local Memory Vault
Safe workspace tools
Electron desktop app foundation
```

Not V1:

```text
Unbounded autonomous agents
System-wide hidden automation
Automatic GitHub merging
Automatic model training
Remote multi-device federation
Android Live2D companion
```

---

## 18. Current Implementation Status

The first runnable foundation is already located in `jinwoo-ai/`:

```text
React + TypeScript Army HQ
Local-first chat with explicit per-message cloud approval
Animated Shadow Gate
15 commander cards
Python FastAPI local backend
Mission routing and worker contracts
Approval gate and blocked-action policy
Redacted local audit events for mission and memory decisions
SQLite consent-based memory with view, edit, delete and local JSON export controls
Credential and one-time-code rejection before memory storage
Provider registry/adapters for local and cloud routes
Controlled framework-status registry for Jinwoo Native, Swarms, Agency-Swarm and Ruflo
Docker Compose foundation
Electron shell foundation
Automated backend tests
```

The UI and backend now use the final hierarchy: **45 sub-departments, 450
logical agents and 1,350 logical worker slots**. Framework presence is visible
in Settings, but optional adapters remain non-executable until their individual
review and policy-gated implementation.

---

## 19. Remaining Work

```text
Merge custom workspace source once it is available locally
Build provider Settings UI and OS secure keychain storage
Connect one real local provider first: Ollama or LM Studio
Add Claude, GLM and HF live-provider integration tests with user-owned keys
Implement Igris workspace tools behind the approval gate
Implement Tank approved research/source citation flow
Add local vector retrieval and Memory Vault search
Implement reviewed, version-pinned framework execution adapters one at a time: Swarms, Agency-Swarm, Ruflo
Add Electron packaging and Windows installer
Add Rust/Go sidecars only after profiling
```

---

## 20. Inputs Needed from Owner

1. Confirm whether **“memo API” = Mem0**.
2. Choose the first real provider:
   - Ollama,
   - LM Studio,
   - Claude,
   - GLM, or
   - Hugging Face.
3. Share target machine details: Windows version, RAM, CPU and GPU.
4. Directly attach a source-only custom ZIP or a GitHub repository for exact
   custom code integration. Exclude `node_modules`, `.next`, `dist`, `build`,
   `.git` and real `.env` files.
5. Do not paste API keys into chat. They will be entered only through local
   secure configuration.
