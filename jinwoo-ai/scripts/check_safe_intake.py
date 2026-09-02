#!/usr/bin/env python3
"""Static no-import guard for controlled Shadow Army source intakes.

This intentionally checks only the clean-room files and dependency manifests
that implement or expose Batch 07/08. It does not unpack, execute, import, or
inspect an archive payload. A failing check prints file locations and rule
names, never matching source text that might contain sensitive material.
"""

from __future__ import annotations

import ast
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CLEAN_ROOM_FILES = (
    ROOT / "backend" / "app" / "shadow_army.py",
    ROOT / "src" / "components" / "ShadowArmyCore.tsx",
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
FORBIDDEN_MANIFEST_PACKAGES = EXTERNAL_FRAMEWORK_MODULES | GEOSPATIAL_RUNTIME_PACKAGES

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
)
SECRET_LITERAL = re.compile(
    r"(?i)(?:api[_-]?key|access[_-]?token|secret|password)\s*[:=]\s*['\"][^'\"]{8,}['\"]"
)
TS_IMPORT = re.compile(r"(?im)^\s*(?:import|export)\b[^;\n]*?\bfrom\s*['\"]([^'\"]+)['\"]|\brequire\(\s*['\"]([^'\"]+)['\"]\s*\)")


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
                if _module_root(module) in EXTERNAL_FRAMEWORK_MODULES:
                    violations.append(f"upstream-framework-import:{path.relative_to(ROOT)}:{module}")
        else:
            for match in TS_IMPORT.finditer(text):
                module = (match.group(1) or match.group(2) or "").casefold()
                if _module_root(module) in EXTERNAL_FRAMEWORK_MODULES:
                    violations.append(f"upstream-framework-import:{path.relative_to(ROOT)}:{module}")

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

    return sorted(set(violations))


def main() -> int:
    violations = scan()
    report = {
        "check": "controlled-source-intake-batch-07-08",
        "clean_room_files": [str(path.relative_to(ROOT)) for path in CLEAN_ROOM_FILES],
        "manifest_files": [str(path.relative_to(ROOT)) for path in MANIFESTS],
        "passed": not violations,
        "violations": violations,
    }
    print(json.dumps(report, indent=2))
    return 0 if not violations else 1


if __name__ == "__main__":
    sys.exit(main())
