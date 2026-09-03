#!/usr/bin/env python3
"""Static no-import guard for controlled Shadow Army source intakes.

This intentionally checks only the clean-room files and dependency manifests
that implement or expose Batch 07–13. It does not unpack, execute, import, or
inspect an archive payload. A failing check prints file locations and rule
names, never matching source text that might contain sensitive material.
"""

from __future__ import annotations

import ast
import json
import os
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CLEAN_ROOM_FILES = (
    ROOT / "backend" / "app" / "shadow_army.py",
    ROOT / "backend" / "app" / "skill_intakes.py",
    ROOT / "backend" / "app" / "skill_library.py",
    ROOT / "backend" / "app" / "skill_activation.py",
    ROOT / "backend" / "app" / "skill_orchestrator.py",
    ROOT / "src" / "components" / "ShadowArmyCore.tsx",
    ROOT / "src" / "components" / "NativeSkillLibraryPanel.tsx",
    ROOT / "backend" / "app" / "workspace.py",
    ROOT / "src" / "components" / "WorkspacePanel.tsx",
    ROOT / "src" / "components" / "InteractionLab.tsx",
    ROOT / "src" / "components" / "SkillIntakePanel.tsx",
    ROOT / "src" / "components" / "UpgradeReviewPanel.tsx",
    ROOT / "src" / "data" / "skillCatalog.ts",
    ROOT / "src" / "data" / "upgradeReview.ts",
)
MANIFESTS = (ROOT / "backend" / "requirements.txt", ROOT / "package.json")

# These names may occur as declarative IDs in the registry. They must never be
# loaded as direct Python/TypeScript dependencies by the Batch 07 implementation.
EXTERNAL_FRAMEWORK_MODULES = {
    "crewai",
    "autogen",
    "langgraph",
    "metagpt",
    "ruflo",
    "agent_swarm",
    "agent-swarm",
    "open_multi_agent",
    "open-multi-agent",
    "microsoft_agent_framework",
    "microsoft-agent-framework",
}

# Batch 08's reviewed geospatial project is intentionally not a direct
# dependency. A future exception needs a fresh source/data/privacy review and
# an explicit update to this guard, rather than a silent package addition.
GEOSPATIAL_RUNTIME_PACKAGES = {
    "@mapbox/vector-tile",
    "cesium",
    "egm96-universal",
    "mgrs",
    "pbf",
    "puppeteer",
    "satellite.js",
    "sharp",
    "vite-plugin-cesium",
    "ws",
}
# Batch 09's NEXA source intake has no verified licence and describes a
# desktop-assistant runtime. These packages must not enter a Jinwoo manifest
# incidentally; any future exception needs an independent review and guard edit.
NEXA_RUNTIME_PACKAGES = {
    "edge-tts",
    "google-api-python-client",
    "google-generativeai",
    "google-genai",
    "livekit",
    "livekit-agents",
    "livekit-plugins-google",
    "openai",
    "opencv-python",
    "pillow",
    "pyaudio",
    "pynput",
    "pyautogui",
    "pygetwindow",
    "pywin32",
    "selenium",
    "speechrecognition",
    "ultralytics",
    "webdriver-manager",
    "youtube-search-python",
}
# Batch 10 adds two unlicensed desktop/gesture source intakes. The nested MIT
# starter in the Jarvis tree does not license its root/CLI/Python content, so its
# media, setup, provider and MCP runtime package set remains excluded as well.
JARVIS_RUNTIME_PACKAGES = {
    "@livekit/components-react",
    "@livekit/protocol",
    "fuzzywuzzy",
    "livekit-client",
    "livekit-server-sdk",
    "livekit-plugins-noise-cancellation",
    "livekit-plugins-openai",
    "mcp",
    "mem0ai",
    "next",
    "python-dotenv",
}
HAND_GESTURE_RUNTIME_PACKAGES = {"mediapipe", "numpy"}
# Batch 11 collection/installer requests remain metadata-only. A catalogue name
# or a SKILL.md file is never an installation grant; explicit package/CLI paths
# are blocked until a future source-specific activation review changes this guard.
SKILL_COLLECTION_RUNTIME_PACKAGES = {"clawhub", "execa", "simple-git"}
# Batch 12 records a finite, metadata-only next-ten review queue. These candidate
# package, binary and observability lanes may not appear in either manifest until
# a separate exact source/licence/dependency/privacy/approval review is accepted.
BATCH_TWELVE_RUNTIME_PACKAGES = {
    "markitdown",
    "graphrag",
    "litellm",
    "opa",
    "lancedb",
    "promptfoo",
    "ruff",
    "syft",
    "trivy",
    "opentelemetry-api",
    "opentelemetry-sdk",
    "opentelemetry-exporter-otlp",
}
# Batch 13 is a native clean-room skill library, not a permission to introduce
# computer-use, vision, robotics or provider dependencies from reviewed sources.
NATIVE_SKILL_LIBRARY_RUNTIME_PACKAGES = {
    "anthropic",
    "easyocr",
    "mss",
    "pytesseract",
    "rclpy",
    "roslib",
    "rospy",
}
FORBIDDEN_MANIFEST_PACKAGES = (
    EXTERNAL_FRAMEWORK_MODULES
    | GEOSPATIAL_RUNTIME_PACKAGES
    | NEXA_RUNTIME_PACKAGES
    | JARVIS_RUNTIME_PACKAGES
    | HAND_GESTURE_RUNTIME_PACKAGES
    | SKILL_COLLECTION_RUNTIME_PACKAGES
    | BATCH_TWELVE_RUNTIME_PACKAGES
    | NATIVE_SKILL_LIBRARY_RUNTIME_PACKAGES
)

# Import-level checks complement manifest scanning. These are package/module
# roots that belong to source-gated desktop, media, vision, provider or tool
# runtimes and must not be imported by a clean-room native feature.
RESTRICTED_RUNTIME_MODULES = {
    "@livekit",
    "@octokit",
    "child_process",
    "clawhub",
    "cv2",
    "dotenv",
    "edge_tts",
    "execa",
    "fuzzywuzzy",
    "google",
    "livekit",
    "mcp",
    "mediapipe",
    "mem0",
    "octokit",
    "numpy",
    "next",
    "openai",
    "pyaudio",
    "pyautogui",
    "pygetwindow",
    "pynput",
    "requests",
    "selenium",
    "simple_git",
    "speech_recognition",
    "ultralytics",
    "webdriver_manager",
    "webbrowser",
    "win32api",
    "win32gui",
}
# Do not import an evaluated Batch 12 candidate just because its metadata is
# listed in a review queue. Any future exception must be intentionally reviewed
# and accompanied by a scope-specific guard revision.
BATCH_TWELVE_RUNTIME_MODULES = {
    "graphrag",
    "lancedb",
    "litellm",
    "markitdown",
    "opentelemetry",
    "opa",
    "promptfoo",
    "ruff",
    "syft",
    "trivy",
}
NATIVE_SKILL_LIBRARY_RUNTIME_MODULES = {
    "anthropic",
    "easyocr",
    "mss",
    "pytesseract",
    "rclpy",
    "roslib",
    "rospy",
}
RESTRICTED_RUNTIME_MODULES |= BATCH_TWELVE_RUNTIME_MODULES | NATIVE_SKILL_LIBRARY_RUNTIME_MODULES

# This is intentionally narrow: it flags direct capability-entry APIs, not
# ordinary words in documentation, status messages, or policy descriptions.
FORBIDDEN_RUNTIME_TOKENS = (
    "subprocess",
    "os.system(",
    "os.popen(",
    "getUserMedia(",
    "navigator.mediaDevices",
    "pyautogui",
    "selenium",
    "playwright",
    "browser_use",
    "pynput",
    "pywin32",
    "pygetwindow",
    "livekit",
    "google.generativeai",
    "google_genai",
    "ultralytics",
    "speech_recognition",
    "pyaudio",
    "cv2.",
    "import cv2",
    "from cv2",
    "import openai",
    "from openai",
    "from google import genai",
    "from google.generativeai",
    "win32",
    "mediapipe",
    "@livekit",
    "mcp.client",
    "webbrowser.open",
    "node:child_process",
    "child_process",
    "npx clawhub",
    "simple-git",
    "@octokit",
)
SECRET_LITERAL = re.compile(
    r"(?i)(?:api[_-]?key|access[_-]?token|secret|password)\s*[:=]\s*['\"][^'\"]{8,}['\"]"
)
TS_IMPORT = re.compile(r"(?im)^\s*(?:import|export)\b[^;\n]*?\bfrom\s*['\"]([^'\"]+)['\"]|\brequire\(\s*['\"]([^'\"]+)['\"]\s*\)")
_SKILL_PAYLOAD_NAMES = {"skill.md"}
_AGENT_PAYLOAD_NAMES = {"agent.md"}
_SKILL_PAYLOAD_SUFFIX = ".agent.md"
_IGNORED_PAYLOAD_DIRECTORIES = {".git", ".venv", "node_modules", "dist", "coverage", "__pycache__", ".vite", "data"}
_NATIVE_SKILLS_DIRECTORY = ROOT / "skills"
_NATIVE_AGENTS_DIRECTORY = ROOT / "agents"
_NATIVE_SKILL_MARKER = "jinwoo_native: true"
_NATIVE_SKILL_HEADINGS = ("## Purpose", "## Procedure", "## Output", "## Safety boundary")
_NATIVE_SKILL_KEYS = {
    "id", "name", "description", "category", "activation_mode", "requires_approval",
    "tags", "routing_terms", "source_refs", "jinwoo_native",
}
_NATIVE_SKILL_ID = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
_NATIVE_AGENT_KEYS = {"id", "name", "description", "role", "skill_scope", "jinwoo_native"}


def _module_root(module: str) -> str:
    return module.replace("/", ".").split(".", 1)[0].casefold()


def _python_imports(path: Path, text: str) -> set[str]:
    tree = ast.parse(text, filename=str(path))
    modules: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            modules.update(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            modules.add(node.module)
    return modules


def _is_valid_native_skill(path: Path) -> bool:
    """Allow only the narrowly structured Jinwoo-authored portable skill files."""

    try:
        relative = path.relative_to(_NATIVE_SKILLS_DIRECTORY)
    except ValueError:
        return False
    if len(relative.parts) != 3 or relative.parts[-1] != "SKILL.md" or path.is_symlink():
        return False
    try:
        text = path.read_text(encoding="utf-8")
    except (OSError, UnicodeError):
        return False
    if not text.startswith("---\n") or len(text.encode("utf-8")) > 16_000 or "\n---\n" not in text:
        return False
    frontmatter, body = text[4:].split("\n---\n", 1)
    fields: dict[str, str] = {}
    for line in frontmatter.splitlines():
        if not line or line[:1].isspace() or ":" not in line:
            return False
        key, value = line.split(":", 1)
        if key in fields or key not in _NATIVE_SKILL_KEYS or not value.strip():
            return False
        fields[key] = value.strip()
    return (
        set(fields) == _NATIVE_SKILL_KEYS
        and fields["jinwoo_native"] == "true"
        and fields["activation_mode"] == "planning-only"
        and fields["requires_approval"] in {"true", "false"}
        and _NATIVE_SKILL_ID.fullmatch(fields["id"]) is not None
        and relative.parts[-2] == fields["id"]
        and _NATIVE_SKILL_MARKER in frontmatter
        and all(heading in body for heading in _NATIVE_SKILL_HEADINGS)
    )


def _is_valid_native_agent(path: Path) -> bool:
    """Allow only the canonical Jinwoo-owned Master Orchestrator manifest."""

    try:
        relative = path.relative_to(_NATIVE_AGENTS_DIRECTORY)
    except ValueError:
        return False
    if len(relative.parts) != 2 or relative.parts[-1] != "AGENT.md" or path.is_symlink():
        return False
    try:
        text = path.read_text(encoding="utf-8")
    except (OSError, UnicodeError):
        return False
    if not text.startswith("---\n") or len(text.encode("utf-8")) > 12_000 or "\n---\n" not in text:
        return False
    frontmatter, _body = text[4:].split("\n---\n", 1)
    fields: dict[str, str] = {}
    for line in frontmatter.splitlines():
        if not line or line[:1].isspace() or ":" not in line:
            return False
        key, value = line.split(":", 1)
        if key in fields or key not in _NATIVE_AGENT_KEYS or not value.strip():
            return False
        fields[key] = value.strip()
    return (
        set(fields) == _NATIVE_AGENT_KEYS
        and fields["jinwoo_native"] == "true"
        and fields["role"] == "canonical-orchestrator"
        and fields["skill_scope"] == "all-native-skills"
        and _NATIVE_SKILL_ID.fullmatch(fields["id"]) is not None
        and relative.parts[-2] == fields["id"]
        and _NATIVE_SKILL_MARKER in frontmatter
    )


def _upstream_skill_payloads() -> list[Path]:
    """Find copied upstream skill/instruction files while skipping local tooling."""

    payloads: list[Path] = []
    for directory, directories, filenames in os.walk(ROOT):
        directories[:] = [name for name in directories if name not in _IGNORED_PAYLOAD_DIRECTORIES]
        for filename in filenames:
            lowered_name = filename.casefold()
            candidate = Path(directory) / filename
            if lowered_name in _SKILL_PAYLOAD_NAMES:
                if not _is_valid_native_skill(candidate):
                    payloads.append(candidate)
            elif lowered_name in _AGENT_PAYLOAD_NAMES:
                if not _is_valid_native_agent(candidate):
                    payloads.append(candidate)
            elif lowered_name.endswith(_SKILL_PAYLOAD_SUFFIX):
                payloads.append(candidate)
    return payloads


def scan() -> list[str]:
    """Return policy-safe violation labels without exposing matching content."""

    violations: list[str] = []
    for path in CLEAN_ROOM_FILES:
        if not path.is_file():
            violations.append(f"missing-clean-room-file:{path.relative_to(ROOT)}")
            continue
        text = path.read_text(encoding="utf-8")
        lowered = text.casefold()

        if SECRET_LITERAL.search(text):
            violations.append(f"embedded-secret-literal:{path.relative_to(ROOT)}")

        for token in FORBIDDEN_RUNTIME_TOKENS:
            if token.casefold() in lowered:
                violations.append(f"forbidden-runtime-token:{path.relative_to(ROOT)}:{token}")

        if path.suffix == ".py":
            try:
                imported = _python_imports(path, text)
            except SyntaxError:
                violations.append(f"unparseable-python:{path.relative_to(ROOT)}")
                continue
            for module in imported:
                module_root = _module_root(module)
                if module_root in EXTERNAL_FRAMEWORK_MODULES:
                    violations.append(f"upstream-framework-import:{path.relative_to(ROOT)}:{module}")
                elif module_root in RESTRICTED_RUNTIME_MODULES:
                    violations.append(f"restricted-runtime-import:{path.relative_to(ROOT)}:{module}")
        else:
            for match in TS_IMPORT.finditer(text):
                module = (match.group(1) or match.group(2) or "").casefold()
                module_root = _module_root(module)
                if module_root in EXTERNAL_FRAMEWORK_MODULES:
                    violations.append(f"upstream-framework-import:{path.relative_to(ROOT)}:{module}")
                elif module_root in RESTRICTED_RUNTIME_MODULES:
                    violations.append(f"restricted-runtime-import:{path.relative_to(ROOT)}:{module}")

    for manifest in MANIFESTS:
        if not manifest.is_file():
            violations.append(f"missing-manifest:{manifest.relative_to(ROOT)}")
            continue
        manifest_text = manifest.read_text(encoding="utf-8").casefold()
        for package in FORBIDDEN_MANIFEST_PACKAGES:
            if re.search(rf"(?<![a-z0-9_@./-]){re.escape(package)}(?![a-z0-9_@./-])", manifest_text):
                violations.append(f"restricted-upstream-dependency:{manifest.relative_to(ROOT)}:{package}")

    # The extraction boundary is enforceable in the application checkout: the
    # archive itself belongs at repository root, never inside Jinwoo's sources.
    if any(ROOT.rglob("project.zip")):
        violations.append("archive-copied-into-jinwoo-source-tree")

    for native_skill in sorted(_NATIVE_SKILLS_DIRECTORY.glob("*/*/SKILL.md")):
        if _is_valid_native_skill(native_skill):
            native_text = native_skill.read_text(encoding="utf-8")
            if SECRET_LITERAL.search(native_text):
                violations.append(f"embedded-secret-literal:{native_skill.relative_to(ROOT)}")

    for payload in _upstream_skill_payloads():
        violations.append(f"unreviewed-skill-payload:{payload.relative_to(ROOT)}")

    return sorted(set(violations))


def main() -> int:
    violations = scan()
    report = {
        "check": "controlled-source-intake-batch-07-13",
        "clean_room_files": [str(path.relative_to(ROOT)) for path in CLEAN_ROOM_FILES],
        "manifest_files": [str(path.relative_to(ROOT)) for path in MANIFESTS],
        "passed": not violations,
        "violations": violations,
    }
    print(json.dumps(report, indent=2))
    return 0 if not violations else 1


if __name__ == "__main__":
    sys.exit(main())
