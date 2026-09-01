"""Controlled adapter registry for optional multi-agent frameworks.

Jinwoo's local mission engine remains the one canonical orchestrator. An
installed package or sidecar never receives a mission automatically and cannot
bypass the policy, approval, workspace, or audit boundaries owned by Jinwoo.

Batches 01–04 contain owner-requested integration lanes. Their adapter
contracts are real and testable now; upstream runtimes remain non-executable
until a version-pinned, local compatibility and licence review is complete.
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
    runtime: Literal[
        "builtin", "python", "typescript-mcp", "typescript-service", "container-sidecar", "go-cli", "go-service",
        "rust-cli", "desktop-client", "mobile-client",
    ]
    category: Literal[
        "orchestration", "workflow", "coding", "research", "web-collection", "memory", "automation", "security",
        "governance", "computer-use", "reference",
    ]
    integration_batch: int
    owner_commander: str
    license: str
    source_url: str | None
    purpose: str
    capabilities: tuple[str, ...] = ()
    activation_boundary: Literal["read-only", "approval-required", "sandboxed", "reference-only"] = "approval-required"
    native_adapter: bool = False
    implementation_status: Literal[
        "active", "contract-ready", "license-review-required", "reference-only", "archived-upstream", "queued",
    ] = "contract-ready"
    guardrails: tuple[str, ...] = ()
    python_module: str | None = None
    executable: str | None = None

    @property
    def is_native(self) -> bool:
        return self.native_adapter

    def is_detected(self) -> bool:
        try:
            module_detected = bool(self.python_module and find_spec(self.python_module) is not None)
            executable_detected = bool(self.executable and which(self.executable) is not None)
            return self.is_native or module_detected or executable_detected
        except (ImportError, ValueError):
            return False

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
                implementation_status=self.implementation_status,
                execution_enabled=self.implementation_status == "active",
                capabilities=list(self.capabilities),
                activation_boundary=self.activation_boundary,
                detail=(
                    "Canonical local mission engine; policy, approval, workspace and audit controls stay here."
                    if self.id == "jinwoo-native"
                    else "Active native control-plane review; it cannot enable adapters or execute external tools."
                ),
            )

        if self.implementation_status == "reference-only":
            state = FrameworkState.REFERENCE_ONLY
            availability = "Reference only"
        else:
            detected = self.is_detected()
            state = FrameworkState.DETECTED if detected else FrameworkState.NOT_INSTALLED
            availability = "Detected locally" if detected else "Not installed"

        if self.implementation_status == "license-review-required":
            readiness = "licence review is required before upstream activation"
        elif self.implementation_status == "reference-only":
            readiness = "source reuse and runtime activation are prohibited"
        elif self.implementation_status == "archived-upstream":
            readiness = "upstream is archived and needs a maintained-source review before any adoption"
        elif self.implementation_status == "queued":
            readiness = "adapter implementation is queued"
        else:
            readiness = "the controlled adapter contract is ready"
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
            implementation_status=self.implementation_status,
            execution_enabled=False,
            capabilities=list(self.capabilities),
            activation_boundary=self.activation_boundary,
            detail=(
                f"{availability}; {readiness}, and upstream execution is disabled. "
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
        elif self.implementation_status == "reference-only":
            policy_outcome = "approval-required" if decision.requires_approval else "safe-plan"
            summary = (
                "A reference-only capability review was prepared. No upstream source, proprietary core, runtime or tool may be used."
            )
            steps = [
                "Use only high-level public capability observations for this review.",
                "Do not copy, link, bundle, install or invoke this project's source or runtime.",
                "Design any future Jinwoo-native feature independently and keep it inside Jinwoo policy and approval controls.",
            ]
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

        if self.guardrails and policy_outcome != "blocked":
            steps.extend(self.guardrails)

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
                native_adapter=True,
                implementation_status="active",
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
            # Owner-requested integration batch 2 (listed order).
            FrameworkAdapter(
                id="ag2",
                label="AG2",
                runtime="python",
                category="orchestration",
                integration_batch=2,
                owner_commander="Bellion",
                license="Apache-2.0",
                source_url="https://github.com/ag2ai/ag2",
                python_module="ag2",
                purpose="Reserved for bounded, policy-mediated multi-agent conversations and hand-offs.",
                guardrails=(
                    "Let Bellion own routing; do not create independent agent-to-agent loops.",
                    "Keep provider, tool and approval decisions inside Jinwoo's native gateway.",
                ),
            ),
            FrameworkAdapter(
                id="openhands",
                label="OpenHands",
                runtime="container-sidecar",
                category="coding",
                integration_batch=2,
                owner_commander="Igris",
                license="MIT",
                source_url="https://github.com/OpenHands/OpenHands",
                python_module="openhands",
                executable="openhands",
                purpose="Reserved for isolated coding-task proposals and sandboxed patch review.",
                guardrails=(
                    "Require an isolated sandbox and the selected Workspace Guard root.",
                    "Never run shell commands, patches, git operations or installs without a visible approval.",
                ),
            ),
            FrameworkAdapter(
                id="firecrawl",
                label="Firecrawl",
                runtime="typescript-service",
                category="web-collection",
                integration_batch=2,
                owner_commander="Tank",
                license="AGPL-3.0",
                source_url="https://github.com/firecrawl/firecrawl",
                purpose="Reserved for user-approved public-web search/scrape plans after a separate licence decision.",
                implementation_status="license-review-required",
                guardrails=(
                    "Do not crawl, fetch URLs, use cookies or transmit workspace data in a dry run.",
                    "Future targets must be public, user-supplied or explicitly approved, and policy-checked.",
                ),
            ),
            FrameworkAdapter(
                id="firecrawl-web-agent",
                label="Firecrawl Web-Agent",
                runtime="typescript-service",
                category="research",
                integration_batch=2,
                owner_commander="Tank",
                license="MIT",
                source_url="https://github.com/firecrawl/web-agent",
                purpose="Reserved for structured, approved public-web research plans.",
                guardrails=(
                    "No browser session, authenticated site, cookie or private-network access is allowed.",
                    "Future research requires source attribution and user-visible target approval.",
                ),
            ),
            FrameworkAdapter(
                id="crawl4ai",
                label="Crawl4AI",
                runtime="python",
                category="web-collection",
                integration_batch=2,
                owner_commander="Tank",
                license="Apache-2.0",
                source_url="https://github.com/unclecode/crawl4ai",
                python_module="crawl4ai",
                purpose="Reserved for bounded public-web collection after robots, target and rate-limit review.",
                guardrails=(
                    "No URL is fetched in a dry run; authenticated, private and localhost targets stay disallowed.",
                    "Future collection must use strict domain, rate, size and citation limits.",
                ),
            ),
            # Owner-requested integration batch 3 (listed order).
            FrameworkAdapter(
                id="mem0",
                label="Mem0",
                runtime="python",
                category="memory",
                integration_batch=3,
                owner_commander="Jinwoo",
                license="Apache-2.0",
                source_url="https://github.com/mem0ai/mem0",
                python_module="mem0",
                purpose="Reserved for separately consented, optional memory interoperability; local SQLite remains authoritative.",
                guardrails=(
                    "Do not treat the owner's ambiguous memo API as confirmed Mem0 integration.",
                    "Never sync memory content, identifiers or provider credentials without renewed, per-operation consent.",
                ),
            ),
            FrameworkAdapter(
                id="openclaw",
                label="OpenClaw",
                runtime="typescript-service",
                category="automation",
                integration_batch=3,
                owner_commander="Nox",
                license="MIT",
                source_url="https://github.com/openclaw/openclaw",
                executable="openclaw",
                purpose="Reserved for a future isolated local automation gateway under Jinwoo mission control.",
                guardrails=(
                    "Do not start messaging channels, pairing, schedules, skills, browser access or shell tools in a dry run.",
                    "Future delivery and tool actions must remain locally isolated and require a visible Jinwoo approval.",
                ),
            ),
            FrameworkAdapter(
                id="trufflehog",
                label="TruffleHog",
                runtime="go-cli",
                category="security",
                integration_batch=3,
                owner_commander="Greed",
                license="AGPL-3.0",
                source_url="https://github.com/trufflesecurity/trufflehog",
                executable="trufflehog",
                purpose="Reserved for bounded, local secret-exposure review after a separate licence decision.",
                implementation_status="license-review-required",
                guardrails=(
                    "Do not read files, scan Git history, verify credentials or contact a provider in a dry run.",
                    "Future findings must be masked, local-only and confined to the selected workspace after explicit approval.",
                ),
            ),
            FrameworkAdapter(
                id="gitleaks",
                label="Gitleaks",
                runtime="go-cli",
                category="security",
                integration_batch=3,
                owner_commander="Greed",
                license="MIT",
                source_url="https://github.com/gitleaks/gitleaks",
                executable="gitleaks",
                purpose="Reserved for bounded local secret-scanner proposals and redacted security reporting.",
                guardrails=(
                    "Do not read workspace files or Git history and do not expose any candidate secret in a dry run.",
                    "Future scans need explicit approval, a selected workspace boundary and redacted local findings only.",
                ),
            ),
            # Owner-requested advanced skills batch 4 (listed order). The entries below
            # are capability contracts only: no upstream package, archive, container,
            # desktop controller, voice/vision service or CLI is installed or invoked.
            FrameworkAdapter(
                id="goose",
                label="Goose",
                runtime="rust-cli",
                category="coding",
                integration_batch=4,
                owner_commander="Igris",
                license="Apache-2.0",
                source_url="https://github.com/block/goose",
                executable="goose",
                purpose="Reserved for sandboxed coding-agent, tool-protocol and evaluation proposals.",
                capabilities=("Coding-task plans", "MCP/ACP boundary review", "Test and evaluation proposals"),
                activation_boundary="sandboxed",
                guardrails=(
                    "Use a disposable sandbox with only the selected Workspace Guard root mounted read-only by default.",
                    "Do not run a shell command, edit, test, install, MCP tool or provider call without separate visible approval.",
                ),
            ),
            FrameworkAdapter(
                id="orkas",
                label="Orkas",
                runtime="desktop-client",
                category="orchestration",
                integration_batch=4,
                owner_commander="Bellion",
                license="MIT",
                source_url="https://github.com/Orkas-AI/Orkas",
                purpose="Reserved for local desktop team-routing, reflection and skill-crystallisation pattern review.",
                capabilities=("Team-routing patterns", "Reflection proposals", "Skill-crystallisation review"),
                activation_boundary="sandboxed",
                guardrails=(
                    "Bellion and Jinwoo retain the one canonical mission queue; do not create an independent agent team or memory store.",
                    "Do not configure a provider, enable MCP tools or persist a skill without explicit Jinwoo approval and a local review.",
                ),
            ),
            FrameworkAdapter(
                id="bytebot",
                label="Bytebot",
                runtime="container-sidecar",
                category="computer-use",
                integration_batch=4,
                owner_commander="Nox",
                license="Apache-2.0",
                source_url="https://github.com/bytebot-ai/bytebot",
                purpose="Reserved for isolated container-desktop computer-use proposals; the reviewed upstream is archived.",
                capabilities=("Container desktop boundary", "Computer-use proposals", "Action-transcript design"),
                activation_boundary="sandboxed",
                implementation_status="archived-upstream",
                guardrails=(
                    "Do not launch a container or mount the host home directory, credentials, clipboard, devices or browser profile.",
                    "Any future pointer, keyboard, file, network or delivery step needs an individual user approval and visible transcript.",
                ),
            ),
            FrameworkAdapter(
                id="open-desktop",
                label="OpenDesktop",
                runtime="desktop-client",
                category="computer-use",
                integration_batch=4,
                owner_commander="Nox",
                license="MIT",
                source_url="https://github.com/Atum246/OpenDesktop",
                purpose="Reserved for desktop computer-use, voice and vision capability planning under explicit local control.",
                capabilities=("Desktop-action proposals", "Voice/vision boundary review", "Local automation plans"),
                activation_boundary="sandboxed",
                guardrails=(
                    "Do not capture a screen, microphone, camera, clipboard or desktop input in a dry run or by default.",
                    "Future desktop actions need a selected workspace where relevant, an exact action preview and per-action approval.",
                ),
            ),
            FrameworkAdapter(
                id="hermes-agent",
                label="Hermes Agent",
                runtime="python",
                category="automation",
                integration_batch=4,
                owner_commander="Igris",
                license="MIT",
                source_url="https://github.com/NousResearch/hermes-agent",
                python_module="hermes",
                purpose="Reserved for agent-skill, local state, MCP and coding-workflow boundary proposals.",
                capabilities=("Skill-boundary review", "Local-state patterns", "MCP and coding proposals"),
                activation_boundary="sandboxed",
                guardrails=(
                    "Do not install optional skills, MCP servers, plugins, cron jobs, gateways or providers from this lane.",
                    "Keep all tool decisions, workspace limits, memory consent and audit events in Jinwoo's native control plane.",
                ),
            ),
            FrameworkAdapter(
                id="openagent",
                label="OpenAgent",
                runtime="go-service",
                category="automation",
                integration_batch=4,
                owner_commander="Fang",
                license="Apache-2.0",
                source_url="https://github.com/the-open-agent/openagent",
                purpose="Reserved for RAG, tool-routing and personal-assistant capability-contract review.",
                capabilities=("RAG architecture review", "MCP/skill routing", "Browser and coding boundary review"),
                activation_boundary="sandboxed",
                guardrails=(
                    "Do not start its service, browser, computer-use, shell, media, authentication or agent-loop capability.",
                    "A future adapter must use Jinwoo's local memory, provider consent, workspace boundary and approval path rather than upstream defaults.",
                ),
            ),
            FrameworkAdapter(
                id="iris-go",
                label="IRIS-GO",
                runtime="typescript-service",
                category="orchestration",
                integration_batch=4,
                owner_commander="Bellion",
                license="Unverified — README claims MIT; no repository LICENSE file at review",
                source_url="https://github.com/IRISX-AI/IRIS-GO",
                purpose="Reserved for local multi-agent workflow and dashboard capability review only while licence evidence is unresolved.",
                capabilities=("Local multi-agent planning", "Workflow dashboard review", "CLI/mobile boundary design"),
                activation_boundary="sandboxed",
                implementation_status="license-review-required",
                guardrails=(
                    "Do not copy, install, link, bundle or invoke upstream source until a valid licence file and deployment terms are verified.",
                    "No autonomous system workflow, remote control, CLI action or mobile action is permitted from this lane.",
                ),
            ),
            FrameworkAdapter(
                id="iris-mini",
                label="IRIS-Mini",
                runtime="typescript-service",
                category="coding",
                integration_batch=4,
                owner_commander="Igris",
                license="Custom restrictive licence (personal/educational only; not SPDX Apache-2.0)",
                source_url="https://github.com/IRISX-AI/IRIS-Mini",
                purpose="Reserved for CLI developer-workflow capability review only while its restrictive licence is unresolved.",
                capabilities=("CLI workflow plans", "Filesystem-action boundary", "Local developer UX review"),
                activation_boundary="sandboxed",
                implementation_status="license-review-required",
                guardrails=(
                    "Do not copy, install, link, bundle or invoke upstream source without a documented compatible-use decision.",
                    "Terminal, filesystem and project actions remain disabled until their own approval-gated adapter is reviewed.",
                ),
            ),
            FrameworkAdapter(
                id="iris-zero",
                label="IRIS-Zero",
                runtime="typescript-service",
                category="automation",
                integration_batch=4,
                owner_commander="Nox",
                license="Unverified — README claims MIT; no repository LICENSE file at review",
                source_url="https://github.com/IRISX-AI/IRIS-Zero",
                purpose="Reserved for local terminal, voice and project-automation capability review only while licence evidence is unresolved.",
                capabilities=("Offline terminal planning", "Voice workflow boundary", "Project-automation review"),
                activation_boundary="sandboxed",
                implementation_status="license-review-required",
                guardrails=(
                    "Do not copy, install, link, bundle or invoke upstream source until a valid licence file and terms are verified.",
                    "No terminal command, voice capture, model download, filesystem action or automation may begin from this lane.",
                ),
            ),
            FrameworkAdapter(
                id="zoey",
                label="Zoey",
                runtime="rust-cli",
                category="orchestration",
                integration_batch=4,
                owner_commander="Ashborn",
                license="MIT",
                source_url="https://github.com/Agent-Zoey/Zoey",
                purpose="Reserved for privacy-first Rust local-agent framework and capability-sandbox review.",
                capabilities=("Rust local-agent patterns", "Privacy-first architecture", "Capability sandbox review"),
                activation_boundary="sandboxed",
                guardrails=(
                    "Do not install a Rust binary, start a service, enable voice or configure a provider in this dry run.",
                    "Keep experiments reversible, locally isolated and below Jinwoo's approval, memory and audit boundaries.",
                ),
            ),
            FrameworkAdapter(
                id="iris-ai",
                label="IRIS-AI",
                runtime="desktop-client",
                category="reference",
                integration_batch=4,
                owner_commander="Ashborn",
                license="Custom source-available agreement; proprietary core excluded",
                source_url="https://github.com/IRISX-AI/IRIS-AI",
                purpose="Reference-only inspiration for public desktop voice, memory, vision and workflow UX; no upstream code path is permitted.",
                capabilities=("Desktop UX reference", "Voice/memory UX reference", "Vision workflow reference"),
                activation_boundary="reference-only",
                implementation_status="reference-only",
                guardrails=(
                    "Do not copy, link, bundle, install or invoke any IRIS-AI source, hidden core, backend or runtime.",
                    "Build any approved Jinwoo feature independently from high-level public product observations only.",
                ),
            ),
            FrameworkAdapter(
                id="iris-x",
                label="IRIS-X",
                runtime="mobile-client",
                category="reference",
                integration_batch=4,
                owner_commander="Ashborn",
                license="Dual licence: public UI shell MIT; proprietary engine and commercial features restricted",
                source_url="https://github.com/IRISX-AI/IRIS-X",
                purpose="Reference-only inspiration for a future mobile companion UX; the proprietary engine is outside Jinwoo scope.",
                capabilities=("Mobile companion UX reference", "Voice interaction reference", "Visual-context UX reference"),
                activation_boundary="reference-only",
                implementation_status="reference-only",
                guardrails=(
                    "Do not copy, link, bundle, install or invoke proprietary engine, mobile execution or commercial-only functionality.",
                    "Treat the public UI shell as reference-only for this project unless a separate compatible-source decision is approved.",
                ),
            ),
            FrameworkAdapter(
                id="jinwoo-native-control-audit",
                label="Jinwoo Native Control & Audit Review",
                runtime="builtin",
                category="governance",
                integration_batch=3,
                owner_commander="Jinwoo",
                license="Original project code",
                source_url=None,
                purpose="Active zero-side-effect local review of capacity, adapter, licence, workspace and audit boundaries.",
                native_adapter=True,
                implementation_status="active",
                guardrails=(
                    "The review reports local control-plane state only and cannot enable adapters or execute tools.",
                ),
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
