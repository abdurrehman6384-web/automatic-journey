"""Mission store: only a bounded, visible set of workers exists for each mission."""

from __future__ import annotations

from .army import build_mission
from .audit import AuditStore
from .schemas import Mission, MissionStatus


class MissionStore:
    def __init__(self, audit: AuditStore | None = None) -> None:
        self._missions: dict[str, Mission] = {}
        self._audit = audit

    def _record(self, event_type: str, mission: Mission, detail: str, *, actor: str = "jinwoo") -> None:
        if self._audit is not None:
            self._audit.record(event_type, detail, mission_id=mission.id, actor=actor)

    def create(self, prompt: str) -> Mission:
        mission = build_mission(prompt)
        self._missions[mission.id] = mission
        self._record(
            "mission.created",
            mission,
            f"Routed to {mission.commander}; approval required: {str(mission.requires_approval).lower()}.",
        )
        return mission

    def get(self, mission_id: str) -> Mission | None:
        return self._missions.get(mission_id)

    def list(self) -> list[Mission]:
        return sorted(self._missions.values(), key=lambda item: item.created_at, reverse=True)

    def approve(self, mission_id: str, approved_by: str = "local-user") -> Mission | None:
        mission = self._missions.get(mission_id)
        if mission is None:
            return None
        if mission.status == MissionStatus.AWAITING_APPROVAL:
            mission.status = MissionStatus.RUNNING
            self._record("mission.approved", mission, "Approval recorded before any tool execution.", actor=approved_by)
            # The actual executor remains intentionally absent until an allowed
            # desktop tool is connected. This transition is visible and auditable.
            mission.status = MissionStatus.COMPLETE
            mission.result = "Approval recorded. No unconfigured desktop tool was executed."
            self._record("mission.completed", mission, mission.result)
        return mission

    def cancel(self, mission_id: str, cancelled_by: str = "local-user") -> Mission | None:
        mission = self._missions.get(mission_id)
        if mission is None:
            return None
        mission.status = MissionStatus.CANCELLED
        mission.result = "Cancelled by the local user before execution."
        self._record("mission.cancelled", mission, mission.result, actor=cancelled_by)
        return mission
