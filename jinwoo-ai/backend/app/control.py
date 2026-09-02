"""Zero-side-effect native control-plane review for all controlled integration lanes.

The review is intentionally local and descriptive: it validates Jinwoo's own
invariants and reports whether any registry state needs attention. It never
starts an optional runtime, opens a network connection, reads workspace files,
or changes policy/approval settings.
"""

from __future__ import annotations

from .army import army_summary
from .schemas import ControlReview, ControlReviewCheck, FrameworkStatus, WorkspaceStatus
from .skill_intakes import BATCH_ELEVEN_SKILL_INTAKES


_EXPECTED_CAPACITY = {
    "departments": 15,
    "sub_departments": 45,
    "logical_agents": 450,
    "worker_slots": 1_350,
}
_BATCH_THREE_IDS = {"mem0", "openclaw", "trufflehog", "gitleaks", "jinwoo-native-control-audit"}
_BATCH_FOUR_IDS = {
    "goose", "orkas", "bytebot", "open-desktop", "hermes-agent", "openagent", "iris-go", "iris-mini", "iris-zero", "zoey",
    "iris-ai", "iris-x",
}
_BATCH_FIVE_IDS = {
    "ai-video-editor", "ai-video-editor-pipeline", "watch-video-skill", "videodb-skills", "anthropic-cybersecurity-skills",
    "anthropic-skills", "ai-research-skills", "addy-osmani-agent-skills", "wordpress-agent-skills", "composio", "stagehand",
    "langchain-community", "official-mcp-servers", "awesome-mcp-servers", "metagpt", "autogen", "pydantic-ai",
    "scientific-agent-skills", "open-autoglm", "500-ai-agent-projects", "envagent-source-intake",
}
_BATCH_SIX_IDS = {"barehands", "ultron-orb-ui", "physical-cutter-safety-intake"}
_BATCH_SEVEN_IDS = {"agent-swarm", "roma", "open-multi-agent", "awesome-agent-orchestration", "microsoft-agent-framework"}
_BATCH_EIGHT_IDS = {"gods-eye-view"}
_BATCH_NINE_IDS = {"nexa-ai-assistant"}
_BATCH_TEN_IDS = {"jarvis-one-click-setup", "pc-hand-gesture-control"}
_BATCH_ELEVEN_IDS = {spec.id for spec in BATCH_ELEVEN_SKILL_INTAKES}
_LICENSE_REVIEW_IDS = {
    "firecrawl", "trufflehog", "iris-go", "iris-mini", "iris-zero", "anthropic-skills", "wordpress-agent-skills",
    "official-mcp-servers", "barehands", "roma", "gods-eye-view",
}
_REFERENCE_ONLY_IDS = {"iris-ai", "iris-x", "awesome-mcp-servers", "500-ai-agent-projects", "awesome-agent-orchestration"}
_ARCHIVED_UPSTREAM_IDS = {"bytebot"}
_QUEUED_IDS = {"open-autoglm"}
_SOURCE_REVIEW_IDS = {
    "envagent-source-intake", "physical-cutter-safety-intake", "nexa-ai-assistant",
    "jarvis-one-click-setup", "pc-hand-gesture-control",
}


def build_control_review(
    *,
    framework_statuses: list[FrameworkStatus],
    workspace_status: WorkspaceStatus,
    audit_available: bool,
) -> ControlReview:
    """Return a local invariant report without changing any execution state."""

    by_id = {framework.id: framework for framework in framework_statuses}
    capacity = army_summary()
    canonical_ids = {framework.id for framework in framework_statuses if framework.state.value == "canonical"}
    external_adapters = [framework for framework in framework_statuses if framework.state.value != "canonical"]
    batch_three = [by_id[framework_id] for framework_id in _BATCH_THREE_IDS if framework_id in by_id]
    batch_four = [by_id[framework_id] for framework_id in _BATCH_FOUR_IDS if framework_id in by_id]
    batch_five = [by_id[framework_id] for framework_id in _BATCH_FIVE_IDS if framework_id in by_id]
    batch_six = [by_id[framework_id] for framework_id in _BATCH_SIX_IDS if framework_id in by_id]
    batch_seven = [by_id[framework_id] for framework_id in _BATCH_SEVEN_IDS if framework_id in by_id]
    batch_eight = [by_id[framework_id] for framework_id in _BATCH_EIGHT_IDS if framework_id in by_id]
    batch_nine = [by_id[framework_id] for framework_id in _BATCH_NINE_IDS if framework_id in by_id]
    batch_ten = [by_id[framework_id] for framework_id in _BATCH_TEN_IDS if framework_id in by_id]
    batch_eleven = [by_id[framework_id] for framework_id in _BATCH_ELEVEN_IDS if framework_id in by_id]
    licence_gates = [by_id[framework_id] for framework_id in _LICENSE_REVIEW_IDS if framework_id in by_id]
    reference_only = [by_id[framework_id] for framework_id in _REFERENCE_ONLY_IDS if framework_id in by_id]
    archived_upstream = [by_id[framework_id] for framework_id in _ARCHIVED_UPSTREAM_IDS if framework_id in by_id]
    queued = [by_id[framework_id] for framework_id in _QUEUED_IDS if framework_id in by_id]
    source_review = [by_id[framework_id] for framework_id in _SOURCE_REVIEW_IDS if framework_id in by_id]

    checks = [
        ControlReviewCheck(
            id="army-capacity",
            label="Final Army capacity",
            passed=capacity == _EXPECTED_CAPACITY,
            detail=(
                "15 commanders, 45 sub-departments, 450 logical agents and 1,350 worker slots are derived without spawning them."
                if capacity == _EXPECTED_CAPACITY
                else "The derived Army capacity differs from the final hierarchy and needs review."
            ),
        ),
        ControlReviewCheck(
            id="native-control",
            label="Native command ownership",
            passed=(
                canonical_ids == {"jinwoo-native", "jinwoo-native-control-audit"}
                and by_id.get("jinwoo-native") is not None
                and by_id["jinwoo-native"].execution_enabled
                and by_id.get("jinwoo-native-control-audit") is not None
                and by_id["jinwoo-native-control-audit"].execution_enabled
            ),
            detail="Jinwoo remains the canonical mission engine and the control/audit review remains a native local capability.",
        ),
        ControlReviewCheck(
            id="external-runtime-lock",
            label="External runtime lock",
            passed=bool(external_adapters) and all(not framework.execution_enabled for framework in external_adapters),
            detail="Every external adapter remains disabled; registry discovery never authorises execution.",
        ),
        ControlReviewCheck(
            id="batch-three-registry",
            label="Batch 03 integration inventory",
            passed=(
                len(batch_three) == len(_BATCH_THREE_IDS)
                and all(framework.integration_batch == 3 for framework in batch_three)
            ),
            detail="Mem0, OpenClaw, TruffleHog, Gitleaks and the native control/audit lane remain present and controlled.",
        ),
        ControlReviewCheck(
            id="batch-four-advanced-skills",
            label="Batch 04 advanced skill inventory",
            passed=(
                len(batch_four) == len(_BATCH_FOUR_IDS)
                and all(framework.integration_batch == 4 and not framework.execution_enabled for framework in batch_four)
            ),
            detail="All 12 owner-requested advanced skill lanes are registered, bounded and non-executing.",
        ),
        ControlReviewCheck(
            id="batch-five-specialist-skills",
            label="Batch 05 specialist skill inventory",
            passed=(
                len(batch_five) == len(_BATCH_FIVE_IDS)
                and all(framework.integration_batch == 5 and not framework.execution_enabled for framework in batch_five)
            ),
            detail="All 21 owner-requested specialist skill/toolkit lanes are registered as bounded, non-executing capabilities.",
        ),
        ControlReviewCheck(
            id="batch-six-interaction-safety",
            label="Batch 06 interaction-safety inventory",
            passed=(
                len(batch_six) == len(_BATCH_SIX_IDS)
                and all(framework.integration_batch == 6 and not framework.execution_enabled for framework in batch_six)
            ),
            detail="Barehands, Ultron Orb UI and the physical-hardware intake remain bounded, non-executing interaction concepts.",
        ),
        ControlReviewCheck(
            id="batch-seven-multi-agent-core",
            label="Batch 07 multi-agent core inventory",
            passed=(
                len(batch_seven) == len(_BATCH_SEVEN_IDS)
                and all(framework.integration_batch == 7 and not framework.execution_enabled for framework in batch_seven)
            ),
            detail=(
                "Agent Swarm, ROMA, Open Multi-Agent, Awesome Agent Orchestration and Microsoft Agent Framework "
                "are visible as bounded, non-executing Shadow Army integration lanes."
            ),
        ),
        ControlReviewCheck(
            id="batch-eight-geospatial-safety",
            label="Batch 08 geospatial-safety inventory",
            passed=(
                len(batch_eight) == len(_BATCH_EIGHT_IDS)
                and all(
                    framework.integration_batch == 8
                    and framework.implementation_status == "license-review-required"
                    and not framework.execution_enabled
                    for framework in batch_eight
                )
            ),
            detail=(
                "God's Eye View is a source/data/licence-gated geospatial reference; it has no map, live-feed, camera, location, "
                "tracking, voice or external-service runtime in Jinwoo."
            ),
        ),
        ControlReviewCheck(
            id="batch-nine-nexa-source-safety",
            label="Batch 09 NEXA source-safety inventory",
            passed=(
                len(batch_nine) == len(_BATCH_NINE_IDS)
                and all(
                    framework.integration_batch == 9
                    and framework.implementation_status == "source-review-required"
                    and framework.activation_boundary == "reference-only"
                    and not framework.execution_enabled
                    for framework in batch_nine
                )
            ),
            detail=(
                "NEXA AI Assistant remains a no-licence, configuration-risk source-review intake; no desktop, voice, vision, "
                "browser, device, model or automation runtime is present in Jinwoo."
            ),
        ),
        ControlReviewCheck(
            id="batch-ten-desktop-gesture-safety",
            label="Batch 10 desktop and gesture source-safety inventory",
            passed=(
                len(batch_ten) == len(_BATCH_TEN_IDS)
                and all(
                    framework.integration_batch == 10
                    and framework.implementation_status == "source-review-required"
                    and framework.activation_boundary == "reference-only"
                    and not framework.execution_enabled
                    for framework in batch_ten
                )
            ),
            detail=(
                "Jarvis One-Click Setup and Control PC Using Hand Gesture remain source-gated; no installer, provider, "
                "voice, camera, model, screen, mouse, keyboard, desktop, device or automation runtime is present in Jinwoo."
            ),
        ),
        ControlReviewCheck(
            id="batch-eleven-skill-catalogue-safety",
            label="Batch 11 skill-catalogue safety inventory",
            passed=(
                len(batch_eleven) == len(_BATCH_ELEVEN_IDS)
                and all(
                    framework.integration_batch == 11
                    and framework.implementation_status in {"source-review-required", "reference-only"}
                    and framework.activation_boundary == "reference-only"
                    and not framework.execution_enabled
                    for framework in batch_eleven
                )
            ),
            detail=(
                "Every Batch 11 source is a declared catalogue record only; no upstream SKILL.md, prompt, agent, installer, "
                "provider, browser, repository, model, desktop or device capability is loaded, spawned or granted permission."
            ),
        ),
        ControlReviewCheck(
            id="restricted-source-gates",
            label="Restricted source and licence gates",
            passed=(
                len(licence_gates) == len(_LICENSE_REVIEW_IDS)
                and all(
                    framework.implementation_status == "license-review-required" and not framework.execution_enabled
                    for framework in licence_gates
                )
                and len(reference_only) == len(_REFERENCE_ONLY_IDS)
                and all(
                    framework.implementation_status == "reference-only"
                    and framework.state.value == "reference-only"
                    and not framework.execution_enabled
                    for framework in reference_only
                )
                and len(archived_upstream) == len(_ARCHIVED_UPSTREAM_IDS)
                and all(
                    framework.implementation_status == "archived-upstream" and not framework.execution_enabled
                    for framework in archived_upstream
                )
                and len(queued) == len(_QUEUED_IDS)
                and all(
                    framework.implementation_status == "queued" and not framework.execution_enabled
                    for framework in queued
                )
                and len(source_review) == len(_SOURCE_REVIEW_IDS)
                and all(
                    framework.implementation_status == "source-review-required" and not framework.execution_enabled
                    for framework in source_review
                )
            ),
            detail=(
                "Licence gates remain on Firecrawl, TruffleHog, IRIS-GO/Mini/Zero, Anthropic Skills, WordPress skills, MCP Servers, Barehands and ROMA; "
                "NEXA, Jarvis, PC hand-gesture, Batch 11 skill catalogues and other source-intake, reference-only, archived, queued-mobile, orchestration-catalogue and physical-hardware boundaries remain locked."
            ),
        ),
        ControlReviewCheck(
            id="workspace-read-only",
            label="Workspace containment",
            passed=workspace_status.read_only,
            detail="Igris Workspace Guard is read-only whether or not a user-selected workspace is currently configured.",
        ),
        ControlReviewCheck(
            id="audit-availability",
            label="Local audit availability",
            passed=audit_available,
            detail="The local audit store was reachable; this review records only aggregate control metadata.",
        ),
    ]
    all_passed = all(check.passed for check in checks)
    return ControlReview(
        all_passed=all_passed,
        summary=(
            f"{len(checks)} local control checks passed. No external runtime or tool was invoked."
            if all_passed
            else "One or more local control checks need attention. No external runtime or tool was invoked."
        ),
        checks=checks,
    )
