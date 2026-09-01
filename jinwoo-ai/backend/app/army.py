"""Logical Shadow Army directory and deterministic local mission routing."""

from __future__ import annotations

from dataclasses import dataclass

from .schemas import Mission, MissionStatus, RiskLevel, SafetyLevel, WorkerSpec


@dataclass(frozen=True)
class Commander:
    id: str
    name: str
    department: str
    safety: SafetyLevel
    keywords: tuple[str, ...]


COMMANDERS: tuple[Commander, ...] = (
    Commander("jinwoo", "Jinwoo", "Supreme Command", SafetyLevel.NO_DIRECT_TOOLS, ()),
    Commander("bellion", "Bellion", "Controller", SafetyLevel.NO_DIRECT_TOOLS, ("task", "plan", "coordinate")),
    Commander("igris", "Igris", "Development", SafetyLevel.APPROVAL_REQUIRED, ("code", "bug", "test", "python", "react", "api", "database", "build")),
    Commander("beru", "Beru", "Managers", SafetyLevel.NO_DIRECT_TOOLS, ("manage", "workflow", "organize", "roadmap")),
    Commander("tusk", "Tusk", "Features", SafetyLevel.APPROVAL_REQUIRED, ("ui", "design", "animation", "image", "video", "feature")),
    Commander("iron", "Iron", "Business", SafetyLevel.APPROVAL_REQUIRED, ("business", "marketing", "mvp", "brand", "campaign", "sales")),
    Commander("tank", "Tank", "Researchers", SafetyLevel.READ_ONLY, ("research", "search", "report", "data", "market", "compare")),
    Commander("kaisel", "Kaisel", "Upgrading", SafetyLevel.SANDBOXED, ("upgrade", "dependency", "repository", "repo", "improve")),
    Commander("jima", "Jima", "Scribes", SafetyLevel.APPROVAL_REQUIRED, ("document", "docs", "write", "proposal", "summary", "changelog")),
    Commander("greed", "Greed", "Security", SafetyLevel.SANDBOXED, ("security", "secret", "privacy", "encrypt", "audit")),
    Commander("shadow", "Shadow", "Quality Assurance", SafetyLevel.READ_ONLY, ("qa", "quality", "verify", "validate", "regression")),
    Commander("fang", "Fang", "Integration", SafetyLevel.APPROVAL_REQUIRED, ("integrate", "integration", "connect", "webhook", "service")),
    Commander("blades", "Blades", "Training", SafetyLevel.SANDBOXED, ("train", "evaluation", "prompt", "benchmark", "fine tune")),
    Commander("nox", "Nox", "Operations", SafetyLevel.APPROVAL_REQUIRED, ("schedule", "monitor", "operation", "resource", "daily")),
    Commander("ashborn", "Ashborn", "Innovation", SafetyLevel.SANDBOXED, ("innovate", "prototype", "experiment", "future")),
)

# The backend keeps the same final three-team hierarchy shown in Army HQ. The
# agents are logical templates, so this catalogue does not start 450 processes.
SUB_DEPARTMENTS: dict[str, tuple[str, ...]] = {
    "jinwoo": ("Mission Control", "Final Decision", "User Interface Layer"),
    "bellion": ("Routing and Queue", "Commander Coordination", "Mission Monitoring"),
    "igris": ("Core Engine", "Intelligence Layer", "Delivery and Safety"),
    "beru": ("Task Distribution", "Workflow Management", "Update and Maintenance"),
    "tusk": ("Creative Production", "Editing and Tools", "Agent Factory"),
    "iron": ("Business Planning", "Marketing and Growth", "MVP and Expansion"),
    "tank": ("Public Research", "Data Extraction", "Report Generation"),
    "kaisel": ("Tool Discovery", "Safe Integration", "Version Management"),
    "jima": ("Documentation", "Knowledge Base", "Report Writing"),
    "greed": ("Privacy Guard", "Secret Scanner", "Policy Enforcer"),
    "shadow": ("Testing", "Bug Hunting", "Regression"),
    "fang": ("API Linking", "Service Connection", "Module Integration"),
    "blades": ("Model Evaluation", "Prompt Engineering", "Agent Training"),
    "nox": ("Scheduling", "Resource Management", "Health Monitoring"),
    "ashborn": ("Experimentation", "Future Research", "Prototype Development"),
}

SUB_DEPARTMENTS_PER_COMMANDER = 3
AGENTS_PER_SUB_DEPARTMENT = 10

if set(SUB_DEPARTMENTS) != {commander.id for commander in COMMANDERS} or any(
    len(teams) != SUB_DEPARTMENTS_PER_COMMANDER for teams in SUB_DEPARTMENTS.values()
):
    raise RuntimeError("The Shadow Army must define exactly three sub-departments per commander")

WORKERS = [
    WorkerSpec(id="planner", name="Planner", responsibility="Creates a visible and bounded plan."),
    WorkerSpec(id="executor", name="Executor", responsibility="Produces a safe draft or approved action."),
    WorkerSpec(id="verifier", name="Verifier", responsibility="Checks evidence, quality and policy."),
]


IMPACTFUL_TERMS = (
    "delete", "remove", "overwrite", "write file", "terminal", "run command",
    "install", "uninstall", "send ", "publish", "upload", "payment", "mouse", "keyboard",
)


def select_commander(prompt: str) -> Commander:
    normalized = prompt.casefold()
    ranked = sorted(
        ((sum(word in normalized for word in commander.keywords), commander) for commander in COMMANDERS[1:]),
        key=lambda item: item[0],
        reverse=True,
    )
    return ranked[0][1] if ranked and ranked[0][0] else COMMANDERS[1]


def needs_approval(prompt: str, commander: Commander) -> bool:
    """Approval follows the proposed action, not the commander's label.

    Igris may safely analyse code and draft a patch. Applying that patch still
    needs an explicit request/approval. The commander safety label tells the UI
    what kind of operations the department *can* propose; it is not permission
    to block every read-only mission.
    """
    del commander
    normalized = prompt.casefold()
    return any(term in normalized for term in IMPACTFUL_TERMS)


def build_mission(prompt: str) -> Mission:
    commander = select_commander(prompt)
    approval = needs_approval(prompt, commander)
    risk = RiskLevel.HIGH if approval else RiskLevel.MEDIUM if commander.safety == SafetyLevel.SANDBOXED else RiskLevel.LOW
    return Mission(
        prompt=prompt,
        commander_id=commander.id,
        commander=commander.name,
        status=MissionStatus.AWAITING_APPROVAL if approval else MissionStatus.PLANNED,
        risk=risk,
        requires_approval=approval,
        steps=[
            f"{commander.name} scopes the mission and its data boundary.",
            "Planner creates a visible plan with an allowed-tool list.",
            "Wait for approval before an impactful action; otherwise prepare a safe draft.",
            "Verifier checks the result, evidence and audit record before delivery.",
        ],
        workers=WORKERS,
    )


def army_summary() -> dict[str, int]:
    departments = len(COMMANDERS)
    sub_departments = sum(len(teams) for teams in SUB_DEPARTMENTS.values())
    agents = sub_departments * AGENTS_PER_SUB_DEPARTMENT
    return {
        "departments": departments,
        "sub_departments": sub_departments,
        "logical_agents": agents,
        "worker_slots": agents * len(WORKERS),
    }
