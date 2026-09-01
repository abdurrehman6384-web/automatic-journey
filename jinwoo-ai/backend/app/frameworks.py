"""Controlled adapter registry for optional multi-agent frameworks.

Jinwoo's local mission engine remains the one canonical orchestrator.  These
adapters deliberately expose discovery/status only in V1: an installed package
or sidecar never receives a mission automatically and cannot bypass the policy,
approval, workspace, or audit boundaries owned by Jinwoo.
"""

from __future__ import annotations

from dataclasses import dataclass
from importlib.util import find_spec
from shutil import which
from typing import Literal

from .schemas import FrameworkState, FrameworkStatus


@dataclass(frozen=True)
class FrameworkAdapter:
    """Metadata and safe availability check for one optional integration."""

    id: str
    label: str
    runtime: Literal["builtin", "python", "typescript-mcp"]
    purpose: str
    python_module: str | None = None
    executable: str | None = None

    def is_detected(self) -> bool:
        if self.python_module:
            return find_spec(self.python_module) is not None
        if self.executable:
            return which(self.executable) is not None
        return True

    def status(self) -> FrameworkStatus:
        if self.id == "jinwoo-native":
            return FrameworkStatus(
                id=self.id,
                label=self.label,
                runtime="builtin",
                state=FrameworkState.CANONICAL,
                execution_enabled=True,
                detail="Canonical local mission engine; policy, approval and audit controls stay here.",
            )

        detected = self.is_detected()
        state = FrameworkState.DETECTED if detected else FrameworkState.NOT_INSTALLED
        availability = "Detected locally" if detected else "Not installed"
        return FrameworkStatus(
            id=self.id,
            label=self.label,
            runtime=self.runtime,
            state=state,
            execution_enabled=False,
            detail=(
                f"{availability}; adapter execution is deliberately disabled in V1. "
                f"{self.purpose}"
            ),
        )


class FrameworkRegistry:
    """Single discovery point for integrations that may be enabled later.

    An explicit, version-pinned adapter implementation plus tests is required
    before a framework can become executable. This prevents independent agent
    loops from competing with the canonical Jinwoo mission lifecycle.
    """

    def __init__(self) -> None:
        self._adapters = (
            FrameworkAdapter(
                id="jinwoo-native",
                label="Jinwoo Native Engine",
                runtime="builtin",
                purpose="Visible Planner, Executor and Verifier mission flow.",
            ),
            FrameworkAdapter(
                id="swarms",
                label="Swarms",
                runtime="python",
                python_module="swarms",
                purpose="Reserved for selected hierarchical worker and specialist patterns.",
            ),
            FrameworkAdapter(
                id="agency-swarm",
                label="Agency-Swarm",
                runtime="python",
                python_module="agency_swarm",
                purpose="Reserved for organisation-style, policy-gated handoffs where compatible.",
            ),
            FrameworkAdapter(
                id="ruflo",
                label="Ruflo",
                runtime="typescript-mcp",
                executable="ruflo",
                purpose="Reserved for an optional local TypeScript/MCP developer-harness bridge.",
            ),
        )

    def statuses(self) -> list[FrameworkStatus]:
        return [adapter.status() for adapter in self._adapters]


frameworks = FrameworkRegistry()
