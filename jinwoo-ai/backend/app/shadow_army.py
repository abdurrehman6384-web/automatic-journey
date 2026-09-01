"""Native, bounded Shadow Army planning core.

This module is intentionally a local planning engine, not a background swarm
runner. It models the final logical hierarchy (15 commanders × 3 divisions ×
10 agents) while exposing at most Planner, Executor, and Verifier work seats
for a user-visible mission. Optional third-party frameworks are represented as
reviewed patterns only; this module never imports, starts, or delegates to them.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable

from .army import COMMANDERS, SUB_DEPARTMENTS, army_summary, needs_approval, select_commander
from .audit import AuditStore
from .frameworks import frameworks
from .policy import ActionClass, classify_action
from .schemas import (
    CoordinationPattern,
    RiskLevel,
    ShadowArmyAgent,
    ShadowArmyFramework,
    ShadowArmyOverview,
    ShadowArmyPlan,
    ShadowArmyPlanRequest,
    ShadowArmyStage,
)


class ShadowArmyPolicyError(ValueError):
    """Raised when a request cannot enter the native Army planning core."""


# These are logical seats, not processes, threads, model sessions, or tool
# grants. Every participating logical agent still routes through the same
# visible Planner → Executor → Verifier safety flow.
_AGENT_SEATS: tuple[tuple[str, str], ...] = (
    ("scout", "Scopes known facts, boundaries and missing evidence."),
    ("analyst", "Separates observations, assumptions, risks and options."),
    ("planner", "Breaks the mission into small, user-visible steps."),
    ("specialist", "Applies the selected division's domain knowledge."),
    ("reviewer", "Looks for gaps, conflicts and unintended consequences."),
    ("researcher", "Finds approved evidence requirements and citations."),
    ("implementer", "Prepares a safe draft; it has no direct tool authority."),
    ("tester", "Defines acceptance checks and failure cases."),
    ("auditor", "Checks policy, privacy, provenance and audit requirements."),
    ("reporter", "Produces a concise human-readable outcome packet."),
)

# These entries are intentionally declarative. The registry is the source of
# truth for exact source, licence, state, and runtime enablement; no upstream
# framework is instantiated here.
_PATTERN_IDS: dict[CoordinationPattern, tuple[str, ...]] = {
    CoordinationPattern.HIERARCHICAL: ("crewai", "metagpt", "ruflo", "microsoft-agent-framework"),
    CoordinationPattern.COMMANDER_COUNCIL: ("autogen", "microsoft-agent-framework", "agent-swarm"),
    CoordinationPattern.DEPENDENCY_GRAPH: ("langgraph", "open-multi-agent", "microsoft-agent-framework"),
    CoordinationPattern.BOUNDED_SWARM: ("ruflo", "agent-swarm", "roma"),
}

_PATTERN_EXPLANATIONS: dict[CoordinationPattern, str] = {
    CoordinationPattern.HIERARCHICAL: "Jinwoo → Bellion → Commander → Division → Planner, Executor, Verifier.",
    CoordinationPattern.COMMANDER_COUNCIL: "A bounded advisory council prepares viewpoints; Bellion preserves one decision route.",
    CoordinationPattern.DEPENDENCY_GRAPH: "A visible dependency graph prepares ordered hand-offs and explicit approval edges.",
    CoordinationPattern.BOUNDED_SWARM: "Several logical specialists are represented, while real runtime work remains capped and reviewable.",
}


@dataclass(frozen=True)
class _DivisionChoice:
    commander_id: str
    division_index: int
    division_name: str


def _slug(value: str) -> str:
    return "".join(character.lower() if character.isalnum() else "-" for character in value).strip("-")


def _choose_division(commander_id: str, prompt: str) -> _DivisionChoice:
    divisions = SUB_DEPARTMENTS[commander_id]
    normalized = prompt.casefold()

    # Preserve deterministic, explainable routing. The words do not grant a
    # capability; they merely select the most relevant logical division.
    signals = (
        (("test", "verify", "quality", "regression", "audit"), 2),
        (("plan", "design", "architecture", "research", "analysis"), 0),
        (("build", "code", "implement", "integrate", "deliver", "fix"), 1),
    )
    for terms, index in signals:
        if any(term in normalized for term in terms):
            return _DivisionChoice(commander_id, index, divisions[index])

    # A stable fallback avoids random routing while sharing work conceptually
    # across a commander's three divisions.
    index = sum(ord(character) for character in normalized) % len(divisions)
    return _DivisionChoice(commander_id, index, divisions[index])


def _logical_agents(choice: _DivisionChoice, requested: int) -> list[ShadowArmyAgent]:
    """Return a compact representative roster for the requested logical scope.

    A request may reserve up to the complete 450-agent catalogue, but the API
    returns at most ten representative seats for a readable mobile UI. This is
    deliberate: no omitted logical agent is hiddenly created or run.
    """

    representatives = min(requested, len(_AGENT_SEATS))
    return [
        ShadowArmyAgent(
            id=f"{choice.commander_id}.{choice.division_index + 1}.{seat_id}",
            name=f"{choice.division_name} · {seat_id.replace('-', ' ').title()}",
            commander_id=choice.commander_id,
            division_id=f"{choice.commander_id}-{choice.division_index + 1}",
            division=choice.division_name,
            specialty=specialty,
            logical=True,
            runtime_started=False,
        )
        for seat_id, specialty in _AGENT_SEATS[:representatives]
    ]


def _framework_patterns(pattern: CoordinationPattern) -> list[ShadowArmyFramework]:
    statuses = {status.id: status for status in frameworks.statuses()}
    selected: list[ShadowArmyFramework] = []

    for framework_id in _PATTERN_IDS[pattern]:
        status = statuses.get(framework_id)
        if status is None:
            # A missing registry record must be visible rather than silently
            # substituted with a package import or runtime fallback.
            selected.append(
                ShadowArmyFramework(
                    id=framework_id,
                    label=framework_id,
                    category="orchestration",
                    pattern_role="Registry record missing — no runtime selected.",
                    implementation_status="source-review-required",
                    execution_enabled=False,
                )
            )
            continue

        selected.append(
            ShadowArmyFramework(
                id=status.id,
                label=status.label,
                category=status.category,
                pattern_role=_pattern_role(framework_id),
                implementation_status=status.implementation_status,
                execution_enabled=status.execution_enabled,
            )
        )

    return selected


def _pattern_role(framework_id: str) -> str:
    roles = {
        "ruflo": "Swarm, coordination and memory-harness design reference.",
        "crewai": "Role and crew hierarchy design reference.",
        "autogen": "Bounded commander discussion and typed handoff reference.",
        "langgraph": "State graph, checkpoints and approval-edge reference.",
        "metagpt": "SOP-oriented software delivery reference.",
        "agent-swarm": "Deliverable-driven specialist collaboration reference.",
        "roma": "Recursive task-tree reference; licence review remains required.",
        "open-multi-agent": "Dynamic DAG and coordination reference.",
        "microsoft-agent-framework": "Production workflow, middleware and human-in-loop reference.",
    }
    return roles.get(framework_id, "Controlled multi-agent pattern reference.")


def _stages(choice: _DivisionChoice, pattern: CoordinationPattern, requires_approval: bool) -> list[ShadowArmyStage]:
    return [
        ShadowArmyStage(
            id="jinwoo-intake",
            label="Jinwoo · mission intake",
            owner="Jinwoo",
            phase="intake",
            detail="Classify the request, data boundary and requested coordination pattern.",
            requires_approval=False,
        ),
        ShadowArmyStage(
            id="bellion-route",
            label="Bellion · command routing",
            owner="Bellion",
            phase="route",
            detail=f"Route through {choice.division_name}; {_PATTERN_EXPLANATIONS[pattern]}",
            requires_approval=False,
        ),
        ShadowArmyStage(
            id="commander-scope",
            label="Commander · division scope",
            owner=choice.commander_id.title(),
            phase="scope",
            detail="Choose logical specialists and state what evidence is needed before any action.",
            requires_approval=False,
        ),
        ShadowArmyStage(
            id="planner",
            label="Planner · visible plan",
            owner="Planner",
            phase="plan",
            detail="Produce bounded steps, dependency edges and an allowed-tool list.",
            requires_approval=False,
        ),
        ShadowArmyStage(
            id="executor",
            label="Executor · safe draft",
            owner="Executor",
            phase="draft",
            detail="Prepare a read-only result or a separately approvable action proposal.",
            requires_approval=requires_approval,
        ),
        ShadowArmyStage(
            id="verifier",
            label="Verifier · evidence and policy",
            owner="Verifier",
            phase="verify",
            detail="Check evidence, acceptance criteria, privacy and policy before delivery.",
            requires_approval=False,
        ),
        ShadowArmyStage(
            id="jinwoo-delivery",
            label="Jinwoo · visible delivery",
            owner="Jinwoo",
            phase="deliver",
            detail="Show the outcome and audit metadata; no optional framework runtime is invoked.",
            requires_approval=False,
        ),
    ]


def build_shadow_army_plan(request: ShadowArmyPlanRequest) -> ShadowArmyPlan:
    """Build a deterministic planning topology without calling a model/tool."""

    decision = classify_action(request.prompt)
    if decision.action_class is ActionClass.BLOCKED:
        raise ShadowArmyPolicyError(decision.reason)

    commander = select_commander(request.prompt)
    division = _choose_division(commander.id, request.prompt)
    requires_approval = decision.requires_approval or needs_approval(request.prompt, commander)
    risk = RiskLevel.HIGH if requires_approval else RiskLevel.MEDIUM if commander.safety.value == "sandboxed" else RiskLevel.LOW
    logical_scope = min(request.requested_logical_agents, army_summary()["logical_agents"])

    return ShadowArmyPlan(
        prompt=request.prompt,
        coordination=request.coordination,
        commander_id=commander.id,
        commander=commander.name,
        division_id=f"{division.commander_id}-{division.division_index + 1}",
        division=division.division_name,
        requested_logical_agents=request.requested_logical_agents,
        logical_agents_reserved=logical_scope,
        displayed_logical_agents=min(logical_scope, len(_AGENT_SEATS)),
        runtime_worker_cap=3,
        runtime_workers_started=0,
        risk=risk,
        requires_approval=requires_approval,
        external_runtime_invoked=False,
        pattern_summary=_PATTERN_EXPLANATIONS[request.coordination],
        agents=_logical_agents(division, logical_scope),
        stages=_stages(division, request.coordination, requires_approval),
        frameworks=_framework_patterns(request.coordination),
        guardrails=[
            "Logical agents are catalogue seats; no process, thread, model session or external framework was started.",
            "Only Planner, Executor and Verifier runtime roles may be proposed for a single mission.",
            "Jinwoo retains policy, explicit approval, workspace confinement, privacy and audit ownership.",
            "An impactful task remains a proposal until the user explicitly approves the individual action.",
        ],
    )


class ShadowArmyStore:
    """In-memory, audit-backed planning store for visible Army topology drafts."""

    def __init__(self, audit: AuditStore | None = None) -> None:
        self._plans: dict[str, ShadowArmyPlan] = {}
        self._audit = audit

    def overview(self) -> ShadowArmyOverview:
        capacity = army_summary()
        return ShadowArmyOverview(
            commanders=capacity["departments"],
            divisions=capacity["sub_departments"],
            logical_agents=capacity["logical_agents"],
            worker_slots=capacity["worker_slots"],
            active_runtime_workers=0,
            runtime_cap_per_mission=3,
            all_external_runtimes_disabled=all(
                not status.execution_enabled
                for status in frameworks.statuses()
                if status.id not in {"jinwoo-native", "jinwoo-native-control-audit"}
            ),
            hierarchy=[
                "Jinwoo · Shadow Monarch",
                "Bellion · Grand Marshal",
                "15 Commanders",
                "45 Sub-departments",
                "450 Logical Agents",
                "Planner · Executor · Verifier",
            ],
            supported_patterns=list(CoordinationPattern),
        )

    def create(self, request: ShadowArmyPlanRequest) -> ShadowArmyPlan:
        plan = build_shadow_army_plan(request)
        self._plans[plan.id] = plan
        if self._audit is not None:
            self._audit.record(
                "shadow_army.plan_created",
                (
                    f"{plan.coordination.value} topology prepared for {plan.commander} / {plan.division}; "
                    f"{plan.logical_agents_reserved} logical seats reserved, "
                    f"{plan.runtime_worker_cap} runtime workers maximum; no external runtime invoked."
                ),
                mission_id=plan.id,
                actor="local-user",
            )
        return plan

    def list(self) -> list[ShadowArmyPlan]:
        return sorted(self._plans.values(), key=lambda item: item.created_at, reverse=True)


def iter_logical_agent_ids() -> Iterable[str]:
    """Expose the full deterministic 450-seat catalogue without creating workers."""

    for commander in COMMANDERS:
        for division_index, _division in enumerate(SUB_DEPARTMENTS[commander.id], start=1):
            for seat_id, _specialty in _AGENT_SEATS:
                yield f"{commander.id}.{division_index}.{seat_id}"


if len(tuple(iter_logical_agent_ids())) != sum(len(divisions) for divisions in SUB_DEPARTMENTS.values()) * len(_AGENT_SEATS):
    # Equivalent to 15 × 3 × 10; keep a defensive invariant adjacent to the
    # generator in case a command hierarchy changes later.
    raise RuntimeError("Shadow Army logical-agent catalogue no longer matches the declared hierarchy.")
