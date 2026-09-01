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


class ApiTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp_dir = tempfile.TemporaryDirectory()
        self.previous_audit = main.audit
        self.previous_memory = main.memory
        self.previous_missions = main.missions
        main.audit = AuditStore(Path(self.temp_dir.name))
        main.memory = LocalMemoryStore(Path(self.temp_dir.name))
        main.missions = MissionStore(main.audit)
        self.client = TestClient(main.app)

    def tearDown(self) -> None:
        self.client.close()
        main.audit = self.previous_audit
        main.memory = self.previous_memory
        main.missions = self.previous_missions
        self.temp_dir.cleanup()

    def test_health_and_provider_registry_are_available_in_demo_mode(self) -> None:
        self.assertEqual(self.client.get("/health").status_code, 200)
        response = self.client.get("/api/providers")
        self.assertEqual(response.status_code, 200)
        self.assertEqual({item["id"] for item in response.json()["providers"]}, {"ollama", "lm-studio", "claude", "glm", "hugging-face", "mem0"})

    def test_framework_registry_is_visible_but_optional_adapters_are_disabled(self) -> None:
        response = self.client.get("/api/frameworks")
        self.assertEqual(response.status_code, 200)
        frameworks = {item["id"]: item for item in response.json()["frameworks"]}
        self.assertEqual(set(frameworks), {"jinwoo-native", "swarms", "agency-swarm", "ruflo"})
        self.assertTrue(frameworks["jinwoo-native"]["execution_enabled"])
        self.assertTrue(all(not frameworks[adapter]["execution_enabled"] for adapter in ("swarms", "agency-swarm", "ruflo")))

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
