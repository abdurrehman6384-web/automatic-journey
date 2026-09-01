# Jinwoo AI — Shadow Army Command Center

An original, local-first desktop assistant foundation for the **Jinwoo AI / Shadow Army** concept.

## What is implemented now

- React + TypeScript Army HQ dashboard with all 15 requested commander roles;
- dynamic logical hierarchy: 15 commanders × 3 sub-departments × 10 agent roles × 3 workers;
- responsive Command Center UI with original Shadow Gate/status-orb visuals, expanded navigation, commander directory, Army Explorer, mission console, Interaction Lab, searchable framework registry and provider panel;
- deterministic local/demo mission routing and local-first chat — no API key required to explore either;
- explicit per-message cloud approval before a configured cloud chat provider can be used;
- Python FastAPI backend with typed mission contracts, routing, approval gate and local SQLite memory;
- usable Memory Vault with explicit consent, local view/edit/delete/export controls, and credential/one-time-code rejection;
- redacted local audit trail for mission routing, approvals, completion and Memory Vault changes;
- Igris Workspace Guard: user-selected, read-only folder listing and bounded source diagnostics with path-escape protection;
- provider registry for Ollama, LM Studio, Claude, GLM/Z.ai, Hugging Face and optional Mem0;
- controlled Batch 01–07 adapter/advanced-skill registry: core orchestration, coding, research, memory, security, media, document, connector, browser, MCP, science, interaction and mobile-companion lanes all remain policy-gated and non-executing in V1;
- Batch 07 adds a native, mobile-first Shadow Army Core: 450 logical seats, visible Planner/Executor/Verifier topology maps, zero started external workers, and reviewed pattern references for Ruflo, CrewAI, AutoGen, MetaGPT, LangGraph, Agent Swarm, ROMA, Open Multi-Agent, Awesome Agent Orchestration and Microsoft Agent Framework;
- Batch 05 registers lawful AI-video, defensive-security, document/research, engineering, connector/MCP, browser, multi-agent and science skill contracts; Batch 06 adds gesture/orb and physical-hardware safety-intake contracts plus an original CSS-only command orb; IRIS-AI, IRIS-X, Awesome MCP Servers, 500 AI Agents Projects and Awesome Agent Orchestration remain reference-only, while required licence/source gates stay locked;
- Tank's no-fetch Research Gate for validating explicit public HTTPS source plans without opening a URL, starting a browser or calling a crawler;
- Greed's no-scan secret-review preflight for selected workspaces, with no file/history read, scanner launch or credential disclosure;
- Jinwoo Native Control & Audit Review for zero-side-effect local checks of capacity, disabled runtimes, licence gates, workspace containment and audit availability;
- API validation that rejects whitespace-only user text, plus hardened bounded regular-file reads for Igris workspace diagnostics;
- unit tests for routing, policy, local memory, workspace confinement, framework boundaries, no-fetch research validation and native control review;
- original code only. External source archives are references until their licence and intended merge path are reviewed.

## Security model

Jinwoo makes plans and drafts by default. Actions that may alter files, run a
terminal command, install software, send/upload content or control a desktop
must request explicit approval. The included backend intentionally has no raw
shell execution endpoint, URL-fetch/crawler endpoint, secret-scanner endpoint,
or external automation gateway. The current Igris Workspace Guard is read-only,
uses bounded regular-file reads, and resolves every inspected path beneath the
one folder selected by the user.

## Run the dashboard

```bash
cd jinwoo-ai
npm install
npm run dev
```

The browser dashboard is available at the Vite address shown in the terminal.
It remains functional if the Python API is not yet running.

## Run the local API

```bash
cd jinwoo-ai
python3 -m venv .venv
. .venv/bin/activate                 # Windows: .venv\Scripts\activate
pip install -r backend/requirements.txt
python -m uvicorn app.main:app --app-dir backend --host 0.0.0.0 --port 8787 --reload
```

Then use `npm run dev` in a second terminal. The browser only calls `/api/*`;
Vite proxies that relative route to the local backend in development.

## Test the Python foundation

```bash
cd jinwoo-ai
python3 -m unittest discover -s backend/tests -v
```

## Configuration

Copy `.env.example` to `.env` locally and supply values only for providers you
choose to enable. Do **not** commit keys and do not paste them into chat.

```bash
cp .env.example .env
```

`JINWOO_MODE=demo` is the safe default. It makes no provider requests. Future
settings UI / desktop secure storage will set these values without exposing them
to the browser.

## Local provider priority

1. **Ollama** — recommended first local model route.
2. **LM Studio** — optional local OpenAI-compatible endpoint.
3. **Claude / GLM / Hugging Face** — optional cloud adapters after local secure
   configuration.
4. **Mem0** — separately consented optional memory-interoperability lane; SQLite is always the local source of truth. The earlier ambiguous “memo API” is not assumed to mean Mem0.

## Orchestration integrations

`/api/frameworks` reports the controlled integration boundary. Batch 01 contains
Swarms, Agency-Swarm, Ruflo, LangGraph and CrewAI; Batch 02 contains AG2,
OpenHands, Firecrawl, Firecrawl Web-Agent and Crawl4AI; Batch 03 contains Mem0,
OpenClaw, TruffleHog, Gitleaks and Jinwoo Native Control & Audit Review; Batch 04
contains the owner-requested advanced-skill lanes Goose, Orkas, Bytebot,
OpenDesktop, Hermes Agent, OpenAgent, IRIS-GO, IRIS-Mini, IRIS-Zero, Zoey and the
reference-only IRIS-AI / IRIS-X records. Batch 05 contains lawful media,
defensive-security, document/research, engineering, connector/MCP, browser,
science and mobile-companion skill lanes. Batch 06 adds the licence-gated
Barehands gesture-interface contract, the MIT Ultron Orb UI design contract,
and a source-gated physical cutter/robotics safety intake. Batch 07 adds Agent
Swarm, ROMA, Open Multi-Agent, Awesome Agent Orchestration and Microsoft Agent
Framework as controlled records, plus the native Shadow Army planning API:
`GET /api/shadow-army/overview`, `GET /api/shadow-army/plans`, and
`POST /api/shadow-army/plans`. A Shadow Army plan is a bounded visual topology:
it starts no worker or external framework runtime. See
[`docs/INTEGRATION_BATCH_05.md`](docs/INTEGRATION_BATCH_05.md),
[`docs/INTEGRATION_BATCH_06.md`](docs/INTEGRATION_BATCH_06.md), and
[`docs/INTEGRATION_BATCH_07.md`](docs/INTEGRATION_BATCH_07.md) for source
matrices and activation boundaries. External adapters can prepare a bounded,
policy-screened dry run through `POST /api/frameworks/{id}/dry-run`, but no
upstream runtime is invoked or enabled in V1.

`POST /api/control/review` runs the native control lane: a zero-side-effect local
control check that cannot enable a runtime, scan files or modify policy.
`POST /api/security/scan-plan` requires a selected workspace and explicit
authorisation, but creates only a no-scan preflight — it cannot read files or
Git history, invoke a scanner, verify a credential or expose a finding.

For web research lanes, `POST /api/research/plan` only validates a user-visible,
no-fetch plan: it does not resolve DNS, open a URL, launch a browser or call a
crawler. It accepts only public HTTPS domain targets and requires a separate
approved retrieval implementation later. Firecrawl and TruffleHog are explicitly
blocked from activation pending AGPL-3.0 compatibility decisions. IRIS-GO,
IRIS-Mini and IRIS-Zero are blocked pending their individual licence decisions;
Bytebot is marked archived-upstream; IRIS-AI and IRIS-X are reference-only.
Batch 05 also locks Anthropic Skills, WordPress Agent Skill Prototypes and
Official MCP Servers pending individual licence/component review; it leaves
Open-AutoGLM queued for a separate Android phase and EnvAgent pending an exact
source URL. Batch 06 locks Barehands pending an AGPL-3.0 compatibility decision
and keeps all camera, gesture, Android and physical-device paths disabled;
physical cutter/robotics input needs exact machine and safety evidence. See
[`docs/INTEGRATION_BATCH_01.md`](docs/INTEGRATION_BATCH_01.md),
[`docs/INTEGRATION_BATCH_02.md`](docs/INTEGRATION_BATCH_02.md),
[`docs/INTEGRATION_BATCH_03.md`](docs/INTEGRATION_BATCH_03.md),
[`docs/INTEGRATION_BATCH_04.md`](docs/INTEGRATION_BATCH_04.md),
[`docs/INTEGRATION_BATCH_05.md`](docs/INTEGRATION_BATCH_05.md),
[`docs/INTEGRATION_BATCH_06.md`](docs/INTEGRATION_BATCH_06.md),
[`docs/INTEGRATION_BATCH_07.md`](docs/INTEGRATION_BATCH_07.md), and
[`docs/FRAMEWORK_ADAPTERS.md`](docs/FRAMEWORK_ADAPTERS.md) before enabling any
adapter.

## Desktop packaging

The repository includes an Electron shell foundation in `desktop/main.cjs`.
Packaging remains a Phase C task: it will wrap the stable local dashboard and
API after source intake, packaging configuration, and release checks are
approved.

## Imported source intake

The current workspace includes `../project.zip`. Batch 07 selectively reviewed
**only that archive**, then clean-room reimplemented safe planning/UI concepts;
no archive source, dependency, executable, credential/configuration, model,
provider, tool, browser/device, hardware, autopilot or security-offense path was
copied or activated. See [`docs/INTEGRATION_BATCH_07.md`](docs/INTEGRATION_BATCH_07.md)
for the archive hash, intake boundary and static regression guard.

For a future source intake, provide one source-only ZIP or a GitHub repository
with its exact licence and version. Exclude `node_modules`, `.next`, `dist`,
`build`, `.git`, binaries/caches, captured data and real `.env` files. Every
source remains a non-executing reference until its licence, intended merge path,
dependencies and safety controls have been individually reviewed.
