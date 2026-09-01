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
        framework_items = response.json()["frameworks"]
        self.assertEqual(len(framework_items), 49)
        frameworks = {item["id"]: item for item in framework_items}
        self.assertEqual(len(frameworks), 49)
        self.assertEqual(
            set(frameworks),
            {
                "jinwoo-native", "swarms", "agency-swarm", "ruflo", "langgraph", "crewai",
                "ag2", "openhands", "firecrawl", "firecrawl-web-agent", "crawl4ai",
                "mem0", "openclaw", "trufflehog", "gitleaks", "jinwoo-native-control-audit",
                "goose", "orkas", "bytebot", "open-desktop", "hermes-agent", "openagent", "iris-go", "iris-mini",
                "iris-zero", "zoey", "iris-ai", "iris-x",
                "ai-video-editor", "ai-video-editor-pipeline", "watch-video-skill", "videodb-skills", "anthropic-cybersecurity-skills",
                "anthropic-skills", "ai-research-skills", "addy-osmani-agent-skills", "wordpress-agent-skills", "composio", "stagehand",
                "langchain-community", "official-mcp-servers", "awesome-mcp-servers", "metagpt", "autogen", "pydantic-ai",
                "scientific-agent-skills", "open-autoglm", "500-ai-agent-projects", "envagent-source-intake",
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
        for adapter in ("mem0", "openclaw", "trufflehog", "gitleaks"):
            self.assertFalse(frameworks[adapter]["execution_enabled"])
            self.assertEqual(frameworks[adapter]["integration_batch"], 3)
        self.assertEqual(frameworks["trufflehog"]["implementation_status"], "license-review-required")
        self.assertEqual(frameworks["gitleaks"]["runtime"], "go-cli")
        self.assertEqual(frameworks["mem0"]["category"], "memory")
        batch_four = (
            "goose", "orkas", "bytebot", "open-desktop", "hermes-agent", "openagent", "iris-go", "iris-mini",
            "iris-zero", "zoey", "iris-ai", "iris-x",
        )
        for adapter in batch_four:
            self.assertFalse(frameworks[adapter]["execution_enabled"])
            self.assertEqual(frameworks[adapter]["integration_batch"], 4)
            self.assertTrue(frameworks[adapter]["capabilities"])
        self.assertEqual(frameworks["goose"]["runtime"], "rust-cli")
        self.assertEqual(frameworks["openagent"]["runtime"], "go-service")
        self.assertEqual(frameworks["bytebot"]["implementation_status"], "archived-upstream")
        self.assertEqual(frameworks["iris-go"]["implementation_status"], "license-review-required")
        self.assertEqual(frameworks["iris-mini"]["implementation_status"], "license-review-required")
        self.assertEqual(frameworks["iris-zero"]["implementation_status"], "license-review-required")
        self.assertEqual(frameworks["iris-ai"]["implementation_status"], "reference-only")
        self.assertEqual(frameworks["iris-ai"]["state"], "reference-only")
        self.assertEqual(frameworks["iris-x"]["activation_boundary"], "reference-only")
        batch_five = (
            "ai-video-editor", "ai-video-editor-pipeline", "watch-video-skill", "videodb-skills", "anthropic-cybersecurity-skills",
            "anthropic-skills", "ai-research-skills", "addy-osmani-agent-skills", "wordpress-agent-skills", "composio", "stagehand",
            "langchain-community", "official-mcp-servers", "awesome-mcp-servers", "metagpt", "autogen", "pydantic-ai",
            "scientific-agent-skills", "open-autoglm", "500-ai-agent-projects", "envagent-source-intake",
        )
        for adapter in batch_five:
            self.assertFalse(frameworks[adapter]["execution_enabled"])
            self.assertEqual(frameworks[adapter]["integration_batch"], 5)
            self.assertTrue(frameworks[adapter]["capabilities"])
        self.assertEqual(frameworks["ai-video-editor"]["category"], "media")
        self.assertEqual(frameworks["anthropic-cybersecurity-skills"]["activation_boundary"], "read-only")
        self.assertEqual(frameworks["anthropic-skills"]["implementation_status"], "license-review-required")
        self.assertEqual(frameworks["official-mcp-servers"]["implementation_status"], "license-review-required")
        self.assertEqual(frameworks["awesome-mcp-servers"]["state"], "reference-only")
        self.assertEqual(frameworks["open-autoglm"]["implementation_status"], "queued")
        self.assertEqual(frameworks["envagent-source-intake"]["implementation_status"], "source-review-required")
        self.assertNotIn("capcut-patcher", frameworks)
        self.assertTrue(frameworks["jinwoo-native-control-audit"]["execution_enabled"])
        self.assertEqual(frameworks["jinwoo-native-control-audit"]["state"], "canonical")

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

    def test_batch_three_dry_runs_remain_non_executing_and_expose_boundaries(self) -> None:
        openclaw = self.client.post(
            "/api/frameworks/openclaw/dry-run",
            json={"prompt": "Prepare a local automation safety plan", "requested_agents": 120},
        )
        scanner = self.client.post(
            "/api/frameworks/gitleaks/dry-run",
            json={"prompt": "Prepare a bounded secret-scanner review", "requested_agents": 3},
        )
        mem0 = self.client.post(
            "/api/frameworks/mem0/dry-run",
            json={"prompt": "Prepare an optional memory-interoperability plan", "requested_agents": 3},
        )
        self.assertEqual(openclaw.status_code, 200)
        self.assertFalse(openclaw.json()["external_runtime_invoked"])
        self.assertIn("Do not start messaging channels", " ".join(openclaw.json()["next_steps"]))
        self.assertEqual(scanner.status_code, 200)
        self.assertFalse(scanner.json()["external_runtime_invoked"])
        self.assertIn("Do not read workspace files", " ".join(scanner.json()["next_steps"]))
        self.assertEqual(mem0.status_code, 200)
        self.assertIn("ambiguous memo API", " ".join(mem0.json()["next_steps"]))

    def test_batch_four_skill_dry_runs_remain_non_executing_and_references_stay_reference_only(self) -> None:
        goose = self.client.post(
            "/api/frameworks/goose/dry-run",
            json={"prompt": "Prepare a safe coding-task review", "requested_agents": 450},
        )
        desktop = self.client.post(
            "/api/frameworks/open-desktop/dry-run",
            json={"prompt": "Prepare a desktop automation boundary", "requested_agents": 3},
        )
        reference = self.client.post(
            "/api/frameworks/iris-ai/dry-run",
            json={"prompt": "Review public desktop UX capabilities", "requested_agents": 3},
        )
        self.assertEqual(goose.status_code, 200)
        self.assertEqual(goose.json()["bounded_runtime_workers"], 3)
        self.assertFalse(goose.json()["external_runtime_invoked"])
        self.assertIn("disposable sandbox", " ".join(goose.json()["next_steps"]).casefold())
        self.assertEqual(desktop.status_code, 200)
        self.assertFalse(desktop.json()["external_runtime_invoked"])
        self.assertIn("screen, microphone", " ".join(desktop.json()["next_steps"]).casefold())
        self.assertEqual(reference.status_code, 200)
        self.assertFalse(reference.json()["external_runtime_invoked"])
        self.assertIn("reference-only", reference.json()["summary"])
        self.assertIn("Do not copy", " ".join(reference.json()["next_steps"]))

    def test_batch_five_specialist_skill_plans_remain_non_executing_and_apply_boundaries(self) -> None:
        video = self.client.post(
            "/api/frameworks/watch-video-skill/dry-run",
            json={"prompt": "Prepare a local video feedback plan", "requested_agents": 8},
        )
        defensive = self.client.post(
            "/api/frameworks/anthropic-cybersecurity-skills/dry-run",
            json={"prompt": "Prepare a defensive security controls review", "requested_agents": 3},
        )
        browser = self.client.post(
            "/api/frameworks/stagehand/dry-run",
            json={"prompt": "Prepare a browser automation boundary", "requested_agents": 3},
        )
        catalogue = self.client.post(
            "/api/frameworks/500-ai-agent-projects/dry-run",
            json={"prompt": "Compare public agent use cases", "requested_agents": 3},
        )
        source_intake = self.client.post(
            "/api/frameworks/envagent-source-intake/dry-run",
            json={"prompt": "Plan a sandbox architecture review", "requested_agents": 3},
        )
        self.assertEqual(video.status_code, 200)
        self.assertFalse(video.json()["external_runtime_invoked"])
        self.assertIn("user-supplied", " ".join(video.json()["next_steps"]))
        self.assertEqual(defensive.status_code, 200)
        self.assertFalse(defensive.json()["external_runtime_invoked"])
        self.assertIn("defensive", " ".join(defensive.json()["next_steps"]).casefold())
        self.assertEqual(browser.status_code, 200)
        self.assertFalse(browser.json()["external_runtime_invoked"])
        self.assertIn("Do not launch a browser", " ".join(browser.json()["next_steps"]))
        self.assertEqual(catalogue.status_code, 200)
        self.assertIn("reference-only", catalogue.json()["summary"])
        self.assertEqual(source_intake.status_code, 200)
        self.assertIn("source-intake", source_intake.json()["summary"])
        self.assertFalse(source_intake.json()["external_runtime_invoked"])

    def test_native_control_review_reports_invariants_and_writes_redacted_metadata(self) -> None:
        response = self.client.post("/api/control/review")
        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertTrue(payload["all_passed"])
        self.assertFalse(payload["external_runtime_invoked"])
        self.assertEqual(len(payload["checks"]), 9)
        self.assertTrue(all(check["passed"] for check in payload["checks"]))
        self.assertIn("external runtime", payload["summary"].casefold())
        audit = self.client.get("/api/audit").json()
        self.assertIn("control.review_completed", {event["event_type"] for event in audit})
        self.assertNotIn("https://", str(audit))

    def test_security_scan_plan_requires_workspace_and_consent_without_reading_files(self) -> None:
        missing_workspace = self.client.post(
            "/api/security/scan-plan",
            json={"scanner_id": "gitleaks", "confirm_authorized": True},
        )
        project = Path(self.temp_dir.name) / "security-project"
        project.mkdir()
        self.assertEqual(self.client.put("/api/workspace", json={"path": str(project)}).status_code, 200)
        no_consent = self.client.post(
            "/api/security/scan-plan",
            json={"scanner_id": "gitleaks", "confirm_authorized": False},
        )
        gitleaks = self.client.post(
            "/api/security/scan-plan",
            json={"scanner_id": "gitleaks", "confirm_authorized": True},
        )
        trufflehog = self.client.post(
            "/api/security/scan-plan",
            json={"scanner_id": "trufflehog", "confirm_authorized": True},
        )
        self.assertEqual(missing_workspace.status_code, 400)
        self.assertEqual(no_consent.status_code, 400)
        self.assertEqual(gitleaks.status_code, 200)
        self.assertFalse(gitleaks.json()["external_scan_started"])
        self.assertTrue(gitleaks.json()["requires_approval_for_scan"])
        self.assertEqual(trufflehog.status_code, 200)
        self.assertTrue(trufflehog.json()["license_review_required"])
        audit = self.client.get("/api/audit").json()
        self.assertIn("security.scan_plan_created", {event["event_type"] for event in audit})
        self.assertNotIn(str(project), str(audit))

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

    def test_api_rejects_whitespace_only_text_at_boundary(self) -> None:
        blank_chat = self.client.post("/api/chat", json={"message": "   "})
        blank_mission = self.client.post("/api/missions", json={"prompt": "   "})
        blank_dry_run = self.client.post(
            "/api/frameworks/ag2/dry-run",
            json={"prompt": "   ", "requested_agents": 3},
        )
        blank_memory = self.client.post(
            "/api/memories",
            json={"content": "   ", "kind": "note", "consent": True},
        )
        blank_research = self.client.post("/api/research/plan", json={"topic": "   "})
        mission = self.client.post("/api/missions", json={"prompt": "Analyze a safe document"}).json()
        blank_actor = self.client.post(f"/api/missions/{mission['id']}/approve", json={"approved_by": "   "})
        for response in (blank_chat, blank_mission, blank_dry_run, blank_memory, blank_research, blank_actor):
            self.assertEqual(response.status_code, 422)

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
