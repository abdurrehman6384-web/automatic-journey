"""
Orchestration Core — RGS AI Desktop
=====================================
Merges:
  • Orkas Commander / dispatcher logic → task decomposition & routing
  • Agent event bus (publish/subscribe)
  • Plugin agent registry integration
  • Licensing gate (STARTER / PRO / GOD MODE)
  • Task queue with priority + dependency tracking

This is the SINGLE central router — all user requests flow through here
before reaching any agent plugin.
"""

from __future__ import annotations

import enum
import json
import logging
import queue
import threading
import time
import uuid
from dataclasses import dataclass, field
from typing import Any, Callable, Dict, List, Optional, Set

log = logging.getLogger("rgs.orchestration")


# ── Licensing ─────────────────────────────────────────────────────────────────
class LicenseTier(enum.Enum):
    STARTER  = "STARTER"
    PRO      = "PRO"
    GOD_MODE = "GOD_MODE"


# Feature gates per tier
_TIER_FEATURES: Dict[str, Set[str]] = {
    LicenseTier.STARTER.value: {
        "chat", "voice", "code_exec", "memory",
    },
    LicenseTier.PRO.value: {
        "chat", "voice", "code_exec", "memory",
        "browser_use", "screen_control", "vision", "knowledge_base",
    },
    LicenseTier.GOD_MODE.value: {
        "chat", "voice", "code_exec", "memory",
        "browser_use", "screen_control", "vision", "knowledge_base",
        "task_planning", "tool_calling", "android_control",
        "hot_swap_plugins", "unrestricted_code",
    },
}


class LicenseGate:
    def __init__(self, tier: LicenseTier = LicenseTier.STARTER):
        self._tier = tier

    @property
    def tier(self) -> LicenseTier:
        return self._tier

    @tier.setter
    def tier(self, t: LicenseTier) -> None:
        self._tier = t
        log.info("License tier changed to %s", t.value)

    def can_use(self, feature: str) -> bool:
        allowed = _TIER_FEATURES.get(self._tier.value, set())
        return feature in allowed

    def require(self, feature: str) -> None:
        if not self.can_use(feature):
            raise PermissionError(
                f"Feature '{feature}' requires {LicenseTier.PRO.value}+ "
                f"(current tier: {self._tier.value})"
            )

    def status(self) -> Dict:
        return {
            "tier": self._tier.value,
            "features": sorted(_TIER_FEATURES.get(self._tier.value, set())),
        }


# ── Event Bus (Orkas-inspired pub/sub) ────────────────────────────────────────
EventHandler = Callable[[str, Any], None]


class EventBus:
    """
    Lightweight publish/subscribe event bus.
    Decouples agents from each other — nobody imports nobody else.
    """

    def __init__(self):
        self._handlers: Dict[str, List[EventHandler]] = {}
        self._lock = threading.RLock()

    def subscribe(self, event: str, handler: EventHandler) -> None:
        with self._lock:
            self._handlers.setdefault(event, []).append(handler)

    def unsubscribe(self, event: str, handler: EventHandler) -> None:
        with self._lock:
            if event in self._handlers:
                try:
                    self._handlers[event].remove(handler)
                except ValueError:
                    pass

    def publish(self, event: str, data: Any = None) -> int:
        """Publish event to all subscribers.  Returns number of handlers called."""
        with self._lock:
            handlers = list(self._handlers.get(event, []))
        called = 0
        for h in handlers:
            try:
                h(event, data)
                called += 1
            except Exception as exc:
                log.error("EventBus handler error [%s]: %s", event, exc)
        return called

    def topics(self) -> List[str]:
        with self._lock:
            return list(self._handlers.keys())


# ── Task data structures (Orkas Commander pattern) ────────────────────────────
class TaskPriority(enum.IntEnum):
    LOW    = 0
    NORMAL = 5
    HIGH   = 10
    URGENT = 20


class TaskStatus(enum.Enum):
    PENDING    = "pending"
    RUNNING    = "running"
    DONE       = "done"
    FAILED     = "failed"
    CANCELLED  = "cancelled"


@dataclass(order=True)
class Task:
    priority: int = field(default=TaskPriority.NORMAL)
    id: str = field(default_factory=lambda: str(uuid.uuid4())[:8],
                    compare=False)
    goal: str = field(default="", compare=False)
    agent: str = field(default="", compare=False)          # target agent name
    arguments: Dict[str, Any] = field(default_factory=dict, compare=False)
    status: TaskStatus = field(default=TaskStatus.PENDING, compare=False)
    result: Optional[Any] = field(default=None, compare=False)
    error: Optional[str] = field(default=None, compare=False)
    created_at: float = field(default_factory=time.time, compare=False)
    completed_at: Optional[float] = field(default=None, compare=False)
    parent_id: Optional[str] = field(default=None, compare=False)

    def to_dict(self) -> Dict:
        return {
            "id": self.id,
            "goal": self.goal,
            "agent": self.agent,
            "priority": self.priority,
            "status": self.status.value,
            "result": self.result,
            "error": self.error,
            "created_at": self.created_at,
            "completed_at": self.completed_at,
        }


# ── Orchestrator ─────────────────────────────────────────────────────────────
class OrchestrationCore:
    """
    Central dispatcher — routes tasks to agents, enforces licensing, fires events.

    Inspired by Orkas Commander task-decomposition pattern:
      User request → decompose → sub-tasks → assign to agents → aggregate results

    Usage:
        orch = OrchestrationCore()
        orch.register_agent("code_exec",  capability="code_exec",  fn=exec_code)
        orch.dispatch("run python: print('hello')")
    """

    def __init__(self, license_gate: Optional[LicenseGate] = None):
        self._gate = license_gate or LicenseGate(LicenseTier.STARTER)
        self._bus = EventBus()
        self._agents: Dict[str, Dict] = {}        # name → {capability, fn, meta}
        self._task_queue: queue.PriorityQueue = queue.PriorityQueue()
        self._task_history: List[Task] = []
        self._history_lock = threading.RLock()
        self._worker_thread: Optional[threading.Thread] = None
        self._running = False

    # -- event bus passthrough ------------------------------------------------
    def subscribe(self, event: str, handler: EventHandler) -> None:
        self._bus.subscribe(event, handler)

    def publish(self, event: str, data: Any = None) -> None:
        self._bus.publish(event, data)

    # -- agent registry -------------------------------------------------------
    def register_agent(
        self,
        name: str,
        capability: str,
        fn: Callable,
        meta: Optional[Dict] = None,
    ) -> None:
        self._agents[name] = {
            "capability": capability,
            "fn": fn,
            "meta": meta or {},
            "calls": 0,
            "errors": 0,
        }
        log.info("Agent registered: %s (capability=%s)", name, capability)
        self._bus.publish("agent_registered", {"name": name, "capability": capability})

    def unregister_agent(self, name: str) -> bool:
        removed = self._agents.pop(name, None) is not None
        if removed:
            log.info("Agent unregistered: %s", name)
        return removed

    def agent_names(self) -> List[str]:
        return list(self._agents.keys())

    def agent_for_capability(self, capability: str) -> Optional[str]:
        for name, info in self._agents.items():
            if info["capability"] == capability:
                return name
        return None

    # -- task decomposition (Orkas Commander pattern) -------------------------
    def _decompose(self, goal: str, llm: Optional[Callable] = None) -> List[Dict]:
        """
        Break a high-level goal into sub-tasks.
        With LLM: structured decomposition.
        Without LLM: heuristic keyword routing.
        """
        if llm:
            try:
                prompt = (
                    f"Decompose this task into atomic sub-tasks for a desktop AI agent.\n"
                    f"Task: {goal}\n\n"
                    f"Available agents: {list(self._agents.keys())}\n\n"
                    f"Reply with JSON list: "
                    f'[{{"agent": "agent_name", "goal": "sub-task description", "args": {{}}}}]'
                    f"\nReply ONLY with JSON, no explanation."
                )
                raw = llm(prompt)
                # strip markdown fences
                raw = raw.strip().strip("```json").strip("```").strip()
                steps = json.loads(raw)
                return steps if isinstance(steps, list) else []
            except Exception as exc:
                log.warning("LLM decompose failed: %s — using heuristics", exc)

        # Heuristic routing (no LLM)
        goal_lower = goal.lower()
        steps = []
        if any(k in goal_lower for k in ["run", "execute", "python", "code", "script"]):
            steps.append({"agent": "code_exec", "goal": goal, "args": {}})
        elif any(k in goal_lower for k in ["browse", "open website", "search web", "http"]):
            steps.append({"agent": "browser", "goal": goal, "args": {}})
        elif any(k in goal_lower for k in ["screenshot", "click", "type on screen", "mouse"]):
            steps.append({"agent": "screen_control", "goal": goal, "args": {}})
        elif any(k in goal_lower for k in ["remember", "recall", "memory", "forget"]):
            steps.append({"agent": "memory", "goal": goal, "args": {}})
        elif any(k in goal_lower for k in ["voice", "say", "speak", "tts"]):
            steps.append({"agent": "voice", "goal": goal, "args": {}})
        elif any(k in goal_lower for k in ["read screen", "ocr", "what is on screen"]):
            steps.append({"agent": "vision", "goal": goal, "args": {}})
        else:
            # default: chat
            steps.append({"agent": "chat", "goal": goal, "args": {}})
        return steps

    # -- dispatch --------------------------------------------------------------
    def dispatch(
        self,
        goal: str,
        agent: Optional[str] = None,
        priority: int = TaskPriority.NORMAL,
        arguments: Optional[Dict] = None,
        llm: Optional[Callable] = None,
        blocking: bool = False,
        timeout: float = 30.0,
    ) -> Dict:
        """
        Dispatch a goal to one or more agents.

        If *agent* is specified, routes directly.
        Otherwise uses task decomposition (Orkas Commander pattern).

        Returns {"ok": bool, "results": [...], "task_id": str}
        """
        if agent:
            tasks = [{"agent": agent, "goal": goal, "args": arguments or {}}]
        else:
            tasks = self._decompose(goal, llm=llm)

        results = []
        for step in tasks:
            ag_name = step.get("agent", "chat")
            ag_info = self._agents.get(ag_name)
            if ag_info is None:
                results.append({"agent": ag_name, "ok": False,
                                 "error": f"Agent {ag_name!r} not registered"})
                continue
            # license check
            cap = ag_info["capability"]
            if not self._gate.can_use(cap):
                results.append({
                    "agent": ag_name, "ok": False,
                    "error": f"Feature '{cap}' not available on {self._gate.tier.value} tier"
                })
                continue

            task = Task(
                priority=-priority,   # PriorityQueue is min-heap; negate for max-priority
                goal=step.get("goal", goal),
                agent=ag_name,
                arguments={**step.get("args", {}), **(arguments or {})},
            )
            with self._history_lock:
                self._task_history.append(task)

            self._bus.publish("task_started", task.to_dict())

            # Execute inline (simple model — queue worker optionally used)
            try:
                task.status = TaskStatus.RUNNING
                t0 = time.monotonic()
                fn = ag_info["fn"]
                raw = fn(task.goal, **task.arguments)
                task.result = raw
                task.status = TaskStatus.DONE
                task.completed_at = time.monotonic()
                ag_info["calls"] += 1
                self._bus.publish("task_done", task.to_dict())
                results.append({"agent": ag_name, "ok": True,
                                 "result": raw, "task_id": task.id,
                                 "duration_s": round(time.monotonic() - t0, 3)})
            except PermissionError as exc:
                task.status = TaskStatus.FAILED
                task.error = str(exc)
                ag_info["errors"] += 1
                self._bus.publish("task_failed", task.to_dict())
                results.append({"agent": ag_name, "ok": False, "error": str(exc)})
            except Exception as exc:
                task.status = TaskStatus.FAILED
                task.error = str(exc)
                ag_info["errors"] += 1
                self._bus.publish("task_failed", task.to_dict())
                log.error("Task %s failed: %s", task.id, exc, exc_info=True)
                results.append({"agent": ag_name, "ok": False, "error": str(exc)})

        overall_ok = any(r["ok"] for r in results)
        return {"ok": overall_ok, "results": results}

    # -- status / history ------------------------------------------------------
    def status(self) -> Dict:
        with self._history_lock:
            recent = [t.to_dict() for t in self._task_history[-10:]]
        return {
            "license": self._gate.status(),
            "agents": {
                name: {
                    "capability": info["capability"],
                    "calls": info["calls"],
                    "errors": info["errors"],
                }
                for name, info in self._agents.items()
            },
            "recent_tasks": recent,
            "event_topics": self._bus.topics(),
        }

    def set_license_tier(self, tier: LicenseTier) -> None:
        self._gate.tier = tier
        self._bus.publish("license_changed", {"tier": tier.value})

    @property
    def license(self) -> LicenseGate:
        return self._gate


# ── module-level singleton ────────────────────────────────────────────────────
CORE = OrchestrationCore()


# ── smoke test ────────────────────────────────────────────────────────────────
def smoke_test() -> bool:
    orch = OrchestrationCore(LicenseGate(LicenseTier.GOD_MODE))

    events: List[str] = []
    orch.subscribe("task_done", lambda e, d: events.append(d["agent"]))

    orch.register_agent(
        "echo_agent", capability="chat",
        fn=lambda goal, **kw: f"echo:{goal}"
    )

    r = orch.dispatch("hello world", agent="echo_agent")
    ok = r["ok"] and r["results"][0]["result"] == "echo:hello world"
    ok = ok and "echo_agent" in events
    log.info("OrchestrationCore smoke_test: %s", "PASS" if ok else "FAIL")
    return ok


if __name__ == "__main__":
    logging.basicConfig(level=logging.DEBUG)
    print(smoke_test())
    import json as _json
    print(_json.dumps(CORE.status(), indent=2))
