"""Native, no-runtime master orchestration for Jinwoo-owned skill plans.

This controller governs only visible local plan state. It is intentionally not
an autonomous agent runner: selected skills remain planning instructions and
no external agent, model, provider, process, device or tool is started.
"""

from __future__ import annotations

from datetime import datetime, timezone

from .audit import AuditStore
from .policy import ActionClass, classify_action
from .schemas import (
    SkillOrchestratorDirectiveRequest,
    SkillOrchestratorPlan,
    SkillOrchestratorPlanRequest,
    SkillOrchestratorStage,
    SkillOrchestratorState,
)
from .sensitive import contains_sensitive_value
from .skill_activation import SkillActivationStore
from .skill_library import SkillLibraryError, NativeSkillLibrary, skill_library


class SkillOrchestratorError(ValueError):
    """Raised when a requested plan or plan-state transition is invalid."""


def _guard_text(value: str | None) -> None:
    if value and contains_sensitive_value(value):
        raise SkillOrchestratorError("Credentials and one-time codes cannot be included in a native skill plan.")


def _stages(skill_ids: list[str], requires_approval: bool) -> list[SkillOrchestratorStage]:
    """Construct a bounded Planner → Executor → Verifier plan without workers."""

    planner_ids = skill_ids[: min(2, len(skill_ids))]
    verifier_ids = [
        skill_id for skill_id in skill_ids
        if skill_id in {"evidence-before-completion", "agent-evaluation", "approval-and-permission-boundary"}
    ] or skill_ids[-1:]
    return [
        SkillOrchestratorStage(
            id="planner",
            label="Planner · native skill selection",
            skill_ids=planner_ids,
            detail="Break the outcome into bounded, visible steps and identify evidence before any action proposal.",
        ),
        SkillOrchestratorStage(
            id="executor",
            label="Executor · safe draft only",
            skill_ids=skill_ids,
            detail="Prepare a planning-only draft. Any consequential action remains an explicit proposal.",
            requires_approval=requires_approval,
        ),
        SkillOrchestratorStage(
            id="verifier",
            label="Verifier · policy and evidence",
            skill_ids=verifier_ids,
            detail="Check acceptance evidence, source boundaries, privacy, policy and approval conditions before delivery.",
        ),
    ]


class SkillOrchestratorStore:
    """In-memory, audit-backed native plan controller with no worker backend."""

    def __init__(
        self,
        audit: AuditStore | None = None,
        library: NativeSkillLibrary = skill_library,
        activation_store: SkillActivationStore | None = None,
    ) -> None:
        self._plans: dict[str, SkillOrchestratorPlan] = {}
        self._audit = audit
        self._library = library
        self._activation_store = activation_store

    def create(self, request: SkillOrchestratorPlanRequest) -> SkillOrchestratorPlan:
        _guard_text(request.objective)
        _guard_text(request.controller_instruction)
        decision = classify_action(" ".join(part for part in (request.objective, request.controller_instruction) if part))
        if decision.action_class is ActionClass.BLOCKED:
            raise SkillOrchestratorError(decision.reason)
        try:
            resolution = self._library.resolve(
                request.objective,
                request.skill_ids,
                max_results=5,
                disabled_skill_ids=self._activation_store.disabled_skill_ids() if self._activation_store else frozenset(),
            )
        except SkillLibraryError as error:
            raise SkillOrchestratorError(str(error)) from error
        requires_approval = decision.requires_approval or any(skill.requires_approval for skill in resolution.skills)
        plan = SkillOrchestratorPlan(
            objective=request.objective,
            selected_skill_ids=resolution.selected_skill_ids,
            policy_outcome="approval-required" if requires_approval else "safe-plan",
            requires_approval=requires_approval,
            instruction_overlay=request.controller_instruction,
            runtime_workers_started=0,
            external_runtime_invoked=False,
            stages=_stages(resolution.selected_skill_ids, requires_approval),
            guardrails=[
                "Jinwoo Master Orchestrator selects native skill instructions only; no external agent or runtime is started.",
                "Planner, Executor and Verifier are visible plan roles, not running workers or model sessions.",
                "A controller instruction is a session-local overlay and cannot rewrite immutable native skill files.",
                "Pause, resume and terminate affect only this local plan record and never approve an impactful action.",
                "Any file, network, provider, desktop, device, scanner or package action requires a separate reviewed implementation and explicit approval.",
            ],
        )
        self._plans[plan.id] = plan
        self._record(
            "skill_orchestrator.plan_created",
            (
                f"Jinwoo Master Orchestrator prepared a {plan.policy_outcome} native skill plan with "
                f"{len(plan.selected_skill_ids)} selected skills; no worker or external runtime was invoked."
            ),
            plan.id,
        )
        return plan

    def list(self) -> list[SkillOrchestratorPlan]:
        return sorted(self._plans.values(), key=lambda plan: plan.updated_at, reverse=True)

    def directive(self, plan_id: str, request: SkillOrchestratorDirectiveRequest) -> SkillOrchestratorPlan | None:
        plan = self._plans.get(plan_id)
        if plan is None:
            return None
        _guard_text(request.controller_instruction)
        now = datetime.now(timezone.utc)
        if request.action == "pause":
            if plan.state is not SkillOrchestratorState.PLANNED:
                raise SkillOrchestratorError("Only a planned native skill plan can be paused.")
            updated = plan.model_copy(update={"state": SkillOrchestratorState.PAUSED, "updated_at": now})
        elif request.action == "resume":
            if plan.state is not SkillOrchestratorState.PAUSED:
                raise SkillOrchestratorError("Only a paused native skill plan can be resumed.")
            updated = plan.model_copy(update={"state": SkillOrchestratorState.PLANNED, "updated_at": now})
        elif request.action == "terminate":
            if plan.state is SkillOrchestratorState.TERMINATED:
                raise SkillOrchestratorError("This native skill plan is already terminated.")
            updated = plan.model_copy(update={"state": SkillOrchestratorState.TERMINATED, "updated_at": now})
        else:
            if plan.state is SkillOrchestratorState.TERMINATED:
                raise SkillOrchestratorError("A terminated native skill plan cannot be rewritten; create a new plan instead.")
            if not request.controller_instruction:
                raise SkillOrchestratorError("Provide a non-blank session-local instruction to rewrite the plan overlay.")
            decision = classify_action(request.controller_instruction)
            if decision.action_class is ActionClass.BLOCKED:
                raise SkillOrchestratorError(decision.reason)
            requires_approval = plan.requires_approval or decision.requires_approval
            updated = plan.model_copy(
                update={
                    "instruction_overlay": request.controller_instruction,
                    "requires_approval": requires_approval,
                    "policy_outcome": "approval-required" if requires_approval else "safe-plan",
                    "stages": _stages(plan.selected_skill_ids, requires_approval),
                    "updated_at": now,
                }
            )
        self._plans[plan_id] = updated
        self._record(
            "skill_orchestrator.directive_applied",
            (
                f"Jinwoo Master Orchestrator applied the {request.action} directive to a local native skill plan; "
                "no skill, worker or external runtime was executed."
            ),
            plan_id,
        )
        return updated

    def _record(self, event_type: str, detail: str, plan_id: str) -> None:
        if self._audit is not None:
            self._audit.record(event_type, detail, mission_id=plan_id, actor="local-user")
