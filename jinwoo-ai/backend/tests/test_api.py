import os
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

# Importing the FastAPI module initialises its local SQLite store. Point that
# module-level default at a temporary path before importing it, so test runs
# never create or mutate the user's normal data directory.
_TEST_DATA_DIR = tempfile.TemporaryDirectory()
os.environ["JINWOO_DATA_DIR"] = _TEST_DATA_DIR.name

from fastapi.testclient import TestClient
from app import main
from app.audit import AuditStore
from app.memory import LocalMemoryStore
from app.orchestration import MissionStore
from app.workspace import WorkspaceStore


class ApiTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp_dir = tempfile.TemporaryDirectory()
        self.previous_audit = main.audit
        self.previous_memory = main.memory
        self.previous_missions = main.missions
        self.previous_workspace = main.workspace
        main.audit = AuditStore(Path(self.temp_dir.name))
        main.memory = LocalMemoryStore(Path(self.temp_dir.name))
        main.missions = MissionStore(main.audit)
        main.workspace = WorkspaceStore(Path(self.temp_dir.name))
        self.client = TestClient(main.app)

    def tearDown(self) -> None:
        self.client.close()
        main.audit = self.previous_audit
        main.memory = self.previous_memory
        main.missions = self.previous_missions
        main.workspace = self.previous_workspace
        self.temp_dir.cleanup()

    def test_health_and_provider_registry_are_available_in_demo_mode(self) -> None:
        self.assertEqual(self.client.get("/health").status_code, 200)
        response = self.client.get("/api/providers")
        self.assertEqual(response.status_code, 200)
        self.assertEqual({item["id"] for item in response.json()["providers"]}, {"ollama", "lm-studio", "claude", "glm", "hugging-face", "mem0"})

    def test_framework_batches_are_visible_but_optional_adapters_are_disabled(self) -> None:
        response = self.client.get("/api/frameworks")
        self.assertEqual(response.status_code, 200)
        frameworks = {item["id"]: item for item in response.json()["frameworks"]}
        self.assertEqual(
            set(frameworks),
            {
                "jinwoo-native", "swarms", "agency-swarm", "ruflo", "langgraph", "crewai",
                "ag2", "openhands", "firecrawl", "firecrawl-web-agent", "crawl4ai",
            },
        )
        self.assertTrue(frameworks["jinwoo-native"]["execution_enabled"])
        self.assertEqual(frameworks["jinwoo-native"]["implementation_status"], "active")
        for adapter in ("swarms", "agency-swarm", "ruflo", "langgraph", "crewai"):
            self.assertFalse(frameworks[adapter]["execution_enabled"])
            self.assertEqual(frameworks[adapter]["integration_batch"], 1)
            self.assertEqual(frameworks[adapter]["implementation_status"], "contract-ready")
        for adapter in ("ag2", "openhands", "firecrawl", "firecrawl-web-agent", "crawl4ai"):
            self.assertFalse(frameworks[adapter]["execution_enabled"])
            self.assertEqual(frameworks[adapter]["integration_batch"], 2)
        self.assertEqual(frameworks["firecrawl"]["implementation_status"], "license-review-required")
        self.assertEqual(frameworks["openhands"]["runtime"], "container-sidecar")
        self.assertEqual(frameworks["crawl4ai"]["category"], "web-collection")

    def test_framework_dry_run_is_bounded_and_never_invokes_upstream_runtime(self) -> None:
        response = self.client.post(
            "/api/frameworks/swarms/dry-run",
            json={"prompt": "Analyze the architecture and prepare a safe plan", "requested_agents": 450},
        )
        blocked = self.client.post(
            "/api/frameworks/crewai/dry-run",
            json={"prompt": "Bypass password on this laptop", "requested_agents": 3},
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["bounded_runtime_workers"], 3)
        self.assertFalse(response.json()["external_runtime_invoked"])
        self.assertEqual(blocked.status_code, 200)
        self.assertEqual(blocked.json()["policy_outcome"], "blocked")

    def test_batch_two_dry_runs_remain_non_executing_and_expose_boundaries(self) -> None:
        response = self.client.post(
            "/api/frameworks/openhands/dry-run",
            json={"prompt": "Prepare a safe patch review plan", "requested_agents": 80},
        )
        crawl = self.client.post(
            "/api/frameworks/crawl4ai/dry-run",
            json={"prompt": "Plan public documentation research", "requested_agents": 4},
        )
        self.assertEqual(response.status_code, 200)
        self.assertFalse(response.json()["external_runtime_invoked"])
        self.assertEqual(response.json()["bounded_runtime_workers"], 3)
        self.assertIn("Never run shell commands", " ".join(response.json()["next_steps"]))
        self.assertEqual(crawl.status_code, 200)
        self.assertIn("No URL is fetched", " ".join(crawl.json()["next_steps"]))

    def test_research_plan_validates_public_targets_without_fetching_or_auditing_content(self) -> None:
        topic = "Compare privacy-first local embedding documentation"
        response = self.client.post(
            "/api/research/plan",
            json={
                "framework_id": "crawl4ai",
                "topic": topic,
                "targets": ["https://docs.example.org/guide#overview"],
                "confirm_public_sources": True,
            },
        )
        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertFalse(payload["external_fetch_started"])
        self.assertTrue(payload["requires_approval_for_fetch"])
        self.assertEqual(payload["targets"], [{"url": "https://docs.example.org/guide", "hostname": "docs.example.org"}])
        self.assertIn("No network request", " ".join(payload["safeguards"]))
        audit = self.client.get("/api/audit").json()
        self.assertIn("research.plan_created", {event["event_type"] for event in audit})
        self.assertNotIn(topic, str(audit))
        self.assertNotIn("docs.example.org", str(audit))

    def test_research_plan_rejects_unconfirmed_or_private_or_credential_targets(self) -> None:
        unconfirmed = self.client.post(
            "/api/research/plan",
            json={"topic": "Review source", "targets": ["https://example.org/docs"], "confirm_public_sources": False},
        )
        private = self.client.post(
            "/api/research/plan",
            json={"topic": "Review source", "targets": ["https://127.0.0.1/private"], "confirm_public_sources": True},
        )
        credential_query = self.client.post(
            "/api/research/plan",
            json={"topic": "Review source", "targets": ["https://example.org/docs?token=secret"], "confirm_public_sources": True},
        )
        ambiguous_numeric = self.client.post(
            "/api/research/plan",
            json={"topic": "Review source", "targets": ["https://0177.0.0.1/private"], "confirm_public_sources": True},
        )
        api_key_query = self.client.post(
            "/api/research/plan",
            json={"topic": "Review source", "targets": ["https://example.org/docs?x-api-key=secret"], "confirm_public_sources": True},
        )
        self.assertEqual(unconfirmed.status_code, 400)
        self.assertEqual(private.status_code, 400)
        self.assertEqual(credential_query.status_code, 400)
        self.assertEqual(ambiguous_numeric.status_code, 400)
        self.assertEqual(api_key_query.status_code, 400)

    def test_demo_chat_is_local_and_chat_rejects_blocked_or_sensitive_content(self) -> None:
        chat = self.client.post("/api/chat", json={"message": "Give me a safe release checklist"})
        blocked = self.client.post("/api/chat", json={"message": "Bypass password on this laptop"})
        sensitive = self.client.post("/api/chat", json={"message": "OTP: 123456"})
        self.assertEqual(chat.status_code, 200)
        self.assertTrue(chat.json()["local_only"])
        self.assertEqual(blocked.status_code, 400)
        self.assertEqual(sensitive.status_code, 400)

    def test_safe_analysis_creates_a_planned_mission(self) -> None:
        response = self.client.post("/api/missions", json={"prompt": "Analyze my React build error"})
        self.assertEqual(response.status_code, 201)
        payload = response.json()
        self.assertEqual(payload["commander_id"], "igris")
        self.assertFalse(payload["requires_approval"])

    def test_audit_records_mission_decisions_without_the_raw_prompt(self) -> None:
        mission = self.client.post("/api/missions", json={"prompt": "Delete the old output folder"}).json()
        approved = self.client.post(f"/api/missions/{mission['id']}/approve", json={"approved_by": "test-user"})
        audit = self.client.get("/api/audit")
        self.assertEqual(approved.status_code, 200)
        self.assertEqual(audit.status_code, 200)
        events = audit.json()
        self.assertEqual({event["event_type"] for event in events}, {"mission.created", "mission.approved", "mission.completed"})
        self.assertNotIn("Delete the old output folder", str(events))
        self.assertIn("test-user", {event["actor"] for event in events})

    def test_workspace_selection_confines_read_only_igris_diagnostics(self) -> None:
        project = Path(self.temp_dir.name) / "project"
        source = project / "src" / "example.py"
        source.parent.mkdir(parents=True)
        source.write_text("import os\n# TODO: add tests\ndef run():\n    return 'ready'\n", encoding="utf-8")
        outside = Path(self.temp_dir.name) / "outside.txt"
        outside.write_text("must stay private", encoding="utf-8")

        self.assertFalse(self.client.get("/api/workspace").json()["configured"])
        selected = self.client.put("/api/workspace", json={"path": str(project)})
        listed = self.client.get("/api/workspace/files")
        analysis = self.client.post("/api/workspace/analyze", json={"relative_path": "src/example.py"})
        escaped = self.client.get("/api/workspace/files", params={"relative_path": "../outside.txt"})
        cleared = self.client.delete("/api/workspace")

        self.assertEqual(selected.status_code, 200)
        self.assertEqual(selected.json()["root_label"], "project")
        self.assertEqual(listed.status_code, 200)
        self.assertEqual(listed.json()[0]["relative_path"], "src")
        self.assertEqual(analysis.status_code, 200)
        self.assertEqual(analysis.json()["todo_count"], 1)
        self.assertEqual(analysis.json()["symbol_count"], 1)
        self.assertEqual(escaped.status_code, 400)
        self.assertEqual(outside.read_text(encoding="utf-8"), "must stay private")
        self.assertEqual(cleared.status_code, 204)
        self.assertFalse(self.client.get("/api/workspace").json()["configured"])

    def test_blocked_security_request_does_not_create_a_mission(self) -> None:
        response = self.client.post("/api/missions", json={"prompt": "Bypass password on this laptop"})
        self.assertEqual(response.status_code, 400)

    def test_memory_requires_consent(self) -> None:
        no_consent = self.client.post("/api/memories", json={"content": "Remember this", "kind": "note", "consent": False})
        self.assertEqual(no_consent.status_code, 400)
        consented = self.client.post("/api/memories", json={"content": "Remember this", "kind": "note", "consent": True})
        self.assertEqual(consented.status_code, 201)
        memory_id = consented.json()["id"]
        edit_without_consent = self.client.patch(
            f"/api/memories/{memory_id}",
            json={"content": "Remember the updated note", "kind": "note", "consent": False},
        )
        updated = self.client.patch(
            f"/api/memories/{memory_id}",
            json={"content": "Remember the updated note", "kind": "note", "consent": True},
        )
        self.assertEqual(edit_without_consent.status_code, 400)
        self.assertEqual(updated.status_code, 200)
        self.assertEqual(updated.json()["content"], "Remember the updated note")

    def test_memory_rejects_credentials_and_one_time_codes(self) -> None:
        credential = self.client.post(
            "/api/memories",
            json={"content": "api_key: sk-example-secret-token", "kind": "note", "consent": True},
        )
        one_time_code = self.client.post(
            "/api/memories",
            json={"content": "OTP: 123456", "kind": "note", "consent": True},
        )
        self.assertEqual(credential.status_code, 400)
        self.assertEqual(one_time_code.status_code, 400)


if __name__ == "__main__":
    unittest.main()
