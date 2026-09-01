# Controlled framework adapters

Jinwoo's **native mission engine is canonical**. It owns mission routing,
Planner → Executor → Verifier roles, policy classification, approval gates,
workspace boundaries, and the local audit record.

External frameworks are controlled integration lanes, not independent always-on
orchestrators. This prevents competing agent loops and preserves the
local-first safety model.

## Registered adapter inventory

| Batch | Adapter | Intended later use | Current safe capability |
| --- | --- | --- | --- |
| Core | Jinwoo Native Engine | Visible mission/approval/audit control | Active local engine |
| 01 | Swarms | Bounded hierarchical workers/specialists | Policy-screened dry run only |
| 01 | Agency-Swarm | Organisation-style hand-offs | Policy-screened dry run only |
| 01 | Ruflo | Local TypeScript/MCP developer harness | Policy-screened dry run only |
| 01 | LangGraph | Checkpointed state/workflow primitives | Policy-screened dry run only |
| 01 | CrewAI | Bounded role-based crews | Policy-screened dry run only |
| 02 | AG2 | Policy-mediated multi-agent hand-offs | Policy-screened dry run only |
| 02 | OpenHands | Isolated coding-task proposals and patch review | Policy-screened dry run only; no sandbox/runtime |
| 02 | Firecrawl | User-approved public-web collection | No-fetch plan/dry run only; **AGPL review required** |
| 02 | Firecrawl Web-Agent | Structured public-web research | No-fetch plan/dry run only |
| 02 | Crawl4AI | Bounded public-web collection | No-fetch plan/dry run only |

`GET /api/frameworks` exposes runtime/category, discovery state, licence and
contract state. `POST /api/frameworks/{framework_id}/dry-run` produces a typed,
policy-screened plan without importing, starting, downloading, or calling an
upstream framework.

A dry run accepts at most 450 **logical** agent requests, then caps the actual
proposal at three runtime workers: Planner, Executor and Verifier. It carries
out no tool action and records only redacted metadata in the local audit trail.

## Tank public-web research gate

`POST /api/research/plan` and the dashboard's **Research Gate** provide an
original Jinwoo-native, no-fetch planning surface for Batch 02 web lanes. It
accepts a topic and at most ten explicit source URLs, makes no network request
or DNS lookup, and records only plan metadata in the audit trail.

It permits only explicit public HTTPS domain targets and rejects literal IPs,
localhost/local/internal hostnames, credentials, credential-like query
parameters and non-standard ports. Future execution must revalidate DNS
and connection targets, receive its own approval, honour source rules/robots
and rate/depth/size/domain limits, and retain cited data locally.

## Why detection is not activation

An installed package or CLI must never silently alter Jinwoo's autonomy,
privacy, network behavior or tool access. Therefore all external adapters have
`execution_enabled: false`, even when detected on the local machine.

Firecrawl is additionally `license-review-required`: no Firecrawl upstream code
is copied, bundled, linked, started, or distributed here. Its AGPL-3.0
obligations need an explicit project-owner decision and appropriate legal review
before any Firecrawl runtime/container/service work.

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

### Boundary that never moves

| Concern | Owner |
|---|---|
| Mission state and queue | Jinwoo Native Engine |
| Policy classification and hard blocks | Jinwoo Native Engine |
| Approval cards for impactful actions | Jinwoo Native Engine |
| Workspace/path confinement | Igris Workspace Guard under Jinwoo policy |
| Audit log and memory privacy | Jinwoo Native Engine |

See [`INTEGRATION_BATCH_01.md`](INTEGRATION_BATCH_01.md) and
[`INTEGRATION_BATCH_02.md`](INTEGRATION_BATCH_02.md) for review pins, licences,
and adapter-specific activation requirements. Batch 03 remains queued until the
owner explicitly requests it.
