# Controlled Integration Batch 07 — Shadow Army Multi-Agent Core

**Status:** implemented as a native, clean-room, Python-first planning core.
The requested multi-agent sources are represented as **reviewed pattern records**,
not installed libraries or executing agents. The new mobile-first **Army Core**
view makes the command topology, framework references, Planner → Executor →
Verifier stages, approval edges and runtime boundary visible.

This batch preserves the authoritative hierarchy:

```text
Jinwoo → Bellion → 15 commanders → 3 divisions each → 10 logical seats each
       → Planner → Executor → Verifier → Jinwoo delivery
```

That is **15 commanders × 3 divisions × 10 logical agents = 450 logical
seats**, and **1,350 logical Planner/Executor/Verifier worker slots**. These are
deterministic catalogue values—not processes, threads, model sessions, tools or
external-framework workers. A single plan reserves from one to 450 logical seats,
shows at most ten representative seats for a mobile-readable result, starts zero
workers, and can propose no more than three runtime roles.

## What is actually implemented

| Surface | Local implementation | Safety result |
| --- | --- | --- |
| Native planning core | `backend/app/shadow_army.py` | Deterministic topology builder and in-memory, audit-backed plan list; no package import or runtime delegation |
| Typed API contracts | `backend/app/schemas.py` | Bounded prompt/scope/pattern request and structured plan/overview responses |
| HTTP API | `backend/app/main.py` | `GET /api/shadow-army/overview`, `GET /api/shadow-army/plans`, and `POST /api/shadow-army/plans` |
| Mobile dashboard | `src/components/ShadowArmyCore.tsx` | Visible capacity, hierarchy, mission-map form, plan graph, specialists, framework states and guardrails |
| Registry/control lane | `backend/app/frameworks.py`, `backend/app/control.py` | Five new Batch 07 contracts; zero external runtime enabled; ROMA and catalogue restrictions remain checked |
| Regression checks | `backend/tests/`, `scripts/check_safe_intake.py` | API/core boundary tests plus a static clean-room import/secret guard |

The plan API classifies blocked requests before storing them and rejects detected
credentials or one-time codes. Its audit entry records only aggregate routing and
capacity metadata—not the raw mission prompt, source content, credentials or
external URLs.

## Reviewed multi-agent source matrix

Repository metadata, licence evidence and publicly documented capabilities were
reviewed on **2026-09-02**. The commit values are review observations, **not**
installed pins. No upstream package, source file, asset, CLI, service, model,
tool, browser bridge or runtime has been copied, installed, imported or started.

| Source / Jinwoo ID | Review commit | Licence outcome | Pattern retained locally | Batch state |
| --- | --- | --- | --- | --- |
| [Ruflo](https://github.com/ruvnet/ruflo) / `ruflo` | `29f048fc3b556f857cf2b126d2a84c19d2daa0d0` | MIT | Swarm, coordination and memory-harness boundary | Existing contract-ready; disabled |
| [CrewAI](https://github.com/crewAIInc/crewAI) / `crewai` | `818f2624e84768cc0171e946955a56d35720ed11` | MIT | Role/crew hierarchy | Existing contract-ready; disabled |
| [Microsoft AutoGen](https://github.com/microsoft/autogen) / `autogen` | `027ecf0a379bcc1d09956d46d12d44a3ad9cee14` | MIT code (`LICENSE-CODE`); CC-BY-4.0 docs | Typed handoff / bounded council | Existing contract-ready; disabled |
| [MetaGPT](https://github.com/geekan/MetaGPT) / `metagpt` | `11cdf466d042…` | MIT | SOP-oriented delivery concept | Existing contract-ready; disabled |
| [LangGraph](https://github.com/langchain-ai/langgraph) / `langgraph` | `11ee185999b86bfea2d8c0e69cef9a5e37acf686` | MIT | State graph, checkpoint and approval edge | Existing contract-ready; disabled |
| [Agent Swarm](https://github.com/jlulxy/agent-swarm) / `agent-swarm` | `e36e21107db7…` | MIT | Deliverable-driven specialist collaboration | Batch 07 contract-ready; disabled |
| [ROMA](https://github.com/sentient-agi/ROMA) / `roma` | `a6e3bb4f9e06…` | **Unverified; no repository licence found** | Recursive task-tree concept | Batch 07 **licence review required**; disabled |
| [Open Multi-Agent](https://github.com/open-multi-agent/open-multi-agent) / `open-multi-agent` | `6eece1d5eeb2…` | MIT | Dynamic DAG, budget/recovery/governance concept | Batch 07 contract-ready; disabled |
| [Awesome Agent Orchestration](https://github.com/vivy-yi/awesome-agent-orchestration) / `awesome-agent-orchestration` | `a1de47d37199…` | **NOASSERTION** | Discovery/comparison only | Batch 07 **reference-only**; disabled |
| [Microsoft Agent Framework](https://github.com/microsoft/agent-framework) / `microsoft-agent-framework` | `baf0ea5252eb3faa232b811c1c4d95771afd10ed` | MIT | Workflow, middleware and human-in-loop concept | Batch 07 contract-ready; disabled |

`metagpt` is present in the registry as an existing Batch 05 controlled record
and is used only as a declarative SOP-oriented reference in the hierarchical
native planning mode. It is not imported or run.

### Native coordination modes

| Mode | Native result | Declarative framework references |
| --- | --- | --- |
| `hierarchical` | Jinwoo → Bellion → Commander → Division → Planner/Executor/Verifier | CrewAI, MetaGPT, Ruflo, Microsoft Agent Framework |
| `commander-council` | Small advisory viewpoints with one Bellion decision route | AutoGen, Microsoft Agent Framework, Agent Swarm |
| `dependency-graph` | Visible ordered hand-offs and approval edges | LangGraph, Open Multi-Agent, Microsoft Agent Framework |
| `bounded-swarm` | Logical specialists only; no hidden expansion | Ruflo, Agent Swarm, ROMA |

A reference only describes an architecture pattern. It does **not** activate a
provider, model, tool, file action, network call, database, memory adapter,
workflow engine, MCP server, CLI, worker, child process, or external service.

## `project.zip` selective intake record

The owner asked to extract **only** `/home/user/automatic-journey/project.zip`.
No other archive in the repository was opened or used for this batch.

| Item | Evidence |
| --- | --- |
| Archive | `/home/user/automatic-journey/project.zip` |
| SHA-256 | `436e9f7dfd62137f77044e2f654f224dcba212407a38736229f94d2ea83c7ef4` |
| Archive listing | 3,170 entries; approximately 46.7 MB uncompressed |
| Intake approach | Quarantined review and selective clean-room reimplementation only |
| Code copied from archive | **None** |
| New runtime dependency from archive | **None** |
| Source payload committed into `jinwoo-ai` | **None** |

The archive contains a heterogeneous personal-assistant/workspace payload,
including nested/reference source trees, configuration examples, generated and
captured media/data, histories/logs, executables and cache-like material. It also
contains direct external/provider, command/subprocess, browser/desktop/input,
file/persistence, automation/autopilot, cross-device and hardware paths. Those
paths are inappropriate for an automatic merge into Jinwoo’s V1 safety model.

Useful **concepts**, reimplemented independently, were limited to:

1. a visible agent/role registry and status-oriented command surface;
2. bounded planner/executor/verifier hand-offs;
3. queue/topology visibility rather than hidden autonomous expansion; and
4. explicit approval/audit framing for potentially impactful work.

Excluded material includes source files and nested repositories; `.env` or
credential-like configuration; captured/generated media; logs/history/data;
binaries/caches; installer and build scripts; provider/network wrappers;
browser, desktop, keyboard/mouse, screen/camera, device and hardware controls;
subprocess/terminal execution; autonomous loops; upload/send/delete paths; and
security-offense or bypass-related routes. The CapCut patcher path remains
excluded and its supplied password was not used.

## Static clean-room check

Run the lightweight guard from `jinwoo-ai`:

```bash
PYTHONPATH=. python3 scripts/check_safe_intake.py
```

The guard deliberately inspects the Batch 07 clean-room implementation and the
Batch 07/08 dependency manifests:

- `backend/app/shadow_army.py`
- `src/components/ShadowArmyCore.tsx`
- `backend/requirements.txt`
- `package.json`

It rejects direct imports/dependencies for the selected external frameworks and
God's Eye View's reviewed geospatial runtime packages, embedded secret-like
literals, direct capability entry tokens such as subprocess, `os.system`, browser
automation, camera/media access and common computer-control libraries, and a
copied `project.zip` inside the Jinwoo source tree. It reports only rule/location
identifiers, not matching source text. The same guard is run by the backend unit
suite.

This is a narrow regression control, not a claim that static scanning alone can
prove a repository safe. It complements manual licence/source review, typed
contracts, API policy enforcement, explicit approval and audit review.

## Activation gates remain mandatory

An external framework or any archive-originated capability may move beyond its
current contract only after **all** applicable conditions are satisfied:

1. exact source and version are pinned and licence/NOTICE compatibility is
   resolved; ROMA and Awesome Agent Orchestration cannot bypass their current
   licence/reference restrictions;
2. a minimal adapter is independently reviewed, with no source copy by default;
3. its dependencies, model/provider paths, persistence, telemetry and network
   behaviour are documented and sandboxed;
4. its tool permissions are narrow, disabled by default and visible to the user;
5. file modifications, terminal commands, sends/uploads/deletes, browser/device
   actions and model downloads each require their own explicit approval flow;
6. V1 actions remain confined to a selected workspace folder and are audited
   with redaction; and
7. local/offline tests, stop/timeout controls, a disable path and a security
   review pass before enabling anything.

## Validation commands

```bash
cd jinwoo-ai
PYTHONPATH=backend .venv/bin/python -m unittest discover -s backend/tests -v
npm run typecheck
npm run build
PYTHONPATH=. .venv/bin/python scripts/check_safe_intake.py
```

## Final boundary

Batch 07 is a **native planning and presentation layer**, not an uncontrolled
swarm runner. It uses no external multi-agent runtime. It does not download a
model, invoke a tool, call a provider, open a URL, start a browser, launch a
shell, read/write user workspace files, upload/send/delete content, access a
camera/device/hardware interface, or start a background worker.
