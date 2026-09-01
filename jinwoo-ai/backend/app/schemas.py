"""Typed contracts shared by Jinwoo's local API routes."""

from __future__ import annotations

from datetime import datetime, timezone
from enum import Enum
from typing import Literal
from uuid import uuid4

from pydantic import BaseModel, Field


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


class FrameworkStatus(BaseModel):
    """Read-only status for an orchestration integration boundary."""

    id: str
    label: str
    runtime: Literal["builtin", "python", "typescript-mcp"]
    state: FrameworkState
    execution_enabled: bool
    detail: str


class WorkerSpec(BaseModel):
    id: Literal["planner", "executor", "verifier"]
    name: str
    responsibility: str


class MissionRequest(BaseModel):
    prompt: str = Field(min_length=2, max_length=8_000)
    preferred_provider: str | None = Field(default=None, max_length=64)


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


class MemoryCreateRequest(BaseModel):
    content: str = Field(min_length=2, max_length=2_000)
    kind: Literal["preference", "project", "note", "reminder"] = "note"
    consent: bool = False


class MemoryItem(BaseModel):
    id: int
    content: str
    kind: str
    created_at: datetime


class MemoryUpdateRequest(BaseModel):
    content: str = Field(min_length=2, max_length=2_000)
    kind: Literal["preference", "project", "note", "reminder"] = "note"
    consent: bool = False


class AuditEvent(BaseModel):
    id: int
    event_type: str
    mission_id: str | None = None
    actor: str
    detail: str
    created_at: datetime


class ChatRequest(BaseModel):
    message: str = Field(min_length=1, max_length=8_000)
    preferred_provider: str | None = Field(default=None, max_length=64)
    allow_cloud: bool = False


class ChatResponse(BaseModel):
    reply: str
    provider: str
    local_only: bool
