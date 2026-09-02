import re
import sys
import tempfile
import unittest
from dataclasses import replace
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.army import army_summary, build_mission, needs_approval, select_commander
from app.control import build_control_review
from app.frameworks import frameworks
from app.memory import LocalMemoryStore
from app.policy import ActionClass, classify_action
from app.providers import ProviderError, ProviderGateway
from app.schemas import CoordinationPattern, ShadowArmyPlanRequest, WorkspaceStatus
from app.shadow_army import ShadowArmyPolicyError, ShadowArmyStore, build_shadow_army_plan, iter_logical_agent_ids
from app.skill_intakes import BATCH_ELEVEN_SKILL_INTAKES, BATCH_TWELVE_UPGRADE_INTAKES, source_intake_guardrails
from scripts.check_safe_intake import (
    CLEAN_ROOM_FILES,
    FORBIDDEN_MANIFEST_PACKAGES,
    RESTRICTED_RUNTIME_MODULES,
    scan as scan_safe_intake,
)
from app.settings import Settings


class ArmyRoutingTests(unittest.TestCase):
    def test_development_task_routes_to_igris(self) -> None:
        self.assertEqual(select_commander("Please fix this React build bug").id, "igris")

    def test_research_task_routes_to_tank(self) -> None:
        self.assertEqual(select_commander("Research local LLM options").id, "tank")

    def test_impactful_task_needs_approval(self) -> None:
        mission = build_mission("Delete the old output folder")
        self.assertTrue(mission.requires_approval)
        self.assertTrue(needs_approval("Delete the old output folder", select_commander("project task")))

    def test_code_analysis_does_not_need_approval(self) -> None:
        mission = build_mission("Analyze my React build error and propose a patch")
        self.assertFalse(mission.requires_approval)

    def test_logical_capacity_is_calculated_not_spawned(self) -> None:
        summary = army_summary()
        self.assertEqual(summary["departments"], 15)
        self.assertEqual(summary["sub_departments"], 45)
        self.assertEqual(summary["logical_agents"], 450)
        self.assertEqual(summary["worker_slots"], 1350)


class ShadowArmyCoreTests(unittest.TestCase):
    def test_full_logical_catalogue_is_present_without_started_workers(self) -> None:
        logical_ids = tuple(iter_logical_agent_ids())
        overview = ShadowArmyStore().overview()

        self.assertEqual(len(logical_ids), 450)
        self.assertEqual(len(set(logical_ids)), 450)
        self.assertEqual(overview.commanders, 15)
        self.assertEqual(overview.divisions, 45)
        self.assertEqual(overview.logical_agents, 450)
        self.assertEqual(overview.worker_slots, 1350)
        self.assertEqual(overview.active_runtime_workers, 0)
        self.assertEqual(overview.runtime_cap_per_mission, 3)
        self.assertTrue(overview.all_external_runtimes_disabled)

    def test_dependency_graph_is_a_bounded_visible_plan_not_a_runtime(self) -> None:
        plan = build_shadow_army_plan(
            ShadowArmyPlanRequest(
                prompt="Design a safe dependency graph for a React regression review",
                requested_logical_agents=450,
                coordination=CoordinationPattern.DEPENDENCY_GRAPH,
            )
        )

        self.assertEqual(plan.logical_agents_reserved, 450)
        self.assertEqual(plan.displayed_logical_agents, 10)
        self.assertEqual(len(plan.agents), 10)
        self.assertEqual(plan.runtime_worker_cap, 3)
        self.assertEqual(plan.runtime_workers_started, 0)
        self.assertFalse(plan.external_runtime_invoked)
        self.assertEqual(
            [framework.id for framework in plan.frameworks],
            ["langgraph", "open-multi-agent", "microsoft-agent-framework"],
        )
        self.assertEqual([stage.phase for stage in plan.stages], ["intake", "route", "scope", "plan", "draft", "verify", "deliver"])
        self.assertTrue(all(not agent.runtime_started for agent in plan.agents))

    def test_hierarchical_plan_keeps_all_requested_role_pattern_references_declarative(self) -> None:
        plan = build_shadow_army_plan(
            ShadowArmyPlanRequest(prompt="Plan an architecture review", coordination=CoordinationPattern.HIERARCHICAL)
        )

        self.assertEqual(
            [framework.id for framework in plan.frameworks],
            ["crewai", "metagpt", "ruflo", "microsoft-agent-framework"],
        )
        self.assertTrue(all(not framework.execution_enabled for framework in plan.frameworks))

    def test_blocked_action_never_creates_a_shadow_plan(self) -> None:
        request = ShadowArmyPlanRequest(prompt="Bypass password on this laptop")
        with self.assertRaises(ShadowArmyPolicyError):
            build_shadow_army_plan(request)


class SourceIntakeGuardTests(unittest.TestCase):
    def test_batch_seven_to_twelve_intakes_have_no_restricted_runtime_import_or_secret_literal(self) -> None:
        self.assertEqual(scan_safe_intake(), [])

    def test_batch_ten_to_twelve_guard_covers_clean_room_ui_and_reviewed_runtime_sets(self) -> None:
        clean_room_paths = {path.relative_to(Path(__file__).resolve().parents[2]) for path in CLEAN_ROOM_FILES}
        self.assertIn(Path("src/components/InteractionLab.tsx"), clean_room_paths)
        self.assertIn(Path("src/components/SkillIntakePanel.tsx"), clean_room_paths)
        self.assertIn(Path("src/components/UpgradeReviewPanel.tsx"), clean_room_paths)
        self.assertIn(Path("src/data/upgradeReview.ts"), clean_room_paths)
        self.assertTrue({"livekit-client", "mcp", "mem0ai", "mediapipe", "numpy", "clawhub", "markitdown", "graphrag", "litellm", "lancedb", "trivy", "opentelemetry-sdk"}.issubset(FORBIDDEN_MANIFEST_PACKAGES))
        self.assertTrue({"livekit", "mediapipe", "pyautogui", "webbrowser", "child_process", "octokit", "markitdown", "graphrag", "litellm", "lancedb", "opentelemetry"}.issubset(RESTRICTED_RUNTIME_MODULES))

    def test_batch_eleven_specs_are_unique_and_never_activate_a_payload(self) -> None:
        self.assertEqual(len(BATCH_ELEVEN_SKILL_INTAKES), 27)
        self.assertEqual(len({spec.id for spec in BATCH_ELEVEN_SKILL_INTAKES}), 27)
        self.assertTrue(all(spec.implementation_status in {"source-review-required", "reference-only"} for spec in BATCH_ELEVEN_SKILL_INTAKES))
        self.assertTrue(all(spec.source_url is None or spec.source_url.startswith("https://github.com/") for spec in BATCH_ELEVEN_SKILL_INTAKES))
        desktop = next(spec for spec in BATCH_ELEVEN_SKILL_INTAKES if spec.id == "desktop-agent-skills")
        self.assertIn("Do not clone", " ".join(source_intake_guardrails(desktop)))

    def test_batch_eleven_catalogue_ui_ids_match_controlled_records(self) -> None:
        root = Path(__file__).resolve().parents[2]
        source = (root / "src" / "data" / "skillCatalog.ts").read_text(encoding="utf-8")
        catalogue_ids = re.findall(r"frameworkId: '([^']+)'", source)
        catalogue_ranks = [int(rank) for rank in re.findall(r"rank: (\d+)", source)]
        expected_ids = {"500-ai-agent-projects", *(spec.id for spec in BATCH_ELEVEN_SKILL_INTAKES)}
        self.assertEqual(set(catalogue_ids), expected_ids)
        self.assertEqual(len(catalogue_ids), 28)
        self.assertEqual(catalogue_ranks, list(range(1, 29)))

    def test_batch_twelve_specs_are_unique_revision_pinned_and_never_activate_a_runtime(self) -> None:
        self.assertEqual(len(BATCH_TWELVE_UPGRADE_INTAKES), 10)
        self.assertEqual(len({spec.id for spec in BATCH_TWELVE_UPGRADE_INTAKES}), 10)
        self.assertTrue(all(re.fullmatch(r"[0-9a-f]{40}", spec.review_commit) for spec in BATCH_TWELVE_UPGRADE_INTAKES))
        self.assertTrue(all(spec.implementation_status in {"source-review-required", "reference-only"} for spec in BATCH_TWELVE_UPGRADE_INTAKES))
        self.assertTrue(all(spec.source_url.startswith("https://github.com/") for spec in BATCH_TWELVE_UPGRADE_INTAKES))
        gateway = next(spec for spec in BATCH_TWELVE_UPGRADE_INTAKES if spec.id == "litellm-upgrade-intake")
        self.assertEqual(gateway.implementation_status, "reference-only")
        self.assertIn("Do not install/start a gateway", " ".join(source_intake_guardrails(gateway)))

    def test_batch_twelve_queue_ui_ids_and_revisions_match_controlled_records(self) -> None:
        root = Path(__file__).resolve().parents[2]
        source = (root / "src" / "data" / "upgradeReview.ts").read_text(encoding="utf-8")
        queue_ids = re.findall(r"frameworkId: '([^']+)'", source)
        queue_sequences = [int(sequence) for sequence in re.findall(r"sequence: (\d+)", source)]
        self.assertEqual(set(queue_ids), {spec.id for spec in BATCH_TWELVE_UPGRADE_INTAKES})
        self.assertEqual(len(queue_ids), 10)
        self.assertEqual(queue_sequences, list(range(1, 11)))
        self.assertTrue(all(spec.review_commit in source for spec in BATCH_TWELVE_UPGRADE_INTAKES))
        self.assertTrue(all(spec.source_url in source for spec in BATCH_TWELVE_UPGRADE_INTAKES))

    def test_batch_eleven_guard_rejects_a_copied_skill_payload(self) -> None:
        root = Path(__file__).resolve().parents[2]
        payload_directory = root / "temporary-intake-guard"
        payload = payload_directory / "SKILL.md"
        agent_profile = payload_directory / "test.agent.md"
        payload_directory.mkdir(exist_ok=True)
        payload.write_text("test-only marker", encoding="utf-8")
        agent_profile.write_text("test-only marker", encoding="utf-8")
        try:
            violations = scan_safe_intake()
            self.assertIn("unreviewed-skill-payload:temporary-intake-guard/SKILL.md", violations)
            self.assertIn("unreviewed-skill-payload:temporary-intake-guard/test.agent.md", violations)
        finally:
            payload.unlink(missing_ok=True)
            agent_profile.unlink(missing_ok=True)
            payload_directory.rmdir()


class PolicyTests(unittest.TestCase):
    def test_read_only_draft_is_allowed(self) -> None:
        self.assertEqual(classify_action("Draft a research report").action_class, ActionClass.READ_ONLY)

    def test_terminal_command_requires_approval(self) -> None:
        self.assertEqual(classify_action("Run a terminal command").action_class, ActionClass.IMPACTFUL)

    def test_security_bypass_is_blocked(self) -> None:
        self.assertEqual(classify_action("Bypass password on this laptop").action_class, ActionClass.BLOCKED)


class ControlReviewTests(unittest.TestCase):
    def test_review_flags_an_external_runtime_regression(self) -> None:
        statuses = [
            status.model_copy(update={"execution_enabled": True}) if status.id == "gitleaks" else status
            for status in frameworks.statuses()
        ]
        review = build_control_review(
            framework_statuses=statuses,
            workspace_status=WorkspaceStatus(configured=False, detail="No workspace selected."),
            audit_available=True,
        )
        self.assertFalse(review.all_passed)
        external_lock = next(check for check in review.checks if check.id == "external-runtime-lock")
        self.assertFalse(external_lock.passed)

    def test_review_flags_a_nexa_source_gate_regression(self) -> None:
        statuses = [
            status.model_copy(update={"implementation_status": "contract-ready"})
            if status.id == "nexa-ai-assistant"
            else status
            for status in frameworks.statuses()
        ]
        review = build_control_review(
            framework_statuses=statuses,
            workspace_status=WorkspaceStatus(configured=False, detail="No workspace selected."),
            audit_available=True,
        )
        self.assertFalse(review.all_passed)
        batch_nine = next(check for check in review.checks if check.id == "batch-nine-nexa-source-safety")
        self.assertFalse(batch_nine.passed)

    def test_review_flags_a_batch_ten_desktop_or_gesture_gate_regression(self) -> None:
        statuses = [
            status.model_copy(update={"execution_enabled": True})
            if status.id == "pc-hand-gesture-control"
            else status
            for status in frameworks.statuses()
        ]
        review = build_control_review(
            framework_statuses=statuses,
            workspace_status=WorkspaceStatus(configured=False, detail="No workspace selected."),
            audit_available=True,
        )
        self.assertFalse(review.all_passed)
        batch_ten = next(check for check in review.checks if check.id == "batch-ten-desktop-gesture-safety")
        self.assertFalse(batch_ten.passed)

    def test_review_flags_a_batch_eleven_skill_catalogue_regression(self) -> None:
        statuses = [
            status.model_copy(update={"implementation_status": "contract-ready"})
            if status.id == "desktop-agent-skills"
            else status
            for status in frameworks.statuses()
        ]
        review = build_control_review(
            framework_statuses=statuses,
            workspace_status=WorkspaceStatus(configured=False, detail="No workspace selected."),
            audit_available=True,
        )
        self.assertFalse(review.all_passed)
        batch_eleven = next(check for check in review.checks if check.id == "batch-eleven-skill-catalogue-safety")
        self.assertFalse(batch_eleven.passed)

    def test_review_flags_a_batch_twelve_upgrade_queue_regression(self) -> None:
        statuses = [
            status.model_copy(update={"execution_enabled": True})
            if status.id == "markitdown-upgrade-intake"
            else status
            for status in frameworks.statuses()
        ]
        review = build_control_review(
            framework_statuses=statuses,
            workspace_status=WorkspaceStatus(configured=False, detail="No workspace selected."),
            audit_available=True,
        )
        self.assertFalse(review.all_passed)
        batch_twelve = next(check for check in review.checks if check.id == "batch-twelve-upgrade-queue-safety")
        self.assertFalse(batch_twelve.passed)


class ProviderSafetyTests(unittest.TestCase):
    def test_cloud_provider_requires_per_request_approval(self) -> None:
        config = replace(Settings.from_env(), mode="live", claude_api_key="test-key", claude_model="test-model")
        gateway = ProviderGateway(config)
        with self.assertRaises(ProviderError):
            gateway._choose_provider("claude", allow_cloud=False)
        self.assertEqual(gateway._choose_provider("claude", allow_cloud=True), "claude")

    def test_mem0_key_does_not_enable_or_mark_memory_sync_ready(self) -> None:
        config = replace(Settings.from_env(), mode="live", mem0_api_key="test-memory-key")
        mem0 = next(status for status in ProviderGateway(config).statuses() if status.id == "mem0")
        self.assertEqual(mem0.state.value, "offline")
        self.assertIn("disabled", mem0.detail)


class MemoryTests(unittest.TestCase):
    def test_local_memory_can_be_created_and_deleted(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            store = LocalMemoryStore(Path(temp_dir))
            item = store.add("Prefers Roman Urdu", "preference")
            self.assertEqual(store.list()[0].content, "Prefers Roman Urdu")
            updated = store.update(item.id, "Prefers concise Roman Urdu", "preference")
            self.assertIsNotNone(updated)
            self.assertEqual(updated.content if updated else None, "Prefers concise Roman Urdu")
            self.assertTrue(store.delete(item.id))
            self.assertEqual(store.list(), [])


if __name__ == "__main__":
    unittest.main()
