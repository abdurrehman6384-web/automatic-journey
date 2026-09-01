"""Controlled adapter registry for optional multi-agent frameworks.

Jinwoo's local mission engine remains the one canonical orchestrator. An
installed package or sidecar never receives a mission automatically and cannot
bypass the policy, approval, workspace, or audit boundaries owned by Jinwoo.

Batch 1 contains the first five integrations requested by the owner. Their
adapter contracts are real and testable now; their upstream runtimes remain
non-executable until a version-pinned, local compatibility review is complete.
"""

from __future__ import annotations

from dataclasses import dataclass
from importlib.util import find_spec
from shutil import which
from typing import Literal

from .policy import ActionClass, classify_action
from .schemas import FrameworkDryRun, FrameworkState, FrameworkStatus


class FrameworkNotFoundError(KeyError):
    """Raised for an adapter id outside the reviewed registry."""


@dataclass(frozen=True)
class FrameworkAdapter:
    """Metadata plus a policy-gated dry-run contract for one integration."""

    id: str
    label: str
    runtime: Literal["builtin", "python", "typescript-mcp"]
    category: Literal["orchestration", "workflow"]
    integration_batch: int
    owner_commander: str
    license: str
    source_url: str | None
    purpose: str
    python_module: str | None = None
    executable: str | None = None

    @property
    def is_native(self) -> bool:
        return self.id == "jinwoo-native"

    def is_detected(self) -> bool:
        try:
            if self.python_module:
                return find_spec(self.python_module) is not None
            if self.executable:
                return which(self.executable) is not None
        except (ImportError, ValueError):
            return False
        return self.is_native

    def status(self) -> FrameworkStatus:
        if self.is_native:
            return FrameworkStatus(
                id=self.id,
                label=self.label,
                runtime=self.runtime,
                category=self.category,
                integration_batch=self.integration_batch,
                owner_commander=self.owner_commander,
                license=self.license,
                source_url=self.source_url,
                state=FrameworkState.CANONICAL,
                implementation_status="active",
                execution_enabled=True,
                detail="Canonical local mission engine; policy, approval, workspace and audit controls stay here.",
            )

        detected = self.is_detected()
        state = FrameworkState.DETECTED if detected else FrameworkState.NOT_INSTALLED
        availability = "Detected locally" if detected else "Not installed"
        return FrameworkStatus(
            id=self.id,
            label=self.label,
            runtime=self.runtime,
            category=self.category,
            integration_batch=self.integration_batch,
            owner_commander=self.owner_commander,
            license=self.license,
            source_url=self.source_url,
            state=state,
            implementation_status="contract-ready" if self.integration_batch == 1 else "queued",
            execution_enabled=False,
            detail=(
                f"{availability}; the controlled adapter contract is ready, but upstream execution is disabled. "
                f"{self.purpose}"
            ),
        )

    def dry_run(self, prompt: str, requested_agents: int) -> FrameworkDryRun:
        """Return a bounded, policy-screened plan without invoking any upstream runtime."""

        decision = classify_action(prompt)
        if decision.action_class == ActionClass.BLOCKED:
            policy_outcome: Literal["safe-plan", "approval-required", "blocked"] = "blocked"
            summary = "The request is blocked by Jinwoo policy; no framework plan or external runtime was started."
            steps = ["Keep the request out of every integration runtime.", "Explain the safety boundary to the user."]
        elif decision.action_class == ActionClass.IMPACTFUL:
            policy_outcome = "approval-required"
            summary = "A bounded framework plan was prepared, but an explicit mission approval is required before any future tool action."
            steps = [
                "Keep the plan inside Jinwoo's selected workspace and policy boundary.",
                "Show the proposed action and wait for user approval.",
                "Do not invoke the upstream framework runtime in this V1 dry run.",
            ]
        else:
            policy_outcome = "safe-plan"
            summary = "A read-only, bounded framework plan was prepared; no upstream runtime or tool was invoked."
            steps = [
                "Use at most Planner, Executor and Verifier worker roles for this mission.",
                "Keep external framework execution disabled until its version-pinned review passes.",
                "Return evidence and a visible audit event through Jinwoo.",
            ]

        return FrameworkDryRun(
            framework_id=self.id,
            framework_label=self.label,
            policy_outcome=policy_outcome,
            requested_agents=requested_agents,
            bounded_runtime_workers=min(requested_agents, 3),
            external_runtime_invoked=False,
            requires_approval=decision.requires_approval,
            summary=summary,
            next_steps=steps,
        )


class FrameworkRegistry:
    """Single discovery and dry-run point for controlled integrations.

    A framework only becomes executable after an individual, version-pinned
    adapter implementation, licence review, offline tests, workspace confinement
    and approval/audit hand-off have all passed. This prevents competing agent
    loops from changing the product's autonomy or privacy posture.
    """

    def __init__(self) -> None:
        self._adapters = (
            FrameworkAdapter(
                id="jinwoo-native",
                label="Jinwoo Native Engine",
                runtime="builtin",
                category="orchestration",
                integration_batch=0,
                owner_commander="Jinwoo",
                license="Original project code",
                source_url=None,
                purpose="Visible Planner, Executor and Verifier mission flow.",
            ),
            # Owner-requested integration batch 1 (listed order).
            FrameworkAdapter(
                id="swarms",
                label="Swarms",
                runtime="python",
                category="orchestration",
                integration_batch=1,
                owner_commander="Bellion",
                license="Apache-2.0",
                source_url="https://github.com/kyegomez/swarms",
                python_module="swarms",
                purpose="Reserved for bounded hierarchical worker and specialist patterns.",
            ),
            FrameworkAdapter(
                id="agency-swarm",
                label="Agency-Swarm",
                runtime="python",
                category="orchestration",
                integration_batch=1,
                owner_commander="Beru",
                license="MIT",
                source_url="https://github.com/VRSEN/agency-swarm",
                python_module="agency_swarm",
                purpose="Reserved for policy-gated organisation-style hand-offs where compatible.",
            ),
            FrameworkAdapter(
                id="ruflo",
                label="Ruflo",
                runtime="typescript-mcp",
                category="orchestration",
                integration_batch=1,
                owner_commander="Igris",
                license="MIT",
                source_url="https://github.com/ruvnet/ruflo",
                executable="ruflo",
                purpose="Reserved for an optional local TypeScript/MCP developer-harness bridge.",
            ),
            FrameworkAdapter(
                id="langgraph",
                label="LangGraph",
                runtime="python",
                category="workflow",
                integration_batch=1,
                owner_commander="Jinwoo",
                license="MIT",
                source_url="https://github.com/langchain-ai/langgraph",
                python_module="langgraph",
                purpose="Reserved for checkpointed, stateful workflow primitives under Jinwoo control.",
            ),
            FrameworkAdapter(
                id="crewai",
                label="CrewAI",
                runtime="python",
                category="orchestration",
                integration_batch=1,
                owner_commander="Beru",
                license="MIT",
                source_url="https://github.com/crewAIInc/crewAI",
                python_module="crewai",
                purpose="Reserved for bounded role-based crews after local compatibility review.",
            ),
        )
        self._by_id = {adapter.id: adapter for adapter in self._adapters}

    def statuses(self) -> list[FrameworkStatus]:
        return [adapter.status() for adapter in self._adapters]

    def dry_run(self, framework_id: str, prompt: str, requested_agents: int) -> FrameworkDryRun:
        adapter = self._by_id.get(framework_id)
        if adapter is None:
            raise FrameworkNotFoundError(framework_id)
        return adapter.dry_run(prompt, requested_agents)


frameworks = FrameworkRegistry()
