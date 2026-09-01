"""FastAPI entry point for the local Jinwoo command center."""

from __future__ import annotations

from fastapi import FastAPI, HTTPException, status

from .army import army_summary
from .audit import AuditStore
from .frameworks import frameworks
from .memory import LocalMemoryStore
from .orchestration import MissionStore
from .policy import ActionClass, classify_action
from .providers import ProviderError, ProviderGateway
from .sensitive import contains_sensitive_value
from .schemas import ApprovalRequest, AuditEvent, ChatRequest, ChatResponse, FrameworkStatus, MemoryCreateRequest, MemoryItem, MemoryUpdateRequest, Mission, MissionRequest, ProviderStatus
from .settings import settings

app = FastAPI(title="Jinwoo AI Local API", version="0.1.0")
audit = AuditStore(settings.data_dir)
missions = MissionStore(audit)
memory = LocalMemoryStore(settings.data_dir)
providers = ProviderGateway(settings)


@app.get("/health")
async def health() -> dict[str, object]:
    return {"ok": True, "mode": settings.mode, "local_only": settings.mode == "demo"}


@app.get("/api/army")
async def get_army() -> dict[str, object]:
    return {"ok": True, "summary": army_summary(), "active_missions": len(missions.list())}


@app.get("/api/providers", response_model=dict[str, list[ProviderStatus]])
async def get_providers() -> dict[str, list[ProviderStatus]]:
    return {"providers": providers.statuses()}


@app.get("/api/frameworks", response_model=dict[str, list[FrameworkStatus]])
async def get_frameworks() -> dict[str, list[FrameworkStatus]]:
    """Expose integration readiness without executing optional frameworks."""
    return {"frameworks": frameworks.statuses()}


@app.get("/api/audit", response_model=list[AuditEvent])
async def list_audit_events() -> list[AuditEvent]:
    """Return redacted local mission decisions in newest-first order."""
    return audit.list()


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
