# Batch 13 — Native Skill Library & Master Orchestrator

**Status:** implemented as a local, clean-room, planning-only capability library.

## Outcome

Batch 13 turns the useful *categories* discovered in the 20 owner-supplied
repositories into 15 original Jinwoo skills and one original canonical agent
manifest. This is intentionally not a vendor integration, package import, or
repository mirror:

- all production instructions under `skills/**/SKILL.md` are written by Jinwoo;
- `skills/SOURCES.json` contains controlled provenance metadata only;
- no upstream `SKILL.md`, `.agent.md`, code, script, package, asset, model,
  prompt, installer, linked project, local agent folder, or runtime is copied;
- every new native skill is `planning-only` and remains subject to existing
  approval, privacy, workspace, policy, and audit controls.

The resulting library is discoverable by the local API and dashboard, can be
selected deterministically, and can be composed into a visible
Planner → Executor → Verifier plan by the canonical **Jinwoo Master
Orchestrator**. A plan is not a task runner.

## Repository layout

```text
skills/
  SOURCES.json
  README.md
  core/{evidence-before-completion,agent-governance,
        approval-and-permission-boundary,multi-agent-planning}/SKILL.md
  engineering/{architecture-decision-record,dependency-review,
               scope-and-delivery-control,agent-evaluation}/SKILL.md
  catalogs/{catalogue-curation,agent-blueprint-triage}/SKILL.md
  computer-use/consented-computer-use-planning/SKILL.md
  interaction/gesture-and-vision-safety-planning/SKILL.md
  robotics/robotics-software-review/SKILL.md
  models/multimodal-provider-boundary/SKILL.md
  media/lawful-media-prompt-planning/SKILL.md
agents/
  jinwoo-master-orchestrator/AGENT.md
backend/app/
  skill_library.py
  skill_activation.py
  skill_orchestrator.py
```

`skill_library.py` uses a strict local loader. It accepts only regular,
non-symlinked, canonical in-tree `category/<skill-id>/SKILL.md` files with the
Jinwoo frontmatter marker and required Purpose, Procedure, Output, and Safety
boundary sections. It validates all 20 provenance records and their mappings
before returning the inventory. The loader does not recursively consume a user
workspace, home-directory skill folder, source archive, or an upstream URL.

## Native capability set

| Native skill | Main outcome | Important hard boundary |
| --- | --- | --- |
| `evidence-before-completion` | Acceptance criteria and reproducible evidence plan | Does not run tests or claim unrun checks passed. |
| `agent-governance` | Accountability, hand-off, and escalation map | Does not grant tools or override Jinwoo policy. |
| `approval-and-permission-boundary` | Separate drafting from approval-required actions | Cannot self-approve or perform an action. |
| `multi-agent-planning` | Bounded Planner / Executor / Verifier topology | Does not spawn a worker, queue, model, or process. |
| `architecture-decision-record` | Reviewable technical decision draft | Does not change architecture or dependencies. |
| `dependency-review` | No-scan package / licence / rollback review | Does not install, fetch, scan, or alter a manifest. |
| `scope-and-delivery-control` | Thin-slice delivery and non-goal brief | Does not make product or procurement decisions. |
| `agent-evaluation` | Behavior and safety evaluation matrix | Does not invoke a model, benchmark, or target. |
| `catalogue-curation` | Deduplicated, traceable native candidate selection | Does not clone or load a public skill collection. |
| `agent-blueprint-triage` | Small native proposal from broad agent examples | Does not pull linked projects or dependencies. |
| `consented-computer-use-planning` | Previewable future desktop-interaction proposal | No screenshot, OCR, mouse, keyboard, clipboard, or window action. |
| `gesture-and-vision-safety-planning` | Camera-off gesture/vision design and fallback | No webcam, biometric data, pointer, or device access. |
| `robotics-software-review` | Pure-software/simulation review matrix | No ROS runtime, simulator, actuator, controller, or hardware command. |
| `multimodal-provider-boundary` | Provider-neutral media/document data boundary | No SDK, model download, key access, OCR, upload, or provider call. |
| `lawful-media-prompt-planning` | Original rights-aware media brief | No generation, asset upload, render, export, or publication. |

## Controlled source coverage

The authoritative machine-readable record is
[`skills/SOURCES.json`](../skills/SOURCES.json). It stores the requested and,
where applicable, resolved repository identity; observed default-branch
revision; licence signal; bounded review scope; resulting native skill IDs; and
a no-copy decision. It contains no upstream instruction or code payload.

| Reviewed source | Native clean-room capability mapping | Intake conclusion |
| --- | --- | --- |
| `luokai0/ai-agent-skills-by-luo-kai` | catalogue curation; evidence before completion | No verified reuse licence; no source text copied. |
| `sickn33/antigravity-awesome-skills` → resolved `agentic-awesome-skills` | catalogue curation; evidence before completion | MIT root signal has separate content conditions; no collection copied. |
| `mouadja02/skills` | agent governance; multi-agent planning | No verified reuse licence; concepts only. |
| `theneoai/awesome-skills` | scope and delivery control | Attribution-constrained root licence signal; no persona/skill copied. |
| `alirezarezvani/claude-skills` | dependency review | No scanner, plugin, script, or prompt copied. |
| `agent-skills-hub/agent-skills-hub` | multi-agent planning; agent evaluation | No registry, installer, plugin, or payload copied. |
| `VoltAgent/awesome-agent-skills` | catalogue curation | Index only; no downstream item inferred, fetched, or copied. |
| `patrickporto/desktop-agent` | consented computer-use planning | No CLI, screenshot, mouse, or keyboard route. |
| `1m1ai/computer-use` | consented computer-use planning | No verified reuse licence; no screen/input/shell route. |
| `trycua/acu` | consented computer-use planning | Resource index only; no linked project or browser route. |
| `jaredrhod/barehands` | gesture and vision safety planning | AGPL-3.0 source excluded; webcam and service path stay off. |
| `Viral-Doshi/Gesture-Controlled-Virtual-Mouse` | gesture and vision safety planning | GPL-3.0 source excluded; camera/model/pointer path stays off. |
| `arpitg1304/robotics-agent-skills` | robotics software review | No ROS, simulator, certificate, controller, or hardware code. |
| `zai-org/GLM-skills` | multimodal provider boundary | No provider SDK, API key, model, OCR, or media operation. |
| `Stijnman/grok-custom-skills` | evidence; governance; ADR; permission boundary | No `.grok` payload, scheduler, connector, or service. |
| `vasilyu1983/AI-Agents-public` | permission boundary; planning; evaluation | No agent prompt, hook, runtime, provider, or tool implementation. |
| `LeoYeAI/seedance-skills` | lawful media prompt planning | No media asset, provider, prompt payload, upload, or model. |
| `ashishpatel26/500-AI-Agents-Projects` | agent blueprint triage | No linked project, agent code, configuration, or dependency. |
| `Shubhamsaboo/awesome-llm-apps` | blueprint triage; scope; planning | No agent implementation, provider, loop, or payload. |
| `github/awesome-copilot` | governance; ADR; blueprint triage | No `.agent.md`, extension, terminal tool, or workflow. |

A limited, fixed-ref document review was used to identify broad design ideas,
ot to certify every file in an upstream repository. Licence signals do not turn
into reuse permission. Any future direct reuse still needs a component-level
licence review and an explicit approved merge path.

## Master Orchestrator semantics

[`agents/jinwoo-master-orchestrator/AGENT.md`](../agents/jinwoo-master-orchestrator/AGENT.md)
is a native manifest. It is the only canonical controller for this library.
It may:

1. discover relevant native skills;
2. select and combine at most five enabled skills for a plan;
3. assign visible Planner, Executor, and Verifier stages;
4. pause, resume, or terminate the **local plan record**; and
5. revise a session-local controller overlay for that plan.

It may not rewrite a `SKILL.md` file, override a policy classification, grant
itself a tool, approve an impactful action, invoke an external agent, start a
model/provider, launch a process, or access a desktop/device/workspace.

`skill_activation.py` supports per-skill enabled/disabled availability. This is
only an explicit selection filter. “Enabled” means a skill may be chosen for a
planning-only response; it never means that desktop, camera, robotics,
provider, or media functionality has been turned on. Availability lives in the
current local API process and defaults to enabled after restart; its changes are
recorded as redacted local audit metadata.

## Local API

| Method | Route | Meaning |
| --- | --- | --- |
| `GET` | `/api/skills` | Lists native skills, the canonical agent, and the 20 metadata-only source records. |
| `GET` | `/api/skills/{id}` | Returns one locally authored portable `SKILL.md`. |
| `PUT` | `/api/skills/{id}/activation` | Enables/disables planning selection only: `{ "enabled": false }`. |
| `POST` | `/api/skills/resolve` | Deterministically routes an objective to enabled native skills; no model call. |
| `GET` | `/api/agents/jinwoo-master-orchestrator` | Returns the canonical native agent manifest metadata. |
| `GET` | `/api/skill-orchestrator/plans` | Lists visible in-process plan records. |
| `POST` | `/api/skill-orchestrator/plans` | Creates a plan; no worker or external runtime is started. |
| `PATCH` | `/api/skill-orchestrator/plans/{id}` | Accepts `pause`, `resume`, `terminate`, or `rewrite-instructions` for plan state only. |

Example local plan request:

```json
{
  "objective": "Prepare a privacy-aware desktop interaction proposal.",
  "skill_ids": [
    "consented-computer-use-planning",
    "approval-and-permission-boundary"
  ],
  "controller_instruction": "Keep the proposal text-only and include an emergency stop."
}
```

The response explicitly reports `runtime_workers_started: 0` and
`external_runtime_invoked: false`. The controller rejects sensitive values,
blocked policy requests, unknown skill IDs, duplicate IDs, disabled explicit
skills, invalid state transitions, and attempts to rewrite a terminated plan.

## Dashboard and portable use

The **Native skills** dashboard panel provides:

- local inventory discovery and source-coverage display;
- a one-at-a-time SKILL.md preview from the local API;
- explicit plan-selection enable/disable controls;
- deterministic plan preparation; and
- pause, resume, terminate, and session-overlay controls for the visible local
  plan record.

It has no “run” control. The UI uses relative `/api/*` requests only.

The file layout and plain Markdown frontmatter follow the portable `SKILL.md`
folder convention used by SKILL.md-aware development agents. To use a native
skill with Claude Code, Cursor, Grok-compatible tools, or another compatible
consumer, configure that tool to read this repository-local `skills/` folder
according to that tool's own workspace-skill documentation, or select an
individual native skill folder manually. No claim is made that all tools load
all frontmatter fields identically. Do not bulk-copy a third-party collection
into another tool's skills folder.

## Regression controls and validation

- `scripts/check_safe_intake.py` allows only canonical `jinwoo_native: true`
  skill files under `skills/<category>/<id>/SKILL.md`; a copied `SKILL.md`,
  `AGENT.md`, or `.agent.md` elsewhere is a violation.
- The static guard rejects known reviewed-source runtime imports and packages
  for provider, computer-use, vision/OCR, and ROS paths.
- `POST /api/control/review` now includes the Batch 13 native skill-library
  safety check: 15 original planning-only skills, one canonical agent, 20
  covered metadata records, and no runtime invocation.
- Backend tests cover discovery, source count, no-runtime plan creation,
  availability controls, blocked plan rejection, pause/resume/terminate, local
  overlay revision, redacted auditing, and safe-intake scanning.

Run the checks from `jinwoo-ai`:

```bash
python3 -m unittest discover -s backend/tests -v
python3 scripts/check_safe_intake.py
npm run build
```

## Future activation gates

A future capability implementation must remain a separate, reviewed change.
It needs a narrow native contract, workspace and data-flow boundary,
component-level licence and provenance decision, dependency review, local test
evidence, disable/rollback path, audit behavior, explicit user approval, and
all relevant platform permissions. In particular, V1 still prohibits automatic
source merge, model download, upload/send/delete, uncontrolled terminal use,
desktop input, webcam capture, biometric processing, hardware/robotics control,
and unattended Internet discovery or installation loops.
