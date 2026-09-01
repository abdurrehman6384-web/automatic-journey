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
from app.schemas import WorkspaceStatus
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
