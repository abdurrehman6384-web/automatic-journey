# Jinwoo native skills library

This is a curated, **clean-room** skill library. Every `SKILL.md` in this tree
is original Jinwoo instruction text designed for the portable SKILL.md folder
convention used by Claude Code, Cursor, Grok-compatible agents, Codex-oriented
clients, and other skill-aware tools.

## Layout

```text
skills/
  SOURCES.json                    # provenance and review status for requested repositories
  core/                            # verification, governance, approval and orchestration
  engineering/                     # ADR, dependency, scope and evaluation plans
  catalogs/                        # curation and agent-blueprint triage
  computer-use/                    # consented desktop planning only
  interaction/                     # camera-off gesture/vision planning only
  robotics/                        # software review with no hardware control
  models/                          # provider-neutral multimodal boundaries
  media/                           # original rights-aware media planning
```

## Use from Jinwoo

- `GET /api/skills` lists all native skills, the canonical agent, and source
  coverage.
- `GET /api/skills/{id}` returns a native skill's instructions.
- `POST /api/skills/resolve` deterministically selects relevant native skills
  without calling a model or external service.
- `POST /api/skill-orchestrator/plans` creates a visible Planner → Executor →
  Verifier plan. Its pause, resume, terminate, and instruction-revision routes
  affect only that local plan; they never execute a skill or external runtime.

## Use from an external SKILL.md-aware agent

Point the agent at this `skills/` directory or manually select the one relevant
native skill folder according to that tool's documented workspace-skill setup.
Do not bulk-copy a third-party collection into a tool-specific skills folder.
The local skill instructions remain portable Markdown and contain no required
provider, installer, package, model, browser, or device dependency.

## Provenance and activation

`SOURCES.json` records the requested repository URL, observed default-branch
revision, licence signal, review scope, retained native capabilities, and
exclusion decision. It is not a reuse licence. No upstream source, prompt,
agent, asset, model, package, or installer is bundled in this tree.

All native skills are `planning-only`. Skill selection is usable now, but any
consequential external action still requires its own policy, workspace, privacy,
licence, sandbox, approval, and audit review.
