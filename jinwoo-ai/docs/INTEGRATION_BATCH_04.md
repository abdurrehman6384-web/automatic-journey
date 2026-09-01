# Controlled Integration Batch 04 — Advanced Skill Lanes

**Status:** the owner-requested advanced-skill catalogue is registered as
non-executing, source-reviewed capability contracts. No Batch 04 upstream
source, package, binary, Docker image, desktop client, CLI, browser controller,
voice/vision service, mobile runtime, model, provider, plugin, MCP server or
agent loop is copied, installed, started or invoked by Jinwoo.

Jinwoo Native remains the one canonical mission engine. It owns routing,
Planner → Executor → Verifier roles, policy classification, approval cards,
workspace confinement, memory consent and redacted local audit records. Batch
04 entries can prepare a bounded review plan only; they cannot bypass those
boundaries.

## Reviewed upstream references

The following GitHub repository metadata, root tree and available licence files
were reviewed on **2026-09-02**. Observed commits are review references only,
not installed dependency pins and not a commitment to redistribute upstream
code.

| Adapter ID | Project | Upstream source | Observed HEAD | Licence result | Jinwoo owner | Contract state |
| --- | --- | --- | --- | --- | --- | --- |
| `goose` | Goose | <https://github.com/block/goose> | `7259c05174d25b67f218b6d9ee5f6992c89c0835` | Apache-2.0 | Igris | Contract-ready, execution disabled |
| `orkas` | Orkas | <https://github.com/Orkas-AI/Orkas> | `1fd5a73b6ffbd9e9b3946b8d19a1c73157e2ade6` | MIT | Bellion | Contract-ready, execution disabled |
| `bytebot` | Bytebot | <https://github.com/bytebot-ai/bytebot> | `3d37894ce07ef8d8b40adc7fd309ad96c2a71313` | Apache-2.0 | Nox | **Archived upstream; execution disabled** |
| `open-desktop` | OpenDesktop | <https://github.com/Atum246/OpenDesktop> | `157b792b6360ffef159748ffa2557dba0cb013f9` | MIT | Nox | Contract-ready, execution disabled |
| `hermes-agent` | Hermes Agent | <https://github.com/NousResearch/hermes-agent> | `375ce8eee51b9d76714cb6fd1f200c4c9ef83c4a` | MIT | Igris | Contract-ready, execution disabled |
| `openagent` | OpenAgent | <https://github.com/the-open-agent/openagent> | `45c53053eccf4d82f4e22a718ae87edc82fbff66` | Apache-2.0 | Fang | Contract-ready, execution disabled |
| `iris-go` | IRIS-GO | <https://github.com/IRISX-AI/IRIS-GO> | `0f79e213c5348a2820351379b273cae0c43d4e8d` | **Unverified:** README claims MIT but the reviewed root tree has no `LICENSE` file | Bellion | **Licence review required; execution disabled** |
| `iris-mini` | IRIS-Mini | <https://github.com/IRISX-AI/IRIS-Mini> | `8fc89ff05cc914e838a5a41d476e1a70d3115f10` | **Custom restrictive:** Apache-form text includes a personal/educational-only commercial ban; not SPDX Apache-2.0 | Igris | **Licence review required; execution disabled** |
| `iris-zero` | IRIS-Zero | <https://github.com/IRISX-AI/IRIS-Zero> | `c52db94ea679a331b0d7005bd1aecd09fc01552e` | **Unverified:** README claims MIT but the reviewed root tree has no `LICENSE` file | Nox | **Licence review required; execution disabled** |
| `zoey` | Zoey | <https://github.com/Agent-Zoey/Zoey> | `ddd3a8c80d2876708dfc98cb9a7aafdad104e0cb` | MIT | Ashborn | Contract-ready, execution disabled |
| `iris-ai` | IRIS-AI | <https://github.com/IRISX-AI/IRIS-AI> | `5b37fb7489108870c09c37f26ad7d9af6a34e862` | Custom source-available agreement; proprietary core excluded | Ashborn | **Reference only; source/runtime use prohibited** |
| `iris-x` | IRIS-X | <https://github.com/IRISX-AI/IRIS-X> | `5402b68dfca2e9219e7b2752d91fc9a359a303b6` | Dual licence: public UI shell MIT; proprietary engine and commercial features restricted | Ashborn | **Reference only; source/runtime use prohibited** |

### Licence and source-use decisions

- **IRIS-GO and IRIS-Zero:** a README badge or statement is not enough for
  source inclusion. Both remain `license-review-required` until a valid,
  repository-available licence and intended deployment/distribution terms are
  verified.
- **IRIS-Mini:** adding a commercial-use ban to Apache-form licence text means
  it must not be represented as Apache-2.0. It remains
  `license-review-required` until the project owner records a compatible-use
  decision.
- **IRIS-AI and IRIS-X:** the owner supplied these as proprietary-core
  references. They are intentionally `reference-only`: no source copying,
  linking, bundling, installation or runtime integration is allowed. Jinwoo may
  independently implement a feature based only on high-level public product
  observations after a separate design review.
- **Bytebot:** its upstream repository is archived. Its Apache-2.0 licence does
  not make it a supported runtime. A later adoption would need a maintained
  source, security, licence and support review first.

## Advanced capability map

| Lane | Reserved future capability | Current safe capability | Boundary |
| --- | --- | --- | --- |
| Goose | Coding-agent, MCP/ACP and evaluation workflows | Sandboxed code/task plan only | No CLI, tool, edit, test, install or provider call |
| Orkas | Desktop team routing, reflection and skill crystallisation | Architecture/skill-boundary review | No independent queue, agent team, memory store, provider or MCP tool |
| Bytebot | Isolated container-desktop computer use | Container/action-transcript design | No Docker launch, host mount, desktop input, browser profile or credentials |
| OpenDesktop | Desktop computer use, voice and vision | Exact-action/permission plan | No screen, mic, camera, clipboard or input capture; no desktop action |
| Hermes Agent | Agent skills, local state, MCP and coding workflows | Skill/state/MCP boundary review | No skill, plugin, gateway, cron, MCP or provider activation |
| OpenAgent | RAG, tool routing and assistant patterns | RAG/service-contract review | No service, auth, browser, computer-use, shell or media capability |
| IRIS-GO | Local multi-agent workflow/dashboard concepts | Licence-gated capability review | No source reuse, system workflow, remote control, CLI or mobile action |
| IRIS-Mini | CLI developer workflow concepts | Licence-gated UX/action review | No source reuse, terminal or filesystem action |
| IRIS-Zero | Local terminal, voice and project automation concepts | Licence-gated capability review | No source reuse, command, voice capture, model download or automation |
| Zoey | Privacy-first Rust local-agent patterns | Sandboxed framework/capability review | No binary, service, voice route or provider activation |
| IRIS-AI | Desktop voice, memory, vision and workflow UX | High-level public UX reference only | Proprietary/source-available runtime is out of scope |
| IRIS-X | Future mobile-companion, voice and visual-context UX | High-level public UX reference only | Proprietary engine and commercial-only functionality are out of scope |

## What is implemented locally

- `GET /api/frameworks` now exposes all 12 Batch 04 records with their owner,
  source URL, observed licence state, capability tags, runtime shape, safety
  boundary and non-executing state.
- The Settings **Framework boundaries** panel displays the advanced-skill tags
  and clearly distinguishes `license-review-required`, `archived-upstream` and
  `reference-only` records.
- `POST /api/frameworks/{framework_id}/dry-run` supports safe, bounded plans
  for the Batch 04 records. It accepts 1–450 logical agent requests but returns
  no more than Planner, Executor and Verifier (three runtime workers).
  `external_runtime_invoked` is always `false`.
- A reference-only dry run is explicitly a capability-boundary review. It says
  that no upstream source, proprietary core, runtime or tool may be used.
- Jinwoo Native Control & Audit Review now verifies the complete Batch 04
  inventory and its source gates in addition to the existing capacity,
  native-ownership, external-runtime-lock, workspace and audit checks.

## Computer-use and execution hard boundary

Goose, Bytebot, OpenDesktop, Hermes Agent, OpenAgent, IRIS-Mini and IRIS-Zero
contain or describe capabilities that can edit, execute, control a desktop,
capture context, schedule work, access a browser or invoke tools. Their presence
in this registry grants **none** of that power.

Before any single computer-use or execution capability could be activated, all
of these must be separately implemented and approved:

1. Exact upstream commit/release, dependency graph, licence and NOTICE review.
2. A narrow Jinwoo adapter with typed input/output; never a raw upstream tool
   bridge or direct UI-to-agent path.
3. Disposable local sandbox/container, with no host home directory, credential
   store, browser profile, clipboard, microphone, camera, devices or network
   access by default.
4. User-selected Workspace Guard root only, read-only by default, with no path
   escape, symlink escape, automatic Git action or model download.
5. A visible action preview and **separate approval per impactful step**:
   terminal command, edit, test, install, file move/delete, pointer/keyboard
   input, capture, network request, upload, send, publish or schedule.
6. Explicit cloud/provider consent for every outbound request; no secret in
   prompts, logs, screenshots, URLs or audit events.
7. Local redacted audit records, timeout/concurrency/output limits, a hard stop
   control, rollback/cleanup plan and offline failure tests.

## Per-lane activation prerequisites

| Lane group | Extra evidence required before any activation |
| --- | --- |
| Goose / Hermes Agent / IRIS-Mini / IRIS-Zero | Disposable coding/CLI sandbox, command preview, filesystem confinement, no implicit install/provider/tool route, and regression tests for denial paths |
| Orkas / IRIS-GO / Zoey | Proof that Jinwoo remains the only mission state machine, queue, memory owner and policy/approval gateway; no autonomous background worker or self-evolving skill persistence |
| Bytebot / OpenDesktop | Isolated computer-use design, host-input/capture denial by default, visible per-step transcript, exact approval model and no host credential/browser-profile mount |
| OpenAgent | Separate RAG retention/consent design, service authentication review, MCP/tool allowlist and web/computer-use hard disable until their individual gates pass |
| IRIS-GO / IRIS-Mini / IRIS-Zero | Resolve the licence evidence/compatibility decision before source inclusion, binary/container use or runtime work |
| Bytebot | Identify a maintained source/fork and complete security/support review before even a sandboxed runtime proposal |
| IRIS-AI / IRIS-X | Remain reference-only unless the project owner later approves a new, documented source-compatibility decision; proprietary cores stay excluded |

## Continuing boundary

Batch 04 remains a controlled capability catalogue. The subsequently
owner-requested Batch 05 specialist-skill catalogue is documented in
[`INTEGRATION_BATCH_05.md`](INTEGRATION_BATCH_05.md) and remains non-executing.
No integration is activated merely because it appears in the UI or has a safe
dry-run plan. Jinwoo continues to be local-first, approval-gated,
workspace-confined and auditable.
