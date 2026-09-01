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
| Standard | Ollama or LM Studio plus local LanceDB/Chroma document retrieval |
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
and IRIS-X records. They can prepare bounded, policy-screened plans, but the
backend will not install or execute an upstream runtime. OpenHands has no
container/sandbox path; OpenClaw has no gateway/channel/skill path; Batch 04
computer-use lanes have no container, screen, input, voice, vision, browser or
shell path; secret scanners have no file or Git-history scan path. Firecrawl,
TruffleHog, IRIS-GO, IRIS-Mini and IRIS-Zero are
`license-review-required`; Bytebot is archived-upstream; IRIS-AI and IRIS-X are
reference-only. Any future adapter must return proposed work through Jinwoo's
policy, approval, workspace and audit boundaries. See
[`FRAMEWORK_ADAPTERS.md`](FRAMEWORK_ADAPTERS.md),
[`INTEGRATION_BATCH_01.md`](INTEGRATION_BATCH_01.md),
[`INTEGRATION_BATCH_02.md`](INTEGRATION_BATCH_02.md),
[`INTEGRATION_BATCH_03.md`](INTEGRATION_BATCH_03.md), and
[`INTEGRATION_BATCH_04.md`](INTEGRATION_BATCH_04.md).

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
Batch 03/04 inventory, restricted source/licence gates, read-only workspace
status and local audit availability. It cannot enable a runtime or read
workspace data; its audit entry contains aggregate metadata only.

## Why Rust and Go are not initial services

Python is the main orchestrator. Rust and Go are excellent later sidecars for a
measured hot path — e.g. high-speed indexing or a bounded concurrent service —
but adding them before profiling would create extra IPC, packaging and debugging
cost without making missions better.

## Workspace guard

Igris can perform bounded, read-only diagnostics only after the user selects a
project folder in Settings. The guard canonicalises the root and every requested
child path, rejects path escapes and outside-root symlinks, lists at most 200
entries, and only analyses common regular text/source files up to 500 KB. It
uses no-follow/non-blocking reads where supported and returns a safe error for
special files or read races. It has no write, delete, terminal or package-install
capability.

## Memory

SQLite is the durable, local source of truth. Vector retrieval can use LanceDB
or ChromaDB later. Mem0 is a separately reviewed optional integration lane; the
owner has not yet confirmed that their earlier ambiguous "memo API" means Mem0.
Even if confirmed later, it must be opt-in per operation and never replace the
user's ability to inspect, edit, delete and export local data.
