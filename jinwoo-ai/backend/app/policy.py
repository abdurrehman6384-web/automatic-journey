"""Small, auditable policy gate for actions suggested by models or tools."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum


class ActionClass(str, Enum):
    READ_ONLY = "read-only"
    IMPACTFUL = "impactful"
    BLOCKED = "blocked"


@dataclass(frozen=True)
class PolicyDecision:
    action_class: ActionClass
    reason: str
    requires_approval: bool


BLOCKED_TERMS = (
    "bypass password", "bypass pin", "steal password", "steal credential",
    "keylogger", "hidden recording", "spyware", "disable antivirus",
)
IMPACTFUL_TERMS = (
    "delete", "overwrite", "write file", "save file", "terminal", "shell", "install", "uninstall",
    "send", "publish", "upload", "payment", "mouse", "keyboard", "settings",
)


def classify_action(text: str) -> PolicyDecision:
    normalized = text.casefold()
    if any(term in normalized for term in BLOCKED_TERMS):
        return PolicyDecision(ActionClass.BLOCKED, "The request crosses a security/privacy boundary.", False)
    if any(term in normalized for term in IMPACTFUL_TERMS):
        return PolicyDecision(ActionClass.IMPACTFUL, "This action could change data, a system or an external service.", True)
    return PolicyDecision(ActionClass.READ_ONLY, "Read-only analysis or drafting can be prepared safely.", False)
