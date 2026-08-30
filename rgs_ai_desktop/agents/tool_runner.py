"""
ToolRunner — extracted from Goose (Apache-2.0, block/goose)
============================================================
Provides the extension / tool-calling pattern:
  • A registry of callable tools with JSON-schema signatures
  • Safe execution wrapper with timeout + structured error return
  • Hot-reload so new tools can be added while the app is running

Capability slot: TOOL-CALLING
Source inspiration: Goose ToolRunner extension pattern
"""

from __future__ import annotations

import inspect
import json
import logging
import threading
import time
from dataclasses import dataclass, field
from typing import Any, Callable, Dict, List, Optional

log = logging.getLogger("rgs.tool_runner")

# ── feature flag ──────────────────────────────────────────────────────────────
ENABLED: bool = True          # set False to disable without removing the module

# ── registry ──────────────────────────────────────────────────────────────────
@dataclass
class ToolSpec:
    name: str
    description: str
    fn: Callable
    parameters: Dict[str, Any] = field(default_factory=dict)
    timeout: float = 30.0

    def to_schema(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "description": self.description,
            "parameters": self.parameters,
        }


class ToolRegistry:
    """Thread-safe global registry of all callable tools."""

    def __init__(self) -> None:
        self._lock = threading.RLock()
        self._tools: Dict[str, ToolSpec] = {}

    # -- registration ----------------------------------------------------------

    def register(self, spec: ToolSpec) -> None:
        with self._lock:
            self._tools[spec.name] = spec
        log.debug("registered tool: %s", spec.name)

    def register_fn(
        self,
        fn: Callable,
        name: Optional[str] = None,
        description: Optional[str] = None,
        parameters: Optional[Dict] = None,
        timeout: float = 30.0,
    ) -> None:
        spec = ToolSpec(
            name=name or fn.__name__,
            description=description or (inspect.getdoc(fn) or ""),
            fn=fn,
            parameters=parameters or {},
            timeout=timeout,
        )
        self.register(spec)

    def unregister(self, name: str) -> bool:
        with self._lock:
            return self._tools.pop(name, None) is not None

    # -- lookup ----------------------------------------------------------------

    def get(self, name: str) -> Optional[ToolSpec]:
        with self._lock:
            return self._tools.get(name)

    def list_tools(self) -> List[Dict[str, Any]]:
        with self._lock:
            return [t.to_schema() for t in self._tools.values()]

    def names(self) -> List[str]:
        with self._lock:
            return list(self._tools.keys())

    # -- execution -------------------------------------------------------------

    def call(self, name: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute a named tool with *arguments*.
        Returns  {"ok": True,  "result": ...}
            or   {"ok": False, "error": "..."}
        Never raises.
        """
        if not ENABLED:
            return {"ok": False, "error": "ToolRunner is disabled (feature flag)"}

        spec = self.get(name)
        if spec is None:
            return {"ok": False, "error": f"unknown tool: {name!r}"}

        result: Dict[str, Any] = {}
        exc_holder: List[Exception] = []

        def _run() -> None:
            try:
                out = spec.fn(**arguments)
                result["value"] = out
            except Exception as exc:
                exc_holder.append(exc)

        t = threading.Thread(target=_run, daemon=True)
        t.start()
        t.join(timeout=spec.timeout)

        if t.is_alive():
            return {"ok": False, "error": f"tool {name!r} timed out after {spec.timeout}s"}
        if exc_holder:
            err = exc_holder[0]
            log.error("tool %r raised: %s", name, err, exc_info=err)
            return {"ok": False, "error": f"{type(err).__name__}: {err}"}
        return {"ok": True, "result": result.get("value")}


# ── module-level singleton ────────────────────────────────────────────────────
REGISTRY = ToolRegistry()


# ── convenience decorator ─────────────────────────────────────────────────────
def tool(
    name: Optional[str] = None,
    description: Optional[str] = None,
    parameters: Optional[Dict] = None,
    timeout: float = 30.0,
):
    """
    @tool()
    def my_tool(arg1: str) -> str:
        ...
    """
    def decorator(fn: Callable) -> Callable:
        REGISTRY.register_fn(fn, name=name, description=description,
                              parameters=parameters, timeout=timeout)
        return fn
    return decorator


# ── built-in system tools (registered at import time) ────────────────────────
@tool(name="list_tools", description="List all registered tools.", timeout=5.0)
def _builtin_list_tools() -> List[Dict]:
    return REGISTRY.list_tools()


@tool(name="echo", description="Echo back the input text.", timeout=5.0)
def _builtin_echo(text: str = "") -> str:
    return text


# ── smoke test ────────────────────────────────────────────────────────────────
def smoke_test() -> bool:
    r = REGISTRY.call("echo", {"text": "ping"})
    ok = r.get("ok") and r.get("result") == "ping"
    log.info("ToolRunner smoke_test: %s", "PASS" if ok else "FAIL")
    return ok


if __name__ == "__main__":
    logging.basicConfig(level=logging.DEBUG)
    print(smoke_test())
    print(json.dumps(REGISTRY.list_tools(), indent=2))
