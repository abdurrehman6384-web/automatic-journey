"""Typed contracts shared by Jinwoo's local API routes."""

from __future__ import annotations

from datetime import datetime, timezone
from enum import Enum
from typing import Literal
from uuid import uuid4

from pydantic import BaseModel, Field, field_validator


def _require_non_blank(value: str) -> str:
    """Reject whitespace-only input at every API boundary that carries text."""
    if not value.strip():
        raise ValueError("Provide non-blank text.")
    return value


class SafetyLevel(str, Enum):
    READ_ONLY = "read-only"
    APPROVAL_REQUIRED = "approval-required"
    SANDBOXED = "sandboxed"
    NO_DIRECT_TOOLS = "no-direct-tools"


class MissionStatus(str, Enum):
    PLANNED = "planned"
    AWAITING_APPROVAL = "awaiting_approval"
    RUNNING = "running"
    COMPLETE = "complete"
    CANCELLED = "cancelled"


class RiskLevel(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


class ProviderState(str, Enum):
    READY = "ready"
    UNCONFIGURED = "unconfigured"
    OFFLINE = "offline"
    CHECKING = "checking"


class CoordinationPattern(str, Enum):
    """A visible topology choice for the native Shadow Army planning core."""

    HIERARCHICAL = "hierarchical"
    COMMANDER_COUNCIL = "commander-council"
    DEPENDENCY_GRAPH = "dependency-graph"
    BOUNDED_SWARM = "bounded-swarm"


class ShadowArmyFramework(BaseModel):
    """A non-executing multi-agent framework pattern selected for a plan."""

    id: str
    label: str
    category: str
    pattern_role: str
    implementation_status: str
    execution_enabled: bool = False


class ShadowArmyAgent(BaseModel):
    """A logical specialist seat, not a started process or model session."""

    id: str
    name: str
    commander_id: str
    division_id: str
    division: str
    specialty: str
    logical: bool = True
    runtime_started: bool = False


class ShadowArmyStage(BaseModel):
    """One visible state in a Planner → Executor → Verifier mission graph."""

    id: str
    label: str
    owner: str
    phase: Literal["intake", "route", "scope", "plan", "draft", "verify", "deliver"]
    detail: str
    requires_approval: bool = False


class ShadowArmyPlanRequest(BaseModel):
    prompt: str = Field(min_length=2, max_length=8_000)
    requested_logical_agents: int = Field(default=3, ge=1, le=450)
    coordination: CoordinationPattern = CoordinationPattern.HIERARCHICAL

    @field_validator("prompt")
    @classmethod
    def prompt_is_not_blank(cls, value: str) -> str:
        return _require_non_blank(value)


class ShadowArmyPlan(BaseModel):
    id: str = Field(default_factory=lambda: f"shadow-plan-{uuid4().hex[:10]}")
    prompt: str
    coordination: CoordinationPattern
    commander_id: str
    commander: str
    division_id: str
    division: str
    requested_logical_agents: int
    logical_agents_reserved: int
    displayed_logical_agents: int
    runtime_worker_cap: int = 3
    runtime_workers_started: int = 0
    risk: RiskLevel
    requires_approval: bool
    external_runtime_invoked: bool = False
    pattern_summary: str
    agents: list[ShadowArmyAgent]
    stages: list[ShadowArmyStage]
    frameworks: list[ShadowArmyFramework]
    guardrails: list[str]
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class ShadowArmyOverview(BaseModel):
    commanders: int
    divisions: int
    logical_agents: int
    worker_slots: int
    active_runtime_workers: int = 0
    runtime_cap_per_mission: int = 3
    all_external_runtimes_disabled: bool
    hierarchy: list[str]
    supported_patterns: list[CoordinationPattern]


class ProviderStatus(BaseModel):
    id: str
    label: str
    mode: Literal["local", "cloud", "memory"]
    state: ProviderState
    detail: str


class FrameworkState(str, Enum):
    CANONICAL = "canonical"
    NOT_INSTALLED = "not-installed"
    DETECTED = "detected"
    REFERENCE_ONLY = "reference-only"


class FrameworkStatus(BaseModel):
    """Read-only status for a controlled framework or advanced-skill boundary."""

    id: str
    label: str
    runtime: Literal[
        "builtin", "python", "typescript-mcp", "typescript-service", "container-sidecar", "go-cli", "go-service",
        "rust-cli", "desktop-client", "mobile-client", "skill-catalog",
    ]
    category: Literal[
        "orchestration", "workflow", "coding", "research", "web-collection", "memory", "automation", "security",
        "governance", "computer-use", "reference", "media",
    ]
    integration_batch: int
    owner_commander: str
    license: str
    source_url: str | None = None
    state: FrameworkState
    implementation_status: Literal[
        "active", "contract-ready", "license-review-required", "source-review-required", "reference-only", "archived-upstream", "queued",
    ]
    execution_enabled: bool
    capabilities: list[str] = Field(default_factory=list, max_length=8)
    activation_boundary: Literal["read-only", "approval-required", "sandboxed", "reference-only"] = "approval-required"
    detail: str


class FrameworkDryRunRequest(BaseModel):
    prompt: str = Field(min_length=2, max_length=8_000)
    requested_agents: int = Field(default=3, ge=1, le=450)

    @field_validator("prompt")
    @classmethod
    def prompt_is_not_blank(cls, value: str) -> str:
        return _require_non_blank(value)


class FrameworkDryRun(BaseModel):
    framework_id: str
    framework_label: str
    policy_outcome: Literal["safe-plan", "approval-required", "blocked"]
    requested_agents: int
    bounded_runtime_workers: int
    external_runtime_invoked: bool = False
    requires_approval: bool
    summary: str
    next_steps: list[str]


class ControlReviewCheck(BaseModel):
    id: str
    label: str
    passed: bool
    detail: str


class ControlReview(BaseModel):
    reviewed_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    all_passed: bool
    external_runtime_invoked: bool = False
    summary: str
    checks: list[ControlReviewCheck]


class WorkerSpec(BaseModel):
    id: Literal["planner", "executor", "verifier"]
    name: str
    responsibility: str


class MissionRequest(BaseModel):
    prompt: str = Field(min_length=2, max_length=8_000)
    preferred_provider: str | None = Field(default=None, max_length=64)

    @field_validator("prompt")
    @classmethod
    def prompt_is_not_blank(cls, value: str) -> str:
        return _require_non_blank(value)


class Mission(BaseModel):
    id: str = Field(default_factory=lambda: f"mission-{uuid4().hex[:10]}")
    prompt: str
    commander_id: str
    commander: str
    status: MissionStatus
    risk: RiskLevel
    requires_approval: bool
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    steps: list[str]
    workers: list[WorkerSpec]
    result: str | None = None


class ApprovalRequest(BaseModel):
    approved_by: str = Field(default="local-user", min_length=1, max_length=120)

    @field_validator("approved_by")
    @classmethod
    def actor_is_not_blank(cls, value: str) -> str:
        return _require_non_blank(value)


class MemoryCreateRequest(BaseModel):
    content: str = Field(min_length=2, max_length=2_000)
    kind: Literal["preference", "project", "note", "reminder"] = "note"
    consent: bool = False

    @field_validator("content")
    @classmethod
    def content_is_not_blank(cls, value: str) -> str:
        return _require_non_blank(value)


class MemoryItem(BaseModel):
    id: int
    content: str
    kind: str
    created_at: datetime


class MemoryUpdateRequest(BaseModel):
    content: str = Field(min_length=2, max_length=2_000)
    kind: Literal["preference", "project", "note", "reminder"] = "note"
    consent: bool = False

    @field_validator("content")
    @classmethod
    def content_is_not_blank(cls, value: str) -> str:
        return _require_non_blank(value)


class AuditEvent(BaseModel):
    id: int
    event_type: str
    mission_id: str | None = None
    actor: str
    detail: str
    created_at: datetime


class WorkspaceSelectionRequest(BaseModel):
    path: str = Field(min_length=1, max_length=4_096)


class WorkspaceStatus(BaseModel):
    configured: bool
    root_label: str | None = None
    read_only: bool = True
    detail: str


class WorkspaceEntry(BaseModel):
    name: str
    relative_path: str
    kind: Literal["file", "directory"]
    size_bytes: int | None = None


class WorkspaceAnalysisRequest(BaseModel):
    relative_path: str = Field(min_length=1, max_length=4_096)


class WorkspaceAnalysis(BaseModel):
    relative_path: str
    language: str
    size_bytes: int
    line_count: int
    todo_count: int
    fixme_count: int
    import_count: int
    symbol_count: int
    sha256: str
    truncated: bool


class WorkspaceSearchRequest(BaseModel):
    """A bounded filename-only search inside the selected read-only workspace."""

    query: str = Field(min_length=1, max_length=160)
    relative_path: str = Field(default=".", min_length=1, max_length=4_096)
    max_results: int = Field(default=50, ge=1, le=100)

    @field_validator("query", "relative_path")
    @classmethod
    def search_text_is_not_blank(cls, value: str) -> str:
        return _require_non_blank(value)


class WorkspaceSearch(BaseModel):
    query: str
    relative_path: str
    results: list[WorkspaceEntry]
    scanned_directories: int
    truncated: bool


class ResearchPlanRequest(BaseModel):
    topic: str = Field(min_length=2, max_length=2_000)
    framework_id: Literal["firecrawl", "firecrawl-web-agent", "crawl4ai"] = "crawl4ai"
    targets: list[str] = Field(default_factory=list, max_length=10)
    confirm_public_sources: bool = False

    @field_validator("topic")
    @classmethod
    def topic_is_not_blank(cls, value: str) -> str:
        return _require_non_blank(value)


class ResearchTarget(BaseModel):
    url: str
    hostname: str


class ResearchPlan(BaseModel):
    framework_id: str
    topic: str
    targets: list[ResearchTarget]
    external_fetch_started: bool = False
    requires_approval_for_fetch: bool = True
    safeguards: list[str]
    next_steps: list[str]


class SecurityScanPlanRequest(BaseModel):
    scanner_id: Literal["trufflehog", "gitleaks"] = "gitleaks"
    confirm_authorized: bool = False


class SecurityScanPlan(BaseModel):
    scanner_id: Literal["trufflehog", "gitleaks"]
    scanner_label: str
    workspace_configured: bool
    license_review_required: bool
    external_scan_started: bool = False
    requires_approval_for_scan: bool = True
    safeguards: list[str]
    next_steps: list[str]


class ChatRequest(BaseModel):
    message: str = Field(min_length=1, max_length=8_000)
    preferred_provider: str | None = Field(default=None, max_length=64)
    allow_cloud: bool = False

    @field_validator("message")
    @classmethod
    def message_is_not_blank(cls, value: str) -> str:
        return _require_non_blank(value)


class ChatResponse(BaseModel):
    reply: str
    provider: str
    local_only: bool
