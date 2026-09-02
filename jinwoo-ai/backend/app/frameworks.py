"""Controlled adapter registry for optional multi-agent frameworks.

Jinwoo's local mission engine remains the one canonical orchestrator. An
installed package or sidecar never receives a mission automatically and cannot
bypass the policy, approval, workspace, or audit boundaries owned by Jinwoo.

Batches 01–08 contain owner-requested integration lanes. Their adapter
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
        "rust-cli", "desktop-client", "mobile-client", "skill-catalog",
    ]
    category: Literal[
        "orchestration", "workflow", "coding", "research", "web-collection", "memory", "automation", "security",
        "governance", "computer-use", "reference", "media",
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
        "active", "contract-ready", "license-review-required", "source-review-required", "reference-only", "archived-upstream", "queued",
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
        elif self.implementation_status == "source-review-required":
            readiness = "an exact upstream source and licence review are required before any adapter work"
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
        elif self.implementation_status == "source-review-required":
            policy_outcome = "approval-required" if decision.requires_approval else "safe-plan"
            summary = "A source-intake boundary was prepared. No upstream repository, runtime, tool or capability has been selected or invoked."
            steps = [
                "Obtain the exact upstream URL, immutable version and licence before any source or adapter review.",
                "Do not infer a repository from a product name or install an unreviewed package, skill pack, plugin or service.",
                "Keep the requested capability inside Jinwoo policy, workspace, approval and audit boundaries after source verification.",
            ]
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
            # Owner-requested specialist skills and toolkits batch 5. These are
            # source-reviewed capability contracts, not installed skill packs or
            # executable tool grants. CapCut-Patcher is deliberately excluded: no
            # DRM, licence-bypass or password-protected patcher is a Jinwoo lane.
            FrameworkAdapter(
                id="ai-video-editor",
                label="AI Video Editor (MartinDelophy)",
                runtime="desktop-client",
                category="media",
                integration_batch=5,
                owner_commander="Tusk",
                license="MIT",
                source_url="https://github.com/MartinDelophy/ai-video-editor",
                purpose="Reserved for lawful local timeline-edit, caption and voiceover workflow proposals.",
                capabilities=("Timeline-edit plans", "Caption/voiceover workflow review", "Local media-pipeline design"),
                activation_boundary="sandboxed",
                guardrails=(
                    "Use only user-owned or explicitly authorised local media; do not download, stream, rip or process protected content.",
                    "Do not invoke an editor, render, model download, media tool, file write or upload without a separate visible approval.",
                ),
            ),
            FrameworkAdapter(
                id="ai-video-editor-pipeline",
                label="AI Video Editor Pipeline (mazsola2k)",
                runtime="python",
                category="media",
                integration_batch=5,
                owner_commander="Tusk",
                license="MIT",
                source_url="https://github.com/mazsola2k/ai-video-editor",
                purpose="Reserved for lawful vision-assisted edit, timeline and export-pipeline proposals.",
                capabilities=("Vision-assisted edit plans", "Timeline/pipeline review", "Export-boundary design"),
                activation_boundary="sandboxed",
                guardrails=(
                    "Use only authorised local media and do not run a render, DaVinci integration, external model or filesystem action in a dry run.",
                    "Do not upload or publish to YouTube, Instagram, Facebook or any third-party service without a separate explicit approval.",
                ),
            ),
            FrameworkAdapter(
                id="watch-video-skill",
                label="Watch Video Skill",
                runtime="skill-catalog",
                category="media",
                integration_batch=5,
                owner_commander="Tusk",
                license="MIT",
                source_url="https://github.com/Newuxtreme/watch-video-skill",
                purpose="Reserved for user-authorised local video-analysis, feedback and transcript workflow proposals.",
                capabilities=("Local video-analysis plans", "Visual-feedback outlines", "Transcript/frame workflow review"),
                activation_boundary="sandboxed",
                guardrails=(
                    "Do not fetch, download or copy videos from URLs or platforms; analyse only a user-supplied, authorised local file after approval.",
                    "Do not invoke ffmpeg, Whisper, yt-dlp, a model, a browser or a filesystem write from this dry run.",
                ),
            ),
            FrameworkAdapter(
                id="videodb-skills",
                label="VideoDB Skills",
                runtime="python",
                category="media",
                integration_batch=5,
                owner_commander="Tusk",
                license="MIT",
                source_url="https://github.com/video-db/skills",
                purpose="Reserved for video ingest, understanding, search, edit and stream capability-contract review.",
                capabilities=("Video workflow contracts", "Search/edit pipeline review", "Retention and stream boundary"),
                activation_boundary="sandboxed",
                guardrails=(
                    "Do not start a VideoDB service, send an API key, ingest media, stream video or connect to a hosted account.",
                    "Any future media retention, edit, export or sharing step must use user-authorised content and a separate approval.",
                ),
            ),
            FrameworkAdapter(
                id="anthropic-cybersecurity-skills",
                label="Anthropic Cybersecurity Skills (community)",
                runtime="skill-catalog",
                category="security",
                integration_batch=5,
                owner_commander="Greed",
                license="Apache-2.0",
                source_url="https://github.com/mukul975/Anthropic-Cybersecurity-Skills",
                purpose="Reserved for defensive standards mapping, threat modelling and secure-configuration review proposals.",
                capabilities=("Defensive standards mapping", "Threat-model outlines", "Security-control review"),
                activation_boundary="read-only",
                guardrails=(
                    "Use only defensive governance, mitigation, secure configuration and authorised posture-review guidance.",
                    "Do not enable target enumeration, scanning, exploitation, malware, persistence, credential access, phishing, evasion or exfiltration.",
                ),
            ),
            FrameworkAdapter(
                id="anthropic-skills",
                label="Anthropic Skills",
                runtime="skill-catalog",
                category="workflow",
                integration_batch=5,
                owner_commander="Jima",
                license="Unverified repository licence; third-party notices include GPL-3.0 components",
                source_url="https://github.com/anthropics/skills",
                purpose="Reserved for document, spreadsheet and repeatable-workflow capability review pending a component-level licence decision.",
                capabilities=("Document-workflow review", "Spreadsheet/report planning", "Dynamic-skill boundary"),
                activation_boundary="approval-required",
                implementation_status="license-review-required",
                guardrails=(
                    "Do not copy, install, bundle or execute skill scripts or third-party components until a component-level licence review is complete.",
                    "Document, PDF, DOCX or XLSX generation remains a proposal until file creation, retention and user approval are separately designed.",
                ),
            ),
            FrameworkAdapter(
                id="ai-research-skills",
                label="AI Research SKILLs",
                runtime="skill-catalog",
                category="research",
                integration_batch=5,
                owner_commander="Blades",
                license="MIT",
                source_url="https://github.com/Orchestra-Research/AI-Research-SKILLs",
                purpose="Reserved for reproducible AI research, evaluation, infrastructure and paper-writing workflow proposals.",
                capabilities=("Research-plan design", "Evaluation workflow review", "Paper/artifact outlines"),
                activation_boundary="sandboxed",
                guardrails=(
                    "Do not launch training, distributed infrastructure, model downloads, remote datasets, experiments or provider calls in a dry run.",
                    "Require source attribution, local-retention decisions and approval before any later research execution or file production.",
                ),
            ),
            FrameworkAdapter(
                id="addy-osmani-agent-skills",
                label="Addy Osmani Agent Skills",
                runtime="skill-catalog",
                category="coding",
                integration_batch=5,
                owner_commander="Igris",
                license="MIT",
                source_url="https://github.com/addyosmani/agent-skills",
                purpose="Reserved for API design, UI engineering and testing-pipeline capability proposals.",
                capabilities=("API-design review", "UI-engineering plans", "Testing-pipeline proposals"),
                activation_boundary="sandboxed",
                guardrails=(
                    "Do not install or execute a skill, hook, script, plugin or IDE integration from this lane.",
                    "Keep code changes, tests, commands, dependencies and files inside Igris's future approval-gated sandbox path.",
                ),
            ),
            FrameworkAdapter(
                id="wordpress-agent-skills",
                label="WordPress Agent Skill Prototypes",
                runtime="typescript-mcp",
                category="coding",
                integration_batch=5,
                owner_commander="Igris",
                license="Unverified — no repository LICENSE file at review; upstream labels these as beta prototypes",
                source_url="https://github.com/Automattic/wordpress-agent-skills",
                purpose="Reserved for WordPress theme/site and IDE/MCP workflow review pending licence and deployment review.",
                capabilities=("WordPress site-plan review", "IDE/MCP boundary", "Skill-distribution review"),
                activation_boundary="sandboxed",
                implementation_status="license-review-required",
                guardrails=(
                    "Do not install a plugin, start WordPress Studio/CLI/MCP, create a site or execute an IDE tool from this lane.",
                    "Do not share, sync, deploy or publish a site; future local preview and delivery actions need separate explicit approval.",
                ),
            ),
            FrameworkAdapter(
                id="composio",
                label="Composio",
                runtime="python",
                category="automation",
                integration_batch=5,
                owner_commander="Fang",
                license="MIT",
                source_url="https://github.com/ComposioHQ/composio",
                purpose="Reserved for explicit connector, tool-search, authentication and workbench policy-contract review.",
                capabilities=("Connector-policy design", "OAuth boundary review", "External-action allowlists"),
                activation_boundary="approval-required",
                guardrails=(
                    "Do not install a toolkit, authenticate an account, request OAuth, store a token or discover/activate an external connector.",
                    "Future GitHub, Slack, Jira, Notion, Gmail, Salesforce or other service actions need an individual allowlist and per-action approval.",
                ),
            ),
            FrameworkAdapter(
                id="stagehand",
                label="Stagehand",
                runtime="typescript-service",
                category="automation",
                integration_batch=5,
                owner_commander="Nox",
                license="MIT",
                source_url="https://github.com/browserbase/stagehand",
                purpose="Reserved for approval-bound browser-agent capability planning.",
                capabilities=("Browser workflow plans", "Page-action preview", "Web automation boundary"),
                activation_boundary="sandboxed",
                guardrails=(
                    "Do not launch a browser, fetch a URL, use cookies, access a logged-in session, fill a form or transmit workspace data.",
                    "Future browsing requires the Tank public-target gate plus exact target/action preview, SSRF controls and per-action approval.",
                ),
            ),
            FrameworkAdapter(
                id="langchain-community",
                label="LangChain Community Tools",
                runtime="python",
                category="workflow",
                integration_batch=5,
                owner_commander="Fang",
                license="MIT",
                source_url="https://github.com/langchain-ai/langchain",
                python_module="langchain_community",
                purpose="Reserved for tool, retrieval and structured-workflow interface review.",
                capabilities=("Tool-interface review", "Retrieval boundary design", "Structured-workflow contracts"),
                activation_boundary="sandboxed",
                guardrails=(
                    "Do not import or invoke a community tool, search service, retriever, calculator, filesystem or network integration from this lane.",
                    "Every future tool needs an individual source, privacy, workspace, network and approval review rather than a blanket enablement.",
                ),
            ),
            FrameworkAdapter(
                id="official-mcp-servers",
                label="Official MCP Servers",
                runtime="typescript-mcp",
                category="automation",
                integration_batch=5,
                owner_commander="Fang",
                license="Mixed Apache-2.0/MIT code transition; CC-BY-4.0 documentation",
                source_url="https://github.com/modelcontextprotocol/servers",
                purpose="Reserved for individual MCP capability-manifest and server-boundary review.",
                capabilities=("MCP capability manifests", "Server allowlist design", "Data-boundary review"),
                activation_boundary="sandboxed",
                implementation_status="license-review-required",
                guardrails=(
                    "Do not install, configure, start or connect any MCP server, including filesystem, database, search, fetch or browser capabilities.",
                    "Each future MCP server needs its own version, licence, transport, data scope, network policy, workspace confinement and approval review.",
                ),
            ),
            FrameworkAdapter(
                id="awesome-mcp-servers",
                label="Awesome MCP Servers",
                runtime="skill-catalog",
                category="reference",
                integration_batch=5,
                owner_commander="Fang",
                license="MIT list; every listed third-party MCP server needs its own review",
                source_url="https://github.com/punkpeye/awesome-mcp-servers",
                purpose="Reference-only catalogue for future individual MCP source intake.",
                capabilities=("MCP discovery reference", "Individual-source intake", "Capability comparison"),
                activation_boundary="reference-only",
                implementation_status="reference-only",
                guardrails=(
                    "Do not treat inclusion in a community list as trust, a licence grant or permission to install a server.",
                    "No Docker, filesystem, Spotify, Figma, crypto, browser or other listed integration is enabled from this reference.",
                ),
            ),
            FrameworkAdapter(
                id="metagpt",
                label="MetaGPT",
                runtime="python",
                category="orchestration",
                integration_batch=5,
                owner_commander="Beru",
                license="MIT",
                source_url="https://github.com/geekan/MetaGPT",
                python_module="metagpt",
                purpose="Reserved for product-manager, architect and QA collaboration-pattern review.",
                capabilities=("Role-collaboration plans", "Software-company workflow review", "Artifact handoff design"),
                activation_boundary="sandboxed",
                guardrails=(
                    "Beru and Jinwoo retain the single mission state machine; do not create an autonomous software company or background worker loop.",
                    "Do not start agents, providers, tools, file writes, commands or project generation without separate approval-gated implementation.",
                ),
            ),
            FrameworkAdapter(
                id="autogen",
                label="Microsoft AutoGen",
                runtime="python",
                category="orchestration",
                integration_batch=5,
                owner_commander="Bellion",
                license="MIT for code (LICENSE-CODE); CC-BY-4.0 documentation",
                source_url="https://github.com/microsoft/autogen",
                python_module="autogen",
                purpose="Reserved for event-driven and conversational multi-agent flow contract review.",
                capabilities=("Event-driven flow plans", "Conversational handoff review", "Typed agent-contract design"),
                activation_boundary="sandboxed",
                guardrails=(
                    "Bellion and Jinwoo retain routing, policy, provider choice, workspace confinement and approvals; do not start an independent agent conversation loop.",
                    "Do not activate model clients, tools, code execution or event listeners from this dry run.",
                ),
            ),
            FrameworkAdapter(
                id="pydantic-ai",
                label="Pydantic AI",
                runtime="python",
                category="workflow",
                integration_batch=5,
                owner_commander="Igris",
                license="MIT",
                source_url="https://github.com/pydantic/pydantic-ai",
                python_module="pydantic_ai",
                purpose="Reserved for typed production-agent, structured-output and evaluation-contract review.",
                capabilities=("Typed agent contracts", "Structured-output review", "Evaluation boundary design"),
                activation_boundary="sandboxed",
                guardrails=(
                    "Do not install a model provider, start a tool, generate a file or make a network call from this lane.",
                    "Future use must preserve FastAPI schemas, local-provider preference, cloud consent and Jinwoo approval/audit ownership.",
                ),
            ),
            FrameworkAdapter(
                id="scientific-agent-skills",
                label="Scientific Agent Skills",
                runtime="skill-catalog",
                category="research",
                integration_batch=5,
                owner_commander="Tank",
                license="MIT",
                source_url="https://github.com/K-Dense-AI/scientific-agent-skills",
                purpose="Reserved for reproducible scientific literature, data-analysis and database-access planning.",
                capabilities=("Scientific research plans", "Reproducibility checklists", "Database-access boundary review"),
                activation_boundary="sandboxed",
                guardrails=(
                    "Do not connect to a scientific database, upload data, run wet-lab or computational experiment, or provide unauthorised access from this lane.",
                    "Future research must use lawful sources, attribution, approval, local retention controls and applicable safety review.",
                ),
            ),
            FrameworkAdapter(
                id="open-autoglm",
                label="Open-AutoGLM",
                runtime="python",
                category="computer-use",
                integration_batch=5,
                owner_commander="Nox",
                license="Apache-2.0",
                source_url="https://github.com/zai-org/Open-AutoGLM",
                python_module="phone_agent",
                purpose="Reserved for a separate future Android companion screen-understanding and phone-action design phase.",
                capabilities=("Mobile screen-understanding plans", "Device-action preview", "Android permission-model review"),
                activation_boundary="sandboxed",
                implementation_status="queued",
                guardrails=(
                    "This is outside desktop V1: do not install a phone agent, connect a device, enable Accessibility, capture a screen or perform mobile input.",
                    "Any future Android action needs device-local consent, exact action preview, per-action approval and a separate companion-app safety design.",
                ),
            ),
            FrameworkAdapter(
                id="500-ai-agent-projects",
                label="500 AI Agents Projects",
                runtime="skill-catalog",
                category="reference",
                integration_batch=5,
                owner_commander="Ashborn",
                license="MIT catalogue; linked projects require individual source review",
                source_url="https://github.com/ashishpatel26/500-AI-Agents-Projects",
                purpose="Reference-only catalogue for use-case comparison and future individually reviewed blueprint intake.",
                capabilities=("Use-case reference", "Framework comparison", "Blueprint-intake review"),
                activation_boundary="reference-only",
                implementation_status="reference-only",
                guardrails=(
                    "Do not clone, install, execute or inherit permissions from any linked project in the catalogue.",
                    "Every selected example must pass independent licence, dependency, privacy, tool and approval review before any implementation work.",
                ),
            ),
            FrameworkAdapter(
                id="envagent-source-intake",
                label="EnvAgent (source intake pending)",
                runtime="skill-catalog",
                category="coding",
                integration_batch=5,
                owner_commander="Igris",
                license="Unverified — exact GitHub source and licence required",
                source_url=None,
                purpose="Records the requested secure sandbox, runtime-bug review and code-execution capability without selecting an ambiguous upstream project.",
                capabilities=("Sandbox architecture request", "Runtime-bug review plan", "Test-isolation design"),
                activation_boundary="sandboxed",
                implementation_status="source-review-required",
                guardrails=(
                    "Do not infer an EnvAgent repository from its name or install any package, container or code runner before the owner supplies an exact source URL.",
                    "Any later code execution must use a separately reviewed disposable sandbox with no host credentials, network or workspace write access by default.",
                ),
            ),
            # Owner-requested interaction-design batch 6. The upstream projects
            # are represented as capability contracts only. Jinwoo does not copy
            # their source, request camera access, load CDN scripts, or control a
            # desktop, phone, physical tool or robotic device.
            FrameworkAdapter(
                id="barehands",
                label="Barehands Gesture Interface",
                runtime="desktop-client",
                category="computer-use",
                integration_batch=6,
                owner_commander="Nox",
                license="AGPL-3.0-or-later",
                source_url="https://github.com/jaredrhod/barehands",
                purpose="Reserved for a future local hand-gesture, spatial-board and accessibility interaction design review.",
                capabilities=("Gesture interaction design", "Spatial-board safety review", "Camera-consent UX planning"),
                activation_boundary="sandboxed",
                implementation_status="license-review-required",
                guardrails=(
                    "Do not copy, bundle, install or run upstream code until AGPL-3.0 compatibility, notices and deployment terms are approved.",
                    "Do not request webcam permission, load MediaPipe/Three.js CDNs, read/write local state files, call localhost or trigger board actions.",
                    "Any later camera route needs an explicit in-app consent, camera-off default, local-only processing evidence, visible gesture preview and an emergency stop.",
                ),
            ),
            FrameworkAdapter(
                id="ultron-orb-ui",
                label="Ultron Orb UI (Sagar Builds)",
                runtime="desktop-client",
                category="computer-use",
                integration_batch=6,
                owner_commander="Tusk",
                license="MIT",
                source_url="https://github.com/SAGAR-TAMANG/ultron-by-sagar-builds",
                purpose="Reserved for independently designed orb, HUD and optional hand-gesture interaction pattern review.",
                capabilities=("Orb/HUD design patterns", "Gesture-control UX review", "Visual system-status concepts"),
                activation_boundary="sandboxed",
                guardrails=(
                    "This registry does not copy the Next.js, Three.js or MediaPipe implementation or use Iron Man/JARVIS assets, names or trade dress.",
                    "Do not request camera permission, start hand tracking, connect an Android device or permit an autonomous device action from this lane.",
                    "Any future interaction implementation must be original, camera-off by default, consented, locally processed where feasible and individually approval-gated.",
                ),
            ),
            FrameworkAdapter(
                id="physical-cutter-safety-intake",
                label="Physical Cutter / Robotics Safety Intake",
                runtime="skill-catalog",
                category="computer-use",
                integration_batch=6,
                owner_commander="Nox",
                license="No upstream or machine documentation selected; hardware safety review required",
                source_url=None,
                purpose="Records the owner-requested physical cutter or robotics concept without selecting hardware, a controller, firmware or a device protocol.",
                capabilities=("Hardware safety requirements", "Operator-consent design", "Device-isolation planning"),
                activation_boundary="sandboxed",
                implementation_status="source-review-required",
                guardrails=(
                    "Do not connect USB, serial, Bluetooth, Wi-Fi, GPIO, cameras, motors, blades, lasers, actuators or industrial control interfaces.",
                    "Do not generate a device-control route, bypass an interlock, remove a guard or perform any physical action from Jinwoo.",
                    "A later concept review needs the exact machine/manual, lawful use case, local operator, emergency stop, physical guarding, risk assessment and independent safety sign-off.",
                ),
            ),
            # Owner-requested Shadow Army multi-agent core batch 7. These are
            # local, non-executing integration contracts based on a metadata,
            # README and tree review. Jinwoo remains the sole mission engine.
            FrameworkAdapter(
                id="agent-swarm",
                label="Agent Swarm",
                runtime="python",
                category="orchestration",
                integration_batch=7,
                owner_commander="Bellion",
                license="MIT",
                source_url="https://github.com/jlulxy/agent-swarm",
                python_module="agent_swarm",
                purpose="Reserved for deliverable-driven, bounded specialist-collaboration patterns.",
                capabilities=("Specialist collaboration patterns", "Shared-memory boundary review", "Deliverable verification"),
                activation_boundary="sandboxed",
                guardrails=(
                    "Do not install the upstream backend/frontend, start its server, or create an independent memory store.",
                    "Bellion retains routing, worker limits, approval, local-provider selection and audit ownership.",
                ),
            ),
            FrameworkAdapter(
                id="roma",
                label="ROMA",
                runtime="python",
                category="orchestration",
                integration_batch=7,
                owner_commander="Ashborn",
                license="Unverified — no SPDX licence was detected during source intake",
                source_url="https://github.com/sentient-agi/ROMA",
                python_module="roma_dspy",
                purpose="Reserved for recursive task-tree, aggregation and Planner/Executor/Verifier pattern review.",
                capabilities=("Recursive task-tree planning", "Context aggregation patterns", "Verifier handoff design"),
                activation_boundary="sandboxed",
                implementation_status="license-review-required",
                guardrails=(
                    "Do not copy, install, start or invoke ROMA until an explicit compatible licence and dependency review is complete.",
                    "Do not enable MCP servers, Docker, toolkits, crypto examples, models or background execution from this lane.",
                ),
            ),
            FrameworkAdapter(
                id="open-multi-agent",
                label="Open Multi-Agent",
                runtime="typescript-service",
                category="orchestration",
                integration_batch=7,
                owner_commander="Bellion",
                license="MIT",
                source_url="https://github.com/open-multi-agent/open-multi-agent",
                purpose="Reserved for dynamic DAG, budget, consensus, approval and recovery-pattern review.",
                capabilities=("Dynamic DAG planning", "Consensus/recovery patterns", "Budget and approval design"),
                activation_boundary="sandboxed",
                guardrails=(
                    "Do not install Node packages, start a process, configure providers or let a dynamic DAG create unreviewed tools.",
                    "Jinwoo's native graph retains the final approval edge, workspace boundary and external-runtime lock.",
                ),
            ),
            FrameworkAdapter(
                id="awesome-agent-orchestration",
                label="Awesome Agent Orchestration",
                runtime="skill-catalog",
                category="reference",
                integration_batch=7,
                owner_commander="Kaisel",
                license="Unverified — GitHub metadata reports NOASSERTION",
                source_url="https://github.com/vivy-yi/awesome-agent-orchestration",
                purpose="Reference-only catalogue for individually reviewed orchestration sources and pattern comparison.",
                capabilities=("Framework discovery", "Pattern comparison", "Individual source-intake backlog"),
                activation_boundary="reference-only",
                implementation_status="reference-only",
                guardrails=(
                    "Do not treat an awesome-list entry as a trust signal, licence grant, installation instruction or tool permission.",
                    "Every downstream framework needs a separately pinned source, licence, security and local compatibility review.",
                ),
            ),
            FrameworkAdapter(
                id="microsoft-agent-framework",
                label="Microsoft Agent Framework",
                runtime="python",
                category="workflow",
                integration_batch=7,
                owner_commander="Jinwoo",
                license="MIT",
                source_url="https://github.com/microsoft/agent-framework",
                python_module="agent_framework",
                purpose="Reserved for typed workflows, middleware, durable handoffs and human-in-the-loop pattern review.",
                capabilities=("Typed workflow patterns", "Middleware/governance design", "Durable human-in-loop handoffs"),
                activation_boundary="sandboxed",
                guardrails=(
                    "Do not install providers, enable hosted deployment, telemetry export, tools, workflows or persistence from this lane.",
                    "Use only a future local, version-pinned adapter that keeps Jinwoo policy, audit, memory and approval controls authoritative.",
                ),
            ),
            # Owner-requested geospatial visualisation intake batch 8. The
            # upstream MIT source explicitly excludes third-party live data and
            # assets; this record therefore has no data feed, map or tracker.
            FrameworkAdapter(
                id="gods-eye-view",
                label="God's Eye View — Geospatial Safety Intake",
                runtime="desktop-client",
                category="reference",
                integration_batch=8,
                owner_commander="Tank",
                license=(
                    "MIT source code only; third-party live data, datasets and 3D assets require separate terms/licence review"
                ),
                source_url="https://github.com/bilawalsidhu/gods-eye-view",
                purpose=(
                    "Reserved for privacy-aware, non-live geospatial visualisation, source-attribution and public-data boundary review."
                ),
                capabilities=(
                    "Static geospatial visualisation concepts",
                    "Source attribution and provenance UX review",
                    "Public-data privacy and safety boundary planning",
                ),
                activation_boundary="sandboxed",
                implementation_status="license-review-required",
                guardrails=(
                    "Do not copy, bundle, install or invoke upstream code until source-code licence, third-party data, asset, attribution and deployment terms are individually reviewed.",
                    "Do not fetch, display or track live flights, vessels, satellites, traffic, radio, cameras, places or other location-linked feeds from this lane.",
                    "Do not request camera, microphone, screen, browser location or device permissions, and do not create an OSINT, surveillance or individual-tracking workflow.",
                    "Do not configure Cesium, Google Maps, OpenAI, OpenSky, AIS, map tiles, API keys, proxy routes, sockets or external services from this record.",
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
