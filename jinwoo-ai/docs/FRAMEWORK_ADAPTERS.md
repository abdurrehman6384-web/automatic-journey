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
external-runtime locks, Batch 03 and Batch 04 inventories, restricted source
and licence gates, read-only Workspace Guard and audit availability.

## Why detection is not activation

An installed package or CLI must never silently alter Jinwoo's autonomy,
privacy, network behavior or tool access. Therefore all external adapters have
`execution_enabled: false`, even when detected on the local machine.

The following restrictions are specifically enforced in the registry:

- **Licence-review-required:** Firecrawl, TruffleHog, IRIS-GO, IRIS-Mini and
  IRIS-Zero cannot be copied, bundled, linked, installed or run until their
  individual licence and deployment decision is documented.
- **Archived upstream:** Bytebot cannot be adopted until a maintained source,
  security and support review passes.
- **Reference-only:** IRIS-AI and IRIS-X cannot be used as source/runtime
  integrations. Their proprietary cores remain excluded; any Jinwoo feature
  must be independently designed.
- **Computer-use or execution lanes:** Goose, Bytebot, OpenDesktop, Hermes
  Agent, OpenAgent, IRIS-Mini and IRIS-Zero receive no terminal, desktop,
  browser, capture, plugin, schedule, provider or credential access simply by
  being listed here.

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
[`INTEGRATION_BATCH_03.md`](INTEGRATION_BATCH_03.md), and
[`INTEGRATION_BATCH_04.md`](INTEGRATION_BATCH_04.md) for the source-review
records and adapter-specific activation requirements.
