# Local-first stack decisions

## Default path

The first runnable profile intentionally stays small:

```text
React/Vite UI → relative /api route → FastAPI → SQLite
                                └→ demo provider / optional local Ollama
```

This works without Docker, PostgreSQL, Redis, GPU hardware or cloud API keys.

## Optional profiles

| Profile | Add only when needed |
|---|---|
| Standard | Ollama or LM Studio plus a separately reviewed local retrieval implementation (for example, LanceDB/Chroma) |
| Power | PostgreSQL, Redis and vLLM on a suitable GPU/Linux system |
| Observability | Prometheus and Grafana containers |
| Cloud hybrid | Claude, GLM or Hugging Face enabled from secure local settings |

## Multi-agent framework boundary

Jinwoo's native mission engine is the single canonical orchestrator in V1.
Batch 01 registers Swarms, Agency-Swarm, Ruflo, LangGraph and CrewAI. Batch 02
registers AG2, OpenHands, Firecrawl, Firecrawl Web-Agent and Crawl4AI. Batch 03
registers Mem0, OpenClaw, TruffleHog, Gitleaks and the native control/audit
review. Batch 04 registers Goose, Orkas, Bytebot, OpenDesktop, Hermes Agent,
OpenAgent, IRIS-GO, IRIS-Mini, IRIS-Zero and Zoey, plus reference-only IRIS-AI
and IRIS-X records. Batch 05 registers lawful media, defensive-security,
document/research, coding, connector/MCP, browser, multi-agent, science,
Android and source-intake lanes. Batch 06 registers Barehands, Ultron Orb UI
and a physical cutter/robotics safety intake. Batch 07 adds Agent Swarm, ROMA,
Open Multi-Agent, Awesome Agent Orchestration and Microsoft Agent Framework,
plus a native non-executing Shadow Army topology planner. Batch 08 registers
God's Eye View as a licence/data/asset-gated, non-live geospatial safety intake.
Batch 09 records NEXA AI Assistant as a source-review-required desktop-assistant
intake and independently adds only a bounded native filename locator inside the
selected workspace. Batch 10 records Jarvis One-Click Setup and Control PC Using
Hand Gesture as source-gated desktop/gesture intakes and adds only their original
locked-state status UX to Interaction Lab. Batch 11 adds a ranked, original
status catalogue for requested skill collections; their reported counts do not
add agents and their payloads are not loaded. Batch 12 adds a separate finite,
revision-pinned metadata review queue for ten possible future upgrade lanes; it
runs no unattended discovery process and retrieves no source content. Batch 13
adds 15 Jinwoo-authored, planning-only portable skills and a canonical Master
Orchestrator that can select or control visible local plan state but cannot
start a worker or external runtime. They can prepare bounded,
policy-screened plans, but the backend will not install
or execute an upstream runtime. OpenHands has no container/sandbox path; OpenClaw
has no gateway/channel/skill path; Batch 04/05/06 computer-use lanes have no
container, device, screen, camera, input, voice, vision, browser, CDN,
local-service or shell path; the Batch 08 geospatial lane has no globe, live
feed, map, camera, location, tracking, voice or provider path; the Batch 09
NEXA intake has no upstream source/configuration/model, voice, screen, camera,
vision, browser, OS/window, input, device, messaging, media or automation path;
the Batch 10 Jarvis/hand-gesture lanes have no installer, provider, voice,
external-tool, camera, hand model/data, pointer, keyboard, desktop or device
path; the Batch 11 source catalogue has no third-party skill-file loader,
installer, local skills-path reader, agent process, provider, browser, GitHub,
cloud, model or self-upgrade route; the Batch 13 native loader reads only
Jinwoo-authored in-repository planning files and starts no worker/runtime;
Batch 12 candidates have no package, parser, graph/index,
gateway, policy engine, database, evaluator, formatter, scanner, collector,
exporter, network telemetry or background-loop route; secret scanners have no file or Git-history scan path. Firecrawl,
TruffleHog, IRIS-GO, IRIS-Mini, IRIS-Zero, Anthropic Skills, WordPress Agent
Skill Prototypes, Official MCP Servers, Barehands, ROMA and God's Eye View are
`license-review-required`; Bytebot is archived-upstream; IRIS-AI, IRIS-X,
Awesome MCP Servers, 500 AI Agents Projects and Awesome Agent Orchestration are
reference-only; Open-AutoGLM is queued for a separate Android phase; EnvAgent
and physical hardware need exact source/machine evidence; NEXA has an exact
reviewed source URL but no verified licence and must remain source-review-required;
Jarvis lacks a verified root/CLI/Python reuse licence, and the PC hand-gesture
repository lacks a verified licence and exposes a bundled model/camera/pointer
surface. Batch 11 aggregates named catalogue records only; `NOASSERTION`
sources have no verified reuse grant, and even MIT/Apache metadata remains
subtree/dependency/prompt/asset review-gated. Any future adapter
must return proposed work through Jinwoo's policy, approval, workspace and audit
boundaries. See
[`FRAMEWORK_ADAPTERS.md`](FRAMEWORK_ADAPTERS.md),
[`INTEGRATION_BATCH_01.md`](INTEGRATION_BATCH_01.md),
[`INTEGRATION_BATCH_02.md`](INTEGRATION_BATCH_02.md),
[`INTEGRATION_BATCH_03.md`](INTEGRATION_BATCH_03.md),
[`INTEGRATION_BATCH_04.md`](INTEGRATION_BATCH_04.md),
[`INTEGRATION_BATCH_05.md`](INTEGRATION_BATCH_05.md),
[`INTEGRATION_BATCH_06.md`](INTEGRATION_BATCH_06.md),
[`INTEGRATION_BATCH_07.md`](INTEGRATION_BATCH_07.md),
[`INTEGRATION_BATCH_08.md`](INTEGRATION_BATCH_08.md),
[`INTEGRATION_BATCH_09.md`](INTEGRATION_BATCH_09.md),
[`INTEGRATION_BATCH_10.md`](INTEGRATION_BATCH_10.md),
[`INTEGRATION_BATCH_11.md`](INTEGRATION_BATCH_11.md),
[`INTEGRATION_BATCH_12.md`](INTEGRATION_BATCH_12.md), and
[`INTEGRATION_BATCH_13.md`](INTEGRATION_BATCH_13.md).

## Tank research gate

Tank's local Research Gate validates a no-fetch research plan only. It does not
make a network request, resolve DNS, launch a browser or start a crawler. A plan
can contain at most ten explicit public HTTPS domain sources and rejects
literal IPs, localhost, local/internal hostnames, credentials and
credential-like query strings. A future retrieval executor must revalidate the
resolved connection target to prevent SSRF/rebinding, require visible approval,
and enforce source/robots, rate, depth, response-size, domain, citation and
local-retention limits.

## Greed security gate

Greed's `POST /api/security/scan-plan` is a no-scan preflight for Gitleaks or
TruffleHog. It requires an explicit user-selected workspace and authorisation
confirmation, then creates a plan without reading a file, Git history or key,
starting a scanner, verifying a credential, or placing a finding in the audit
trail. A later scan needs separate approval and strict redaction/retention
controls.

## Native control & audit review

The Jinwoo-native lane is a zero-side-effect `POST /api/control/review`
report. It verifies capacity, native ownership, disabled external runtimes,
Batch 03/04/05/06/07/08/09/10/11 inventory, restricted source/licence/review gates,
read-only workspace status and local audit availability. It cannot enable a
runtime or read workspace data; its audit entry contains aggregate metadata only.

## Why Rust and Go are not initial services

Python is the main orchestrator. Rust and Go are excellent later sidecars for a
measured hot path — e.g. high-speed indexing or a bounded concurrent service —
but adding them before profiling would create extra IPC, packaging and debugging
cost without making missions better.

## Workspace guard

Igris can perform bounded, read-only diagnostics only after the user selects a
project folder in Settings. The guard canonicalises the root and every requested
child path, rejects path escapes and excludes discovered symlinks from the
locator, lists at most 200 entries, offers a filename-and-metadata-only recursive
locator bounded to 120 directories, 500 immediate entries per directory and 100
results, and only analyses common regular text/source files up to 500 KB when
the separate diagnostic endpoint is chosen. The locator never
reads file content, opens a file/process or records its search term in audit. It
uses no-follow/non-blocking reads where supported and returns a safe error for
special files or read races. It has no write, delete, terminal or package-install
capability.

## Memory

SQLite is the durable, local source of truth. Vector retrieval can use LanceDB
or ChromaDB later. Mem0 is a separately reviewed optional integration lane; the
owner has not yet confirmed that their earlier ambiguous "memo API" means Mem0.
Even if confirmed later, it must be opt-in per operation and never replace the
user's ability to inspect, edit, delete and export local data.
