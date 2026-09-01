# Jinwoo AI — Shadow Army Command Center

An original, local-first desktop assistant foundation for the **Jinwoo AI / Shadow Army** concept.

## What is implemented now

- React + TypeScript Army HQ dashboard with all 15 requested commander roles;
- dynamic logical hierarchy: 15 commanders × 3 sub-departments × 10 agent roles × 3 workers;
- responsive Shadow Gate UI, commander directory, mission console and provider panel;
- deterministic local/demo mission routing and local-first chat — no API key required to explore either;
- explicit per-message cloud approval before a configured cloud chat provider can be used;
- Python FastAPI backend with typed mission contracts, routing, approval gate and local SQLite memory;
- usable Memory Vault with explicit consent, local view/edit/delete/export controls, and credential/one-time-code rejection;
- redacted local audit trail for mission routing, approvals, completion and Memory Vault changes;
- Igris Workspace Guard: user-selected, read-only folder listing and bounded source diagnostics with path-escape protection;
- provider registry for Ollama, LM Studio, Claude, GLM/Z.ai, Hugging Face and optional Mem0;
- controlled Batch 01–04 adapter/advanced-skill registry for Swarms, Agency-Swarm, Ruflo, LangGraph, CrewAI, AG2, OpenHands, Firecrawl, Firecrawl Web-Agent, Crawl4AI, Mem0, OpenClaw, TruffleHog, Gitleaks, Goose, Orkas, Bytebot, OpenDesktop, Hermes Agent, OpenAgent, IRIS-GO, IRIS-Mini, IRIS-Zero and Zoey; every external lane is policy-gated and cannot execute an upstream runtime in V1;
- IRIS-AI and IRIS-X are registered as reference-only advanced-skill sources; their proprietary cores are not copied, linked, installed or invoked;
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
python -m uvicorn app.main:app --app-dir backend --host 127.0.0.1 --port 8787 --reload
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
reference-only IRIS-AI / IRIS-X records. External adapters can prepare a bounded,
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
See [`docs/INTEGRATION_BATCH_01.md`](docs/INTEGRATION_BATCH_01.md),
[`docs/INTEGRATION_BATCH_02.md`](docs/INTEGRATION_BATCH_02.md),
[`docs/INTEGRATION_BATCH_03.md`](docs/INTEGRATION_BATCH_03.md),
[`docs/INTEGRATION_BATCH_04.md`](docs/INTEGRATION_BATCH_04.md), and
[`docs/FRAMEWORK_ADAPTERS.md`](docs/FRAMEWORK_ADAPTERS.md) before enabling any
adapter.

## Desktop packaging

The repository includes an Electron shell foundation in `desktop/main.cjs`.
Packaging remains a Phase C task: it will wrap the stable local dashboard and
API after source intake, packaging configuration, and release checks are
approved.

## Imported source intake

The Dropbox links provided refer to a large custom workspace plus public-style
reference archives. The terminal environment cannot retrieve Dropbox binary
files directly. Attach a source-only ZIP in the chat or provide a GitHub repo
for exact code integration. Exclude `node_modules`, `.next`, `dist`, `build`,
`.git` and real `.env` files.
