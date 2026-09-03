# Native agent definitions

This folder holds Jinwoo-owned agent manifests, not imported upstream agent prompts.

- `jinwoo-master-orchestrator/AGENT.md` is the canonical plan controller.
- It uses the native `skills/` library through `backend/app/skill_library.py`.
- It can only create and control visible, non-executing plans. It cannot enable an external runtime or change immutable skill documents.
