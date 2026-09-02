# Controlled framework and advanced-skill adapters

Jinwoo's **native mission engine is canonical**. It owns mission routing,
Planner → Executor → Verifier roles, policy classification, approval gates,
workspace boundaries, local-memory consent and the redacted local audit record.

External frameworks and GitHub-based skill projects are controlled integration
lanes, not independent always-on orchestrators. Their registry entry does not
install code, create a background agent, grant a tool, start a container or
authorise a network, shell, browser, desktop or mobile action.

## Registered adapter inventory

| Batch | Adapter | Owner | Intended later use | Current safe capability |
| --- | --- | --- | --- | --- |
| Core | Jinwoo Native Engine | Jinwoo | Visible mission/approval/audit control | Active local engine |
| 01 | Swarms | Bellion | Bounded hierarchical workers/specialists | Policy-screened dry run only |
| 01 | Agency-Swarm | Beru | Organisation-style hand-offs | Policy-screened dry run only |
| 01 | Ruflo | Igris | Local TypeScript/MCP developer harness | Policy-screened dry run only |
| 01 | LangGraph | Jinwoo | Checkpointed state/workflow primitives | Policy-screened dry run only |
| 01 | CrewAI | Beru | Bounded role-based crews | Policy-screened dry run only |
| 02 | AG2 | Bellion | Policy-mediated multi-agent hand-offs | Policy-screened dry run only |
| 02 | OpenHands | Igris | Isolated coding-task proposals and patch review | Policy-screened dry run only; no sandbox/runtime |
| 02 | Firecrawl | Tank | User-approved public-web collection | No-fetch plan/dry run only; **AGPL review required** |
| 02 | Firecrawl Web-Agent | Tank | Structured public-web research | No-fetch plan/dry run only |
| 02 | Crawl4AI | Tank | Bounded public-web collection | No-fetch plan/dry run only |
| 03 | Mem0 | Jinwoo | Explicitly consented memory interoperability | Policy-screened dry run only; SQLite remains authoritative |
| 03 | OpenClaw | Nox | Isolated local automation gateway | Policy-screened dry run only; no gateway/channel/skill starts |
| 03 | TruffleHog | Greed | Bounded local secret-exposure review | Policy-screened dry run only; **AGPL review required** |
| 03 | Gitleaks | Greed | Bounded local secret-scanner review | Policy-screened dry run only; no file/history scan |
| 03 | Jinwoo Native Control & Audit Review | Jinwoo | Local control-plane invariant review | Active, zero-side-effect native review |
| 04 | Goose | Igris | Sandboxed coding agent, tool protocol and evaluation patterns | Bounded plan only; no CLI/MCP/tool/edit/test/provider call |
| 04 | Orkas | Bellion | Desktop team routing, reflection and skill crystallisation patterns | Bounded review only; no independent queue, team or memory store |
| 04 | Bytebot | Nox | Container-desktop computer-use patterns | **Archived upstream**; no container or host-desktop access |
| 04 | OpenDesktop | Nox | Desktop computer use, voice and vision patterns | Bounded permission plan only; no capture or input control |
| 04 | Hermes Agent | Igris | Skill, local-state, MCP and coding-workflow patterns | Bounded review only; no skills/plugins/cron/gateway/provider starts |
| 04 | OpenAgent | Fang | RAG, tool routing and assistant patterns | Bounded review only; no service/auth/browser/computer/shell route |
| 04 | IRIS-GO | Bellion | Local multi-agent workflow/dashboard patterns | **Licence review required**; no source/runtime/system action |
| 04 | IRIS-Mini | Igris | CLI developer-workflow patterns | **Licence review required**; no source/runtime/terminal action |
| 04 | IRIS-Zero | Nox | Local terminal, voice and project-automation patterns | **Licence review required**; no source/runtime/action |
| 04 | Zoey | Ashborn | Privacy-first Rust local-agent patterns | Sandboxed review only; no binary/service/voice/provider start |
| 04 | IRIS-AI | Ashborn | Desktop voice, memory and vision UX concepts | **Reference only**; proprietary core/source/runtime excluded |
| 04 | IRIS-X | Ashborn | Future mobile-companion, voice and visual-context UX concepts | **Reference only**; proprietary engine/source/runtime excluded |
| 05 | AI Video Editor / AI Video Editor Pipeline | Tusk | Lawful local timeline, vision-assisted edit and export patterns | Bounded plan only; no editor/render/model/upload/protected-content route |
| 05 | Watch Video Skill / VideoDB Skills | Tusk | Authorised local video analysis, feedback and workflow patterns | Bounded plan only; no URL download, ingest, stream, service or media write |
| 05 | Anthropic Cybersecurity Skills (community) | Greed | Defensive standards mapping and threat-model patterns | Read-only defensive plan only; no targeting, scan, exploit or credential route |
| 05 | Anthropic Skills | Jima | Dynamic document, spreadsheet and workflow patterns | **Licence review required**; no script/component/file-production route |
| 05 | AI Research SKILLs | Blades | AI research, evaluation, infrastructure and paper patterns | Bounded plan only; no training/model/data/experiment/file-production route |
| 05 | Addy Osmani Agent Skills | Igris | API design, UI engineering and testing patterns | Bounded plan only; no hook/plugin/IDE/code/test/dependency route |
| 05 | WordPress Agent Skill Prototypes | Igris | WordPress theme/site and IDE/MCP patterns | **Licence review required**; no Studio/CLI/MCP/site/deploy/share/sync route |
| 05 | Composio | Fang | Connector, OAuth and external-action policy patterns | Bounded plan only; no toolkit/account/token/connector/action route |
| 05 | Stagehand | Nox | Browser-agent workflow patterns | Bounded plan only; no browser/URL/cookie/login/form/data-transfer route |
| 05 | LangChain Community Tools | Fang | Tool, retrieval and structured-workflow patterns | Bounded plan only; no community tool/network/filesystem route |
| 05 | Official MCP Servers | Fang | Individual MCP capability and server-boundary patterns | **Licence review required**; no MCP server/service/connection route |
| 05 | Awesome MCP Servers | Fang | Community MCP discovery list | **Reference only**; every downstream server needs individual review |
| 05 | MetaGPT / Microsoft AutoGen | Beru / Bellion | Multi-agent role and event-flow patterns | Bounded plan only; no independent state machine/agent/provider/tool route |
| 05 | Pydantic AI | Igris | Typed production-agent and structured-output patterns | Bounded plan only; no provider/tool/file/network route |
| 05 | Scientific Agent Skills | Tank | Scientific research/reproducibility/database-boundary patterns | Bounded plan only; no database/data upload/experiment route |
| 05 | Open-AutoGLM | Nox | Future Android screen-understanding and mobile-action design | **Queued companion phase**; no device/Accessibility/capture/input route |
| 05 | 500 AI Agents Projects | Ashborn | Agent use-case and blueprint catalogue | **Reference only**; linked projects need individual review |
| 05 | EnvAgent | Igris | Requested sandbox and runtime-bug-review capability | **Source review required**; exact GitHub URL/licence not yet supplied |
| 06 | Barehands Gesture Interface | Nox | Future local hand-gesture, spatial-board and accessibility patterns | **AGPL licence review required**; no webcam/CDN/state/localhost/gesture action route |
| 06 | Ultron Orb UI (Sagar Builds) | Tusk | Independently designed orb, HUD and optional gesture UX patterns | Bounded visual/interaction review only; no upstream source/camera/device/control route |
| 06 | Physical Cutter / Robotics Safety Intake | Nox | Physical-device safety and operator-consent concept | **Source/machine safety review required**; no controller, hardware or physical-action route |
| 07 | Agent Swarm | Bellion | Deliverable-driven specialist collaboration patterns | Native topology reference only; no upstream server/frontend/memory/runtime |
| 07 | ROMA | Ashborn | Recursive task-tree, planner/executor/verifier patterns | **Licence review required**; no MCP/Docker/toolkit/model/background execution |
| 07 | Open Multi-Agent | Bellion | Dynamic DAG, budget, recovery and governance patterns | Native topology reference only; no Node service/provider/tool/runtime |
| 07 | Awesome Agent Orchestration | Kaisel | Orchestration discovery and comparison catalogue | **Reference only**; every listed downstream source needs individual review |
| 07 | Microsoft Agent Framework | Jinwoo | Typed workflow, middleware and human-in-loop patterns | Native topology reference only; no hosted workflow/provider/tool/persistence |
| 08 | God's Eye View — Geospatial Safety Intake | Tank | Non-live geospatial visualisation, provenance and public-data boundary concepts | **Licence/data/asset review required**; no globe, live feed, tracking, camera, voice, location or provider runtime |

`GET /api/frameworks` exposes each record's runtime/category, discovery state,
licence, source URL, owner, capability tags, activation boundary and contract
state. `POST /api/frameworks/{framework_id}/dry-run` produces a typed,
policy-screened plan without importing, starting, downloading or calling an
upstream project.

A dry run accepts at most 450 **logical** agent requests, then caps the actual
proposal at three runtime workers: Planner, Executor and Verifier. It carries
out no tool action and records only redacted outcome metadata in the local audit
trail. A `reference-only` record produces a review that explicitly forbids
source/code/runtime use.

Batch 07 also provides a separate native Shadow Army planning surface:
`GET /api/shadow-army/overview`, `GET /api/shadow-army/plans`, and
`POST /api/shadow-army/plans`. It represents up to 450 logical seats and a
visible Planner → Executor → Verifier graph, returns at most ten representative
seats, caps a proposed runtime at three roles, and always reports zero started
workers and `external_runtime_invoked: false`. It never imports any registered
external framework. See [`INTEGRATION_BATCH_07.md`](INTEGRATION_BATCH_07.md).

## Native safety gates

### Greed no-scan security gate

`POST /api/security/scan-plan` and its Settings panel create a strictly
no-scan preflight for Gitleaks or TruffleHog. It requires a selected workspace
and explicit authorisation confirmation, but does not enumerate files, read Git
history, invoke a binary, verify credentials, upload findings or disclose a
candidate secret. Any future scan remains a separate approval-bound operation.

### Tank public-web research gate

`POST /api/research/plan` and the dashboard's **Research Gate** provide an
original Jinwoo-native no-fetch planning surface for Batch 02 web lanes. It
accepts a topic and at most ten explicit source URLs, makes no network request
or DNS lookup, and records only plan metadata in the audit trail.

It permits only explicit public HTTPS domain targets and rejects literal IPs,
localhost/local/internal hostnames, credentials, credential-like query
parameters and non-standard ports. Future execution must revalidate DNS and
connection targets, receive its own approval, honour source rules/robots and
rate/depth/size/domain limits, and retain cited data locally.

### Jinwoo native control & audit review

`POST /api/control/review` and its Settings panel provide a zero-side-effect
local review. It makes no network request, file read, tool call or
execution-state change. It verifies final Army capacity, native ownership,
external-runtime locks, Batch 03, Batch 04, Batch 05, Batch 06, Batch 07 and
Batch 08 inventories, restricted source/licence/review gates, read-only Workspace
Guard and audit availability.

## Why detection is not activation

An installed package or CLI must never silently alter Jinwoo's autonomy,
privacy, network behavior or tool access. Therefore all external adapters have
`execution_enabled: false`, even when detected on the local machine.

The following restrictions are specifically enforced in the registry:

- **Licence-review-required:** Firecrawl, TruffleHog, IRIS-GO, IRIS-Mini,
  IRIS-Zero, Anthropic Skills, WordPress Agent Skill Prototypes, Official MCP
  Servers, Barehands, ROMA and God's Eye View cannot be copied, bundled, linked,
  installed or run until their individual licence/component/deployment decision is
  documented. God's Eye View additionally requires its third-party data, asset,
  attribution, privacy and provider terms to be resolved per selected layer.
  Barehands additionally needs an AGPL-3.0 compatibility decision before any
  source, derivative, service or runtime is considered.
- **Archived upstream:** Bytebot cannot be adopted until a maintained source,
  security and support review passes.
- **Reference-only:** IRIS-AI, IRIS-X, Awesome MCP Servers, 500 AI Agents
  Projects and Awesome Agent Orchestration cannot be used as source/runtime
  integrations. Their downstream or
  proprietary sources need their own review; any Jinwoo feature must be
  independently designed.
- **Source-review-required:** EnvAgent and the Physical Cutter / Robotics Safety
  Intake have no selected upstream source/runtime. Jinwoo will not guess a
  repository, hardware controller or machine protocol or install a package until
  the owner supplies the exact evidence and it passes source/licence/safety review.
- **Queued companion phase:** Open-AutoGLM does not belong to desktop V1 and
  has no phone, Accessibility, screen-capture or input capability.
- **Computer-use, execution or external-tool lanes:** Goose, Bytebot,
  OpenDesktop, Hermes Agent, OpenAgent, IRIS-Mini, IRIS-Zero, Composio,
  Stagehand, LangChain Community and MCP sources receive no terminal, desktop,
  browser, capture, plugin, schedule, provider, account or credential access
  simply by being listed here.
- **Camera, gestures and physical hardware:** Barehands, Ultron Orb UI and the
  physical-device intake receive no webcam/microphone/screen permission,
  MediaPipe/CDN runtime, local-service call, Android/desktop input, USB/serial/
  Bluetooth/Wi-Fi/GPIO controller, motor, blade, laser, actuator or physical
  action merely by being present in the registry.

## Required activation gate for a later phase

An adapter can become executable only after all of the following are reviewed
and implemented:

1. Pin a compatible version/commit and preserve licence/NOTICE requirements.
2. Review telemetry, network and provider defaults; turn off unapproved routes.
3. Implement one narrow adapter contract with typed input/output.
4. Route every proposed action back through Jinwoo policy and user approval.
5. Restrict every file/tool operation to the user-selected workspace.
6. Record hand-offs, inputs, redacted outputs, errors and approval decisions in
   the local audit trail.
7. Add offline/no-key tests, bounded timeout/concurrency/token budgets and a
   rollback/disable path.
8. For coding tools, use a disposable sandbox and require a separate approval
   before any shell, patch, git, install or network action.
9. For web tools, deny private/authenticated targets, revalidate runtime
   connections against SSRF/rebinding, enforce source/rate/depth/size limits and
   preserve citation plus local-retention controls.
10. For memory tools, retain SQLite as the local source of truth; require
    renewed item-level consent before outbound sync and never assume “memo API”
    means Mem0 without owner confirmation.
11. For automation and computer-use tools, deny auto-start, pairing, messaging,
    schedules, skills, browser/desktop/voice/vision capture and shell access by
    default; require exact action preview plus a separate Jinwoo approval for
    every impactful step.
12. For secret scanners, never verify credentials over a network; require an
    approved workspace, a bounded read-only scan, redacted local findings and
    no automatic remediation.
13. For an archived, restrictive, unverified or reference-only source, resolve
    or preserve its source boundary **before** any dependency, binary,
    container, copied code or runtime implementation is considered.
14. For camera, gesture or hardware concepts, require fresh revocable consent,
    capture minimisation/local processing evidence, visible capture status,
    emergency stop, physical safeguarding, trained local operator and a separate
    machine-specific safety review before any physical/device action is considered.

### Boundary that never moves

| Concern | Owner |
| --- | --- |
| Mission state and queue | Jinwoo Native Engine |
| Policy classification and hard blocks | Jinwoo Native Engine |
| Approval cards for impactful actions | Jinwoo Native Engine |
| Workspace/path confinement | Igris Workspace Guard under Jinwoo policy |
| Audit log and memory privacy | Jinwoo Native Engine |

See [`INTEGRATION_BATCH_01.md`](INTEGRATION_BATCH_01.md),
[`INTEGRATION_BATCH_02.md`](INTEGRATION_BATCH_02.md),
[`INTEGRATION_BATCH_03.md`](INTEGRATION_BATCH_03.md),
[`INTEGRATION_BATCH_04.md`](INTEGRATION_BATCH_04.md),
[`INTEGRATION_BATCH_05.md`](INTEGRATION_BATCH_05.md),
[`INTEGRATION_BATCH_06.md`](INTEGRATION_BATCH_06.md),
[`INTEGRATION_BATCH_07.md`](INTEGRATION_BATCH_07.md), and
[`INTEGRATION_BATCH_08.md`](INTEGRATION_BATCH_08.md) for the source-review
records and adapter-specific activation requirements.
