"""Zero-side-effect native control-plane review for all controlled integration lanes.

The review is intentionally local and descriptive: it validates Jinwoo's own
invariants and reports whether any registry state needs attention. It never
starts an optional runtime, opens a network connection, reads workspace files,
or changes policy/approval settings.
"""

from __future__ import annotations

from .army import army_summary
from .schemas import ControlReview, ControlReviewCheck, FrameworkStatus, WorkspaceStatus


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
_LICENSE_REVIEW_IDS = {"firecrawl", "trufflehog", "iris-go", "iris-mini", "iris-zero"}
_REFERENCE_ONLY_IDS = {"iris-ai", "iris-x"}
_ARCHIVED_UPSTREAM_IDS = {"bytebot"}


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
    licence_gates = [by_id[framework_id] for framework_id in _LICENSE_REVIEW_IDS if framework_id in by_id]
    reference_only = [by_id[framework_id] for framework_id in _REFERENCE_ONLY_IDS if framework_id in by_id]
    archived_upstream = [by_id[framework_id] for framework_id in _ARCHIVED_UPSTREAM_IDS if framework_id in by_id]

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
            ),
            detail=(
                "Firecrawl, TruffleHog, IRIS-GO, IRIS-Mini and IRIS-Zero stay licence-review-required; "
                "IRIS-AI and IRIS-X stay reference-only; Bytebot stays archived-upstream."
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
