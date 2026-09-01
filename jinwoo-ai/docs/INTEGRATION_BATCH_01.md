# Integration Batch 01 — controlled multi-agent foundations

This is the first owner-requested batch, interpreted in the order supplied:

1. Swarms
2. Agency-Swarm
3. Ruflo
4. LangGraph
5. CrewAI

These are **integration lanes**, not replacements for Jinwoo, Bellion, or the
15 named Shadow Army commanders. Jinwoo Native remains the canonical mission
state machine and policy authority.

## What is implemented in this batch

- A typed registry reports source URL, licence, responsible commander, runtime,
  batch number, package/CLI discovery state and implementation state.
- Each of the five has a **contract-ready**, policy-gated dry-run adapter.
- `POST /api/frameworks/{framework_id}/dry-run` accepts a requested plan and
  logical agent count (1–450), screens it through Jinwoo policy, and caps the
  actual runtime proposal at **three** Planner/Executor/Verifier workers.
- A dry run never imports, starts, downloads, calls or delegates to an upstream
  framework. It records only redacted outcome metadata in the local audit log.
- Settings exposes each framework’s state and lets the user run the safe dry
  run. No button enables external execution.

This gives the application one tested integration contract before any third
party agent loop is introduced. “Unlimited agents” is treated as logical
capacity, never an unlimited concurrent-process permission.

## Reviewed upstream references

The following immutable-ish upstream HEADs were observed on **2026-09-01**.
They are reference metadata only; no upstream source was copied into this
repository.

| Integration | Upstream | Observed HEAD | Licence shown upstream | Jinwoo responsibility |
|---|---|---|---|---|
| Swarms | <https://github.com/kyegomez/swarms> | `3977d785dcf8a4d66456ef3e0928d0783d0dc675` | Apache-2.0 | Bellion: bounded hierarchical worker patterns |
| Agency-Swarm | <https://github.com/VRSEN/agency-swarm> | `4d1c35a6dd5ef038a5d15b39803459ff0b5f5578` | MIT | Beru: policy-gated organisation hand-offs |
| Ruflo | <https://github.com/ruvnet/ruflo> | `29f048fc3b556f857cf2b126d2a84c19d2daa0d0` | MIT | Igris: optional local TypeScript/MCP developer bridge |
| LangGraph | <https://github.com/langchain-ai/langgraph> | `11ee185999b86bfea2d8c0e69cef9a5e37acf686` | MIT | Jinwoo: checkpointed state-workflow primitives |
| CrewAI | <https://github.com/crewAIInc/crewAI> | `ec53d6f53448fcc7842f4d4d5f3272d2e7782557` | MIT | Beru: bounded role-based crews |

A release must re-check each selected tag/commit, licence/NOTICE obligations,
transitive dependencies, telemetry defaults, provider requirements, and known
security advisories before adding an optional runtime dependency.

## Activation checklist — one integration at a time

An upstream package/sidecar remains disabled until all items below pass:

1. Pin an exact version/commit and preserve required licence attribution.
2. Review the package’s network, telemetry and provider defaults; turn off any
   unapproved cloud or telemetry route.
3. Implement a narrow adapter with typed input/output rather than exposing the
   framework’s raw tool interface.
4. Preserve Jinwoo policy screening before delegation and before every proposed
   tool action.
5. Restrict filesystem work to the user-selected Workspace Guard root.
6. Keep destructive, terminal, install, upload, send and desktop actions behind
   a visible user approval card.
7. Add offline/no-key tests, a timeout, bounded concurrency/token budget and a
   rollback/disable switch.
8. Record redacted hand-off and outcome metadata in the local audit log.

## Subsequent owner-requested batches

**Batch 02 is now registered as controlled, non-executing contracts:** AG2,
OpenHands, Firecrawl, Firecrawl Web-Agent and Crawl4AI. Its review pins,
no-fetch Tank planner and adapter-specific boundaries are documented in
[`INTEGRATION_BATCH_02.md`](INTEGRATION_BATCH_02.md). Firecrawl remains blocked
from activation pending an AGPL-3.0 compatibility decision.

Only **Batch 03** remains queued: Mem0, OpenClaw, TruffleHog, Gitleaks, then a
final review of the Jinwoo Native control/audit lane as the fifteenth integration
lane. It starts only on a later explicit owner instruction. The same
supply-chain and safety checklist applies before any runtime is enabled.
