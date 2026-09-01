"""FastAPI entry point for the local Jinwoo command center."""

from __future__ import annotations

import sqlite3

from fastapi import FastAPI, HTTPException, Query, status

from .army import army_summary
from .audit import AuditStore
from .control import build_control_review
from .frameworks import FrameworkNotFoundError, frameworks
from .memory import LocalMemoryStore
from .orchestration import MissionStore
from .policy import ActionClass, classify_action
from .providers import ProviderError, ProviderGateway
from .research import ResearchPolicyError, build_research_plan
from .security import SecurityPlanError, build_security_scan_plan
from .shadow_army import ShadowArmyPolicyError, ShadowArmyStore
from .sensitive import contains_sensitive_value
from .schemas import (
    ApprovalRequest,
    AuditEvent,
    ChatRequest,
    ChatResponse,
    ControlReview,
    FrameworkDryRun,
    FrameworkDryRunRequest,
    FrameworkStatus,
    MemoryCreateRequest,
    MemoryItem,
    MemoryUpdateRequest,
    Mission,
    MissionRequest,
    ProviderStatus,
    ResearchPlan,
    ResearchPlanRequest,
    SecurityScanPlan,
    SecurityScanPlanRequest,
    ShadowArmyOverview,
    ShadowArmyPlan,
    ShadowArmyPlanRequest,
    WorkspaceAnalysis,
    WorkspaceAnalysisRequest,
    WorkspaceEntry,
    WorkspaceSelectionRequest,
    WorkspaceStatus,
)
from .settings import settings
from .workspace import WorkspaceError, WorkspaceStore

app = FastAPI(title="Jinwoo AI Local API", version="0.1.0")
audit = AuditStore(settings.data_dir)
missions = MissionStore(audit)
memory = LocalMemoryStore(settings.data_dir)
workspace = WorkspaceStore(settings.data_dir)
providers = ProviderGateway(settings)
shadow_army = ShadowArmyStore(audit)


@app.get("/health")
async def health() -> dict[str, object]:
    return {"ok": True, "mode": settings.mode, "local_only": settings.mode == "demo"}


@app.get("/api/army")
async def get_army() -> dict[str, object]:
    return {"ok": True, "summary": army_summary(), "active_missions": len(missions.list())}


@app.get("/api/shadow-army/overview", response_model=ShadowArmyOverview)
async def get_shadow_army_overview() -> ShadowArmyOverview:
    """Return native Army capacity and planning modes without starting workers."""
    return shadow_army.overview()


@app.get("/api/shadow-army/plans", response_model=list[ShadowArmyPlan])
async def list_shadow_army_plans() -> list[ShadowArmyPlan]:
    """List visible, local planning topologies; no framework runtime is queried."""
    return shadow_army.list()


@app.post("/api/shadow-army/plans", response_model=ShadowArmyPlan, status_code=status.HTTP_201_CREATED)
async def create_shadow_army_plan(request: ShadowArmyPlanRequest) -> ShadowArmyPlan:
    """Build a bounded multi-agent topology without invoking models or tools."""
    if contains_sensitive_value(request.prompt):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Credentials and one-time codes cannot be included in an Army plan.",
        )
    try:
        return shadow_army.create(request)
    except ShadowArmyPolicyError as error:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(error)) from error


@app.get("/api/providers", response_model=dict[str, list[ProviderStatus]])
async def get_providers() -> dict[str, list[ProviderStatus]]:
    return {"providers": providers.statuses()}


@app.get("/api/frameworks", response_model=dict[str, list[FrameworkStatus]])
async def get_frameworks() -> dict[str, list[FrameworkStatus]]:
    """Expose integration readiness without executing optional frameworks."""
    return {"frameworks": frameworks.statuses()}


@app.post("/api/frameworks/{framework_id}/dry-run", response_model=FrameworkDryRun)
async def dry_run_framework(framework_id: str, request: FrameworkDryRunRequest) -> FrameworkDryRun:
    """Prepare a bounded adapter plan; no upstream framework is invoked."""
    if contains_sensitive_value(request.prompt):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Credentials and one-time codes cannot be sent to an integration dry run.",
        )
    try:
        result = frameworks.dry_run(framework_id, request.prompt, request.requested_agents)
    except FrameworkNotFoundError as error:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Unknown framework adapter") from error
    audit.record(
        "integration.dry_run",
        f"{result.framework_label} prepared a {result.policy_outcome} with {result.bounded_runtime_workers} bounded workers; no upstream runtime was invoked.",
        actor="local-user",
    )
    return result


@app.post("/api/control/review", response_model=ControlReview)
async def review_control_plane() -> ControlReview:
    """Run the native aggregate control review without touching an upstream runtime."""
    try:
        audit.list(limit=1)
        audit_available = True
    except (OSError, ValueError, sqlite3.Error):  # surface a damaged local audit store, not hide it
        audit_available = False
    review = build_control_review(
        framework_statuses=frameworks.statuses(),
        workspace_status=workspace.status(),
        audit_available=audit_available,
    )
    if audit_available:
        try:
            audit.record(
                "control.review_completed",
                f"Native control review completed: {sum(check.passed for check in review.checks)}/{len(review.checks)} checks passed; no optional runtime was invoked.",
                actor="local-user",
            )
        except (OSError, sqlite3.Error):  # retain the report, but surface an audit persistence failure
            review = build_control_review(
                framework_statuses=frameworks.statuses(),
                workspace_status=workspace.status(),
                audit_available=False,
            )
    return review


@app.post("/api/security/scan-plan", response_model=SecurityScanPlan)
async def plan_security_scan(request: SecurityScanPlanRequest) -> SecurityScanPlan:
    """Prepare a Greed no-scan preflight without reading workspace content."""
    try:
        plan = build_security_scan_plan(
            scanner_id=request.scanner_id,
            workspace_status=workspace.status(),
            confirm_authorized=request.confirm_authorized,
        )
    except SecurityPlanError as error:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(error)) from error
    audit.record(
        "security.scan_plan_created",
        f"Greed prepared a no-scan {plan.scanner_label} plan for a selected workspace; no scanner runtime was invoked.",
        actor="local-user",
    )
    return plan


@app.post("/api/research/plan", response_model=ResearchPlan)
async def plan_research(request: ResearchPlanRequest) -> ResearchPlan:
    """Validate a Tank research request without opening or resolving any URL."""
    if contains_sensitive_value(request.topic) or any(contains_sensitive_value(target) for target in request.targets):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Credentials and one-time codes cannot be included in a research plan.",
        )
    try:
        plan = build_research_plan(
            framework_id=request.framework_id,
            topic=request.topic,
            targets=request.targets,
            confirm_public_sources=request.confirm_public_sources,
        )
    except ResearchPolicyError as error:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(error)) from error
    audit.record(
        "research.plan_created",
        f"Tank prepared a no-fetch {request.framework_id} research plan for {len(plan.targets)} approved public targets.",
        actor="local-user",
    )
    return plan


@app.get("/api/audit", response_model=list[AuditEvent])
async def list_audit_events() -> list[AuditEvent]:
    """Return redacted local mission decisions in newest-first order."""
    return audit.list()


@app.get("/api/workspace", response_model=WorkspaceStatus)
async def get_workspace() -> WorkspaceStatus:
    return workspace.status()


@app.put("/api/workspace", response_model=WorkspaceStatus)
async def select_workspace(request: WorkspaceSelectionRequest) -> WorkspaceStatus:
    try:
        selected = workspace.select(request.path)
    except WorkspaceError as error:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(error)) from error
    audit.record("workspace.selected", "A user-selected workspace is available for read-only diagnostics.", actor="local-user")
    return selected


@app.delete("/api/workspace", status_code=status.HTTP_204_NO_CONTENT)
async def clear_workspace() -> None:
    if workspace.clear():
        audit.record("workspace.cleared", "The selected workspace boundary was cleared.", actor="local-user")


@app.get("/api/workspace/files", response_model=list[WorkspaceEntry])
async def list_workspace_files(relative_path: str = Query(default=".", min_length=1, max_length=4_096)) -> list[WorkspaceEntry]:
    try:
        return workspace.list_entries(relative_path)
    except WorkspaceError as error:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(error)) from error


@app.post("/api/workspace/analyze", response_model=WorkspaceAnalysis)
async def analyze_workspace_file(request: WorkspaceAnalysisRequest) -> WorkspaceAnalysis:
    try:
        return workspace.analyze_text_file(request.relative_path)
    except WorkspaceError as error:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(error)) from error


@app.post("/api/chat", response_model=ChatResponse)
async def chat(request: ChatRequest) -> ChatResponse:
    decision = classify_action(request.message)
    if decision.action_class == ActionClass.BLOCKED:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=decision.reason)
    if contains_sensitive_value(request.message):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Credentials and one-time codes cannot be sent through Jinwoo chat.",
        )
    try:
        return await providers.chat(request.message, request.preferred_provider, request.allow_cloud)
    except ProviderError as error:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=str(error)) from error


@app.get("/api/missions", response_model=list[Mission])
async def list_missions() -> list[Mission]:
    return missions.list()


@app.post("/api/missions", response_model=Mission, status_code=status.HTTP_201_CREATED)
async def create_mission(request: MissionRequest) -> Mission:
    decision = classify_action(request.prompt)
    if decision.action_class == ActionClass.BLOCKED:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=decision.reason)
    return missions.create(request.prompt)


@app.post("/api/missions/{mission_id}/approve", response_model=Mission)
async def approve_mission(mission_id: str, request: ApprovalRequest) -> Mission:
    mission = missions.approve(mission_id, request.approved_by)
    if mission is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Mission not found")
    return mission


@app.post("/api/missions/{mission_id}/cancel", response_model=Mission)
async def cancel_mission(mission_id: str) -> Mission:
    mission = missions.cancel(mission_id)
    if mission is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Mission not found")
    return mission


@app.get("/api/memories", response_model=list[MemoryItem])
async def list_memories() -> list[MemoryItem]:
    return memory.list()


@app.post("/api/memories", response_model=MemoryItem, status_code=status.HTTP_201_CREATED)
async def create_memory(request: MemoryCreateRequest) -> MemoryItem:
    if not request.consent:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Explicit consent is required before saving memory")
    if contains_sensitive_value(request.content):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Sensitive values, credentials and one-time codes cannot be stored in Memory Vault.",
        )
    item = memory.add(request.content, request.kind)
    audit.record("memory.created", f"A consented {request.kind} memory was saved.", actor="local-user")
    return item


@app.patch("/api/memories/{memory_id}", response_model=MemoryItem)
async def update_memory(memory_id: int, request: MemoryUpdateRequest) -> MemoryItem:
    if not request.consent:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Explicit consent is required before replacing a memory")
    if contains_sensitive_value(request.content):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Sensitive values, credentials and one-time codes cannot be stored in Memory Vault.",
        )
    item = memory.update(memory_id, request.content, request.kind)
    if item is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Memory not found")
    audit.record("memory.updated", f"A consented {request.kind} memory was updated.", actor="local-user")
    return item


@app.delete("/api/memories/{memory_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_memory(memory_id: int) -> None:
    if not memory.delete(memory_id):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Memory not found")
    audit.record("memory.deleted", "A local memory was deleted by the user.", actor="local-user")
