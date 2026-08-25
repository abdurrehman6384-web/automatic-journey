"""A small, auditable LLM loop for driving a phone.

Deliberately *not* a framework. The look-act loop is ~60 lines, every action is
an explicit verb, and every step is logged -- which is what you want when the
thing being driven is someone's real phone.

    from androidctl import connect
    from androidctl.agent import DeviceAgent

    agent = DeviceAgent(connect(), llm=my_llm_callable)
    result = agent.run("Turn on Wi-Fi", max_steps=10)
    print(result.success, result.steps)

``llm`` is any ``callable(prompt: str) -> str``. To use RASHEED's existing
router:

    from actions.ai_brain import MultiLLM
    agent = DeviceAgent(connect(), llm=MultiLLM().smart_ask)
"""

from __future__ import annotations

import json
import logging
import re
from dataclasses import dataclass, field
from typing import Any, Callable, Dict, List, Optional

log = logging.getLogger("androidctl.agent")

__all__ = ["DeviceAgent", "AgentResult", "Step", "AgentActionError"]

SYSTEM_RULES = """You control an Android phone through a small set of actions.

You are given the current screen as a compact UI tree. Lines look like:
  [12] Button "Send" rid=send_btn clickable center=(960,1960)
The number in brackets is the element id.

Reply with EXACTLY ONE line, one of:
  tap <id>              tap that element by its [id]
  tap_xy <x> <y>        tap raw pixel coordinates (only if no id fits)
  swipe <up|down|left|right>
  type <text>           type into the focused field
  press <home|back|enter|recent|volume_up|volume_down>
  launch <package>      open an app by package name
  wait                  wait a moment, then look again
  done <summary>        the goal is complete
  fail <reason>         the goal cannot be completed

Rules:
- Prefer `tap <id>` over `tap_xy`. Never invent an id that is not on the screen.
- One action per reply. No prose, no markdown, no explanation.
- If the screen is not what you expected, use `wait` or `swipe` to recover.
"""


class AgentActionError(Exception):
    """The model produced an action we cannot execute."""


@dataclass
class Step:
    index: int
    app: str
    action: str
    args: str
    result: str
    error: Optional[str] = None
    llm_reply: Optional[str] = None

    def as_dict(self) -> Dict[str, Any]:
        return {
            "index": self.index, "app": self.app, "action": self.action,
            "args": self.args, "result": self.result, "error": self.error,
        }


@dataclass
class AgentResult:
    goal: str
    success: bool
    summary: str
    steps: List[Step] = field(default_factory=list)

    @property
    def step_count(self) -> int:
        return len(self.steps)

    def transcript(self) -> str:
        lines = [f"GOAL: {self.goal}", f"OUTCOME: {'success' if self.success else 'failed'}"
                 f" -- {self.summary}"]
        for s in self.steps:
            mark = "  ! " if s.error else "  - "
            lines.append(f"{mark}{s.index}. {s.action} {s.args}".rstrip()
                         + (f"   [{s.error}]" if s.error else ""))
        return "\n".join(lines)


class DeviceAgent:
    """Look-act loop over an :class:`androidctl.AndroidDevice`."""

    def __init__(self, device: Any, llm: Callable[[str], str],
                 max_nodes: int = 200, use_screenshot: bool = False,
                 on_step: Optional[Callable[[Step], None]] = None,
                 sleep_between: float = 0.8):
        self.device = device
        self.llm = llm
        self.max_nodes = max_nodes
        self.use_screenshot = use_screenshot
        self.on_step = on_step
        self.sleep_between = sleep_between

    # ------------------------------------------------------------------
    def run(self, goal: str, max_steps: int = 10,
            history: Optional[List[str]] = None) -> AgentResult:
        steps: List[Step] = []
        memory = list(history or [])

        for i in range(1, max_steps + 1):
            state = self.device.screen_state(max_nodes=self.max_nodes)
            app = state["app"].get("package", "?")
            prompt = self._build_prompt(goal, state, memory)

            reply = (self.llm(prompt) or "").strip()
            try:
                action, args = self.parse_action(reply)
            except AgentActionError as exc:
                # A malformed reply is a bad step, not a dead run: record it and
                # let the model see the screen again.
                action, args = "error", ""
                parse_error = str(exc)
            else:
                parse_error = None
            log.info("step %d [%s] -> %s %s", i, app, action, args)

            step = Step(index=i, app=app, action=action, args=args,
                        result="", llm_reply=reply, error=parse_error)
            if parse_error is None:
                try:
                    step.result = self._execute(action, args)
                except AgentActionError as exc:
                    step.error = str(exc)
                    step.result = "rejected"
                except Exception as exc:
                    step.error = f"{type(exc).__name__}: {exc}"
                    step.result = "error"
            else:
                step.result = "rejected"

            steps.append(step)
            memory.append(f"screen={app} action={action} {args} -> {step.result or step.error}")
            memory = memory[-6:]                     # bounded context

            if self.on_step:
                self.on_step(step)

            if action == "done":
                return AgentResult(goal, True, args, steps)
            if action == "fail":
                return AgentResult(goal, False, args, steps)

            self.device.wait_idle(self.sleep_between)

        return AgentResult(goal, False, f"reached max_steps={max_steps} without `done`", steps)

    # ------------------------------------------------------------------
    def _build_prompt(self, goal: str, state: Dict[str, Any], memory: List[str]) -> str:
        parts = [SYSTEM_RULES, f"\nGOAL: {goal}"]
        if memory:
            parts.append("\nWHAT I ALREADY DID:\n" + "\n".join(f"  {m}" for m in memory))
        parts.append(f"\nCURRENT APP: {state['app'].get('package')} / "
                     f"{state['app'].get('activity')}")
        parts.append(f"SCREEN SIZE: {state['window_size'][0]}x{state['window_size'][1]}")
        parts.append("\nCURRENT SCREEN:\n" + state["ui_tree"])
        if self.use_screenshot:
            parts.append("\n(a screenshot is attached separately)")
        parts.append("\nYOUR ONE ACTION:")
        return "\n".join(parts)

    # ------------------------------------------------------------------
    @staticmethod
    def parse_action(reply: str) -> tuple:
        """Turn a model reply into ``(verb, args)``.

        Handles the plain-verb format, a fenced code block, and JSON -- models
        drift, and a brittle parser turns a small format slip into a failed run.
        """
        text = (reply or "").strip()
        if not text:
            raise AgentActionError("empty reply from the model")

        # strip code fences / leading bullets
        text = re.sub(r"^```[a-zA-Z]*\s*|\s*```$", "", text.strip()).strip()
        text = re.sub(r"^[-*•]\s*", "", text)

        # JSON form: {"action": "tap", "id": 3}
        if text.startswith("{"):
            try:
                data = json.loads(text)
                verb = str(data.get("action") or data.get("verb") or "").lower()
                if verb == "tap" and "id" in data:
                    return "tap", str(data["id"])
                if verb == "tap_xy":
                    return "tap_xy", f"{data.get('x')} {data.get('y')}"
                arg = data.get("args") or data.get("arg") or data.get("value") or ""
                if isinstance(arg, (list, tuple)):
                    arg = " ".join(str(a) for a in arg)
                return (verb or "fail"), str(arg)
            except Exception:
                pass                                   # fall through to text parsing

        first, _, rest = text.partition("\n")          # one action only
        first = first.strip()
        verb, _, args = first.partition(" ")
        verb = verb.lower().strip(":")
        args = args.strip().strip('"')

        known = {"tap", "tap_xy", "swipe", "type", "press", "launch",
                 "wait", "done", "fail"}
        if verb not in known:
            raise AgentActionError(
                f"unknown action {verb!r} (expected one of {sorted(known)}). "
                f"Reply was: {text[:120]!r}"
            )
        return verb, args

    # ------------------------------------------------------------------
    def _execute(self, action: str, args: str) -> str:
        d = self.device
        if action == "tap":
            if not args.isdigit():
                raise AgentActionError(f"tap needs a numeric element id, got {args!r}")
            node = d.tap_element(int(args))
            return f"tapped [{args}] {node.label!r} at {node.center}"
        if action == "tap_xy":
            try:
                x, y = (int(float(v)) for v in args.split())
            except ValueError:
                raise AgentActionError(f"tap_xy needs '<x> <y>', got {args!r}") from None
            d.tap(x, y)
            return f"tapped ({x}, {y})"
        if action == "swipe":
            d.swipe_direction(args or "up")
            return f"swiped {args or 'up'}"
        if action == "type":
            if not args:
                raise AgentActionError("type needs text")
            d.type_text(args, clear=True)
            return f"typed {len(args)} chars"
        if action == "press":
            d.press(args or "home")
            return f"pressed {args or 'home'}"
        if action == "launch":
            if not args:
                raise AgentActionError("launch needs a package name")
            info = d.launch(args)
            return f"launched {info.get('package')}"
        if action == "wait":
            d.wait_idle(1.5)
            return "waited"
        if action in ("done", "fail"):
            return args
        raise AgentActionError(f"unhandled action {action!r}")


def from_rasheed_brain(device: Any, **kwargs) -> DeviceAgent:
    """Build an agent on RASHEED's existing ``MultiLLM`` router.

    Imported lazily so this module has no dependency on your backend.
    """
    try:
        from actions.ai_brain import MultiLLM          # your module
    except ImportError:
        from ai_brain import MultiLLM                  # when run from actions/
    return DeviceAgent(device, llm=MultiLLM().smart_ask, **kwargs)
