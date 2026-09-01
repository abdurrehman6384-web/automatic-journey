# Controlled multi-agent framework adapters

Jinwoo's **native mission engine is canonical**. It owns mission routing,
Planner → Executor → Verifier roles, policy classification, approval gates,
workspace boundaries, and the local audit record.

External frameworks are integration lanes rather than independent always-on
orchestrators. This prevents competing agent loops and preserves the
local-first safety model.

## Batch 01: contract-ready, non-executable adapters

The first owner-requested batch is now registered:

| Adapter | Intended later use | Current safe capability |
|---|---|---|
| Swarms | Bounded hierarchical workers/specialists | Policy-screened dry run only |
| Agency-Swarm | Organisation-style hand-offs | Policy-screened dry run only |
| Ruflo | Local TypeScript/MCP developer harness | Policy-screened dry run only |
| LangGraph | Checkpointed state/workflow primitives | Policy-screened dry run only |
| CrewAI | Bounded role-based crews | Policy-screened dry run only |

`GET /api/frameworks` shows package/CLI discovery and the contract state.
`POST /api/frameworks/{framework_id}/dry-run` produces a typed plan without
importing, starting, downloading, or calling an upstream framework.

A dry run accepts at most 450 **logical** agent requests, then caps the actual
proposal at three runtime workers: Planner, Executor and Verifier. It carries
out no tool action and records only redacted metadata in the local audit trail.

## Why detection is not activation

An installed package or CLI must never silently alter Jinwoo's autonomy,
privacy, network behavior or tool access. Therefore all external adapters have
`execution_enabled: false`, even when detected on the local machine.

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

### Boundary that never moves

| Concern | Owner |
|---|---|
| Mission state and queue | Jinwoo Native Engine |
| Policy classification and hard blocks | Jinwoo Native Engine |
| Approval cards for impactful actions | Jinwoo Native Engine |
| Workspace/path confinement | Igris Workspace Guard under Jinwoo policy |
| Audit log and memory privacy | Jinwoo Native Engine |

See [`INTEGRATION_BATCH_01.md`](INTEGRATION_BATCH_01.md) for the reviewed
upstream reference pins, licences and the next two owner-requested batches.
