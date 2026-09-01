# Controlled Integration Batch 03 — Final Lane

**Status:** the final requested adapter contracts and Jinwoo-native control review are implemented. No Batch 03 upstream package, binary, source file, container, service, gateway, messaging channel, scanner, browser, credential verifier, or cloud route is installed or executed by Jinwoo.

This completes the owner's staged **contract** inventory. It does not activate an upstream runtime. Jinwoo remains the sole canonical mission engine and retains policy, approval, workspace, privacy and audit ownership.

## Reviewed upstream references

The following upstream HEADs were observed on **2026-09-01**. They are review
references only, not dependency pins.

| Adapter ID | Project | Upstream source | Observed HEAD | Licence | Jinwoo owner | Contract state |
| --- | --- | --- | --- | --- | --- | --- |
| `mem0` | Mem0 | <https://github.com/mem0ai/mem0> | `71fba8d46436f88569d600f81a55208c38ad30b5` | Apache-2.0 | Jinwoo | Contract-ready, execution disabled |
| `openclaw` | OpenClaw | <https://github.com/openclaw/openclaw> | `e8c3fbc05b6b3efed2e27526ddd558a7079c02f3` | MIT | Nox | Contract-ready, execution disabled |
| `trufflehog` | TruffleHog | <https://github.com/trufflesecurity/trufflehog> | `74dcf3f1bdeb0f6ad28061e49bcd29f297634a67` | AGPL-3.0 | Greed | **Licence review required; execution disabled** |
| `gitleaks` | Gitleaks | <https://github.com/gitleaks/gitleaks> | `b58d3f102cf3a2c84cb7f923d05c25c9b1aed84b` | MIT | Greed | Contract-ready, execution disabled |
| `jinwoo-native-control-audit` | Jinwoo Native Control & Audit Review | This repository | n/a | Original project code | Jinwoo | Active local review; no external execution |

The observed commits are review references, not installed dependency pins. No upstream source is copied into this repository.

## What is implemented locally

### All four external lanes

- `GET /api/frameworks` exposes the Batch 03 runtime/category, source, licence, commander owner and readiness state.
- `POST /api/frameworks/{framework_id}/dry-run` produces a policy-screened plan for all Batch 03 entries. It accepts 1–450 logical requests but proposes at most three runtime roles: Planner, Executor and Verifier.
- Every external result reports `external_runtime_invoked: false`; discovery of a local package/CLI never enables it.
- Greed's `POST /api/security/scan-plan` and Settings panel create a no-scan preflight only after a user-selected workspace and explicit authorisation confirmation. It never reads a file, Git history, key, scanner result or credential.

### Mem0

Mem0 is an optional, separately consented memory-interoperability contract. SQLite remains the local source of truth and no sync is added. The owner's earlier ambiguous phrase **“memo API” is still not treated as confirmation that it means Mem0**; this record only covers the explicitly requested Mem0 project.

### OpenClaw

OpenClaw is modelled as a future isolated automation gateway. The contract blocks messaging channels, pairing, schedules, skills, browser access and shell tools. A future implementation must not receive direct UI control or run as an independent always-on orchestrator.

### TruffleHog and Gitleaks

Both security lanes are plan-only. They do not read workspace files, scan Git history, transmit candidate values, verify a discovered credential, or place a secret in an audit event or UI result. Future scan findings must be redacted and local-only.

TruffleHog is marked `license-review-required` because its reviewed project is AGPL-3.0. As with Firecrawl, no code/binary/container/service use is permitted until the project owner records a compatible deployment/distribution decision with appropriate legal review.

### Jinwoo Native Control & Audit Review

`POST /api/control/review` and the Settings panel run a zero-side-effect, local aggregate review. It checks:

1. Final Army capacity: 15 commanders, 45 sub-departments, 450 logical agents and 1,350 derived worker slots.
2. Canonical Jinwoo mission ownership and native control-review availability.
3. The lock that keeps every external adapter disabled.
4. Presence of all five final Batch 03 lanes.
5. The Firecrawl and TruffleHog licence gates.
6. Igris's read-only workspace boundary.
7. Local audit-store availability.

The endpoint may append a single aggregate `control.review_completed` event. It includes no prompt, memory content, workspace path, URL, key or scanner finding; it cannot change an adapter's state.

## Reliability and boundary fixes included in this batch

- Whitespace-only chat messages, missions, dry runs, memory writes/updates, research topics and approval actors now fail validation at the API boundary instead of creating empty records or ambiguous approvals.
- Igris file analysis now opens a bounded regular file defensively, uses no-follow/non-blocking flags where the platform supports them, rejects special files, and turns read races/errors into a safe workspace error rather than an unhandled server error. It remains read-only.

## Per-adapter activation requirements

No checkbox below is implicitly satisfied by the contract registry.

| Adapter | Required before any runtime activation |
| --- | --- |
| Mem0 | Confirm the user's intended “memo API”; design item-by-item renewed consent, local deletion/export parity, provider/embedding disclosure, retention controls, local/offline test route and redacted audit hand-off. Never make it a memory fallback. |
| OpenClaw | Pin/review the release and third-party notices; use a disposable local sandbox; deny host credentials, auto-start, channel pairing, skills, cron, shell, browser and network by default; require a Jinwoo approval for every delivery/tool action and log redacted hand-offs. |
| TruffleHog | Obtain a documented AGPL-compatible/legal path first; then use an approved selected workspace, offline/no-verification mode, output/timeout limits, masked findings and explicit scan approval. No Git hosting, cloud, SaaS or credential-validation route by default. |
| Gitleaks | Pin/review the binary/config; use only an approved selected workspace, read-only scan mode, redacted local findings, timeout/size/history limits and explicit scan approval. No CI upload, remote baseline or automatic remediation. |
| Jinwoo Native Control & Audit Review | Keep its invariant tests passing; preserve metadata-only audit events; do not let a review toggle execution, alter policy or substitute for user approval. |

## Final boundary

All three requested batches are now registered as controlled contracts. The next implementation work is **individual activation only after explicit owner approval and review evidence**; there is no fourth automatic batch. In particular, Firecrawl and TruffleHog remain stopped at their AGPL licence gates.
