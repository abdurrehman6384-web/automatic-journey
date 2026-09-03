"""Local availability controls for native planning skills.

Availability is deliberately narrower than execution: enabling a skill only
allows it to be selected into a future planning-only Jinwoo plan. It cannot
start a runtime, provider, device, process, browser, scanner or external agent.
"""

from __future__ import annotations

from threading import RLock

from .audit import AuditStore
from .schemas import SkillActivationResponse
from .skill_library import NativeSkillLibrary, SkillLibraryError, skill_library


class SkillActivationError(ValueError):
    """Raised when an availability control references an unknown native skill."""


class SkillActivationStore:
    """In-process control plane for explicit enabled/disabled native skill selection."""

    def __init__(self, audit: AuditStore | None = None, library: NativeSkillLibrary = skill_library) -> None:
        self._disabled_skill_ids: set[str] = set()
        self._lock = RLock()
        self._audit = audit
        self._library = library

    def disabled_skill_ids(self) -> frozenset[str]:
        with self._lock:
            return frozenset(self._disabled_skill_ids)

    def set_enabled(self, skill_id: str, enabled: bool) -> SkillActivationResponse:
        try:
            # Validate identity against the strict source-of-truth loader first.
            self._library.skill(skill_id)
        except SkillLibraryError as error:
            raise SkillActivationError("Unknown native skill") from error
        with self._lock:
            was_enabled = skill_id not in self._disabled_skill_ids
            if enabled:
                self._disabled_skill_ids.discard(skill_id)
            else:
                self._disabled_skill_ids.add(skill_id)
            current_disabled = frozenset(self._disabled_skill_ids)
        skill = self._library.skill(skill_id, current_disabled)
        changed = was_enabled != enabled
        state = "enabled for local planning selection" if enabled else "disabled from local planning selection"
        if self._audit is not None and changed:
            self._audit.record(
                "skill_library.availability_changed",
                f"A Jinwoo-owned planning skill was {state}; no skill or external runtime was executed.",
                mission_id=skill_id,
                actor="local-user",
            )
        return SkillActivationResponse(
            skill=skill,
            changed=changed,
            detail=(
                f"{skill.name} is {state}. This changes plan selection only; it does not activate a capability."
            ),
            external_runtime_invoked=False,
        )
