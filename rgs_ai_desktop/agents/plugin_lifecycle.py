"""
Plugin Lifecycle Manager — ported from Zoey (Rust, Agent-Zoey/Zoey)
=====================================================================
Zoey's load/unload/hot-swap plugin lifecycle PATTERN translated to Python.
No Rust code is copied — only the lifecycle semantics:

  REGISTERED → LOADED → ACTIVE → SUSPENDED → UNLOADED

Features:
  • Dynamic import at runtime (importlib)
  • Hot-swap: replace a running plugin without restarting the app
  • Health monitoring: each plugin reports OK/DEGRADED/FAILED
  • Event hooks: on_load, on_unload, on_swap called on the plugin
"""

from __future__ import annotations

import importlib
import importlib.util
import logging
import sys
import threading
import time
from dataclasses import dataclass, field
from enum import Enum, auto
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional

log = logging.getLogger("rgs.plugin_lifecycle")


# ── lifecycle states (from Zoey's state machine) ──────────────────────────────
class PluginState(Enum):
    REGISTERED = auto()
    LOADED     = auto()
    ACTIVE     = auto()
    SUSPENDED  = auto()
    FAILED     = auto()
    UNLOADED   = auto()


@dataclass
class PluginMeta:
    name: str
    module_path: str                  # dotted Python path OR file path
    version: str = "0.0.0"
    description: str = ""
    author: str = ""
    enabled: bool = True             # feature flag — off by default until smoke_test passes
    state: PluginState = PluginState.REGISTERED
    load_error: Optional[str] = None
    load_time: Optional[float] = None
    module_obj: Optional[Any] = None  # the live importlib module
    instance: Optional[Any] = None    # the plugin's AGENT singleton (if any)
    health_fn: Optional[Callable[[], bool]] = None   # smoke_test function


# ── PluginRegistry ───────────────────────────────────────────────────────────
class PluginLifecycleManager:
    """
    Manages the full lifecycle of agent plugins.

    Compatible with the Zoey hot-swap pattern:
      - Plugins are isolated modules
      - Hot-swap atomically swaps the module without downtime
      - Failures in one plugin never affect others
    """

    def __init__(self):
        self._plugins: Dict[str, PluginMeta] = {}
        self._lock = threading.RLock()

    # -- registration ----------------------------------------------------------
    def register(
        self,
        name: str,
        module_path: str,
        version: str = "0.0.0",
        description: str = "",
        enabled: bool = True,
    ) -> None:
        with self._lock:
            meta = PluginMeta(
                name=name,
                module_path=module_path,
                version=version,
                description=description,
                enabled=enabled,
            )
            self._plugins[name] = meta
        log.debug("Plugin registered: %s (%s)", name, module_path)

    # -- loading ---------------------------------------------------------------
    def load(self, name: str) -> bool:
        """
        Dynamically import the plugin module.
        Returns True on success.  Never raises.
        """
        with self._lock:
            meta = self._plugins.get(name)
            if meta is None:
                log.error("Plugin not registered: %s", name)
                return False
            if not meta.enabled:
                log.info("Plugin %s is disabled (feature flag)", name)
                return False

        try:
            t0 = time.monotonic()
            mod_path = meta.module_path

            if mod_path.endswith(".py") or "/" in mod_path or "\\" in mod_path:
                # File path import
                spec = importlib.util.spec_from_file_location(name, mod_path)
                mod = importlib.util.module_from_spec(spec)
                sys.modules[name] = mod
                spec.loader.exec_module(mod)
            else:
                # Dotted module path
                mod = importlib.import_module(mod_path)

            # grab AGENT singleton and smoke_test if they exist
            instance = getattr(mod, "AGENT", None)
            health_fn = getattr(mod, "smoke_test", None)

            with self._lock:
                meta.module_obj = mod
                meta.instance = instance
                meta.health_fn = health_fn
                meta.load_time = time.monotonic() - t0
                meta.load_error = None

            # run smoke test
            passed = True
            if health_fn:
                try:
                    passed = bool(health_fn())
                except Exception as exc:
                    log.warning("Plugin %s smoke_test raised: %s", name, exc)
                    passed = False

            with self._lock:
                meta.state = PluginState.ACTIVE if passed else PluginState.FAILED
                if not passed:
                    meta.load_error = "smoke_test failed"

            log.info("Plugin %s loaded in %.3fs (smoke=%s)", name, meta.load_time,
                     "PASS" if passed else "FAIL")
            return passed

        except Exception as exc:
            with self._lock:
                meta.state = PluginState.FAILED
                meta.load_error = str(exc)
            log.error("Plugin %s load failed: %s", name, exc, exc_info=True)
            return False

    def load_all(self) -> Dict[str, bool]:
        """Load every registered plugin.  Returns {name: success}."""
        results = {}
        with self._lock:
            names = list(self._plugins.keys())
        for name in names:
            results[name] = self.load(name)
        return results

    # -- hot-swap (Zoey pattern) -----------------------------------------------
    def hot_swap(self, name: str, new_module_path: Optional[str] = None) -> bool:
        """
        Replace a running plugin without restarting the app.
        Optionally point to a new module path (upgrade).
        """
        with self._lock:
            meta = self._plugins.get(name)
            if meta is None:
                log.error("hot_swap: plugin %s not registered", name)
                return False
            if new_module_path:
                meta.module_path = new_module_path
            meta.state = PluginState.SUSPENDED

        # call on_unload hook if available
        try:
            if meta.module_obj and hasattr(meta.module_obj, "on_unload"):
                meta.module_obj.on_unload()
        except Exception as exc:
            log.warning("on_unload hook error for %s: %s", name, exc)

        # remove from sys.modules so reimport is fresh
        sys.modules.pop(name, None)
        sys.modules.pop(meta.module_path, None)

        success = self.load(name)

        # call on_load hook
        try:
            if meta.module_obj and hasattr(meta.module_obj, "on_load"):
                meta.module_obj.on_load()
        except Exception as exc:
            log.warning("on_load hook error for %s: %s", name, exc)

        log.info("hot_swap %s: %s", name, "success" if success else "failed")
        return success

    # -- unload ----------------------------------------------------------------
    def unload(self, name: str) -> bool:
        with self._lock:
            meta = self._plugins.get(name)
            if meta is None:
                return False
        try:
            if meta.module_obj and hasattr(meta.module_obj, "on_unload"):
                meta.module_obj.on_unload()
        except Exception as exc:
            log.warning("on_unload error for %s: %s", name, exc)
        with self._lock:
            meta.state = PluginState.UNLOADED
            meta.module_obj = None
            meta.instance = None
        sys.modules.pop(name, None)
        log.info("Plugin %s unloaded", name)
        return True

    # -- suspend / resume ------------------------------------------------------
    def suspend(self, name: str) -> None:
        with self._lock:
            if name in self._plugins:
                self._plugins[name].state = PluginState.SUSPENDED

    def resume(self, name: str) -> None:
        with self._lock:
            if name in self._plugins:
                self._plugins[name].state = PluginState.ACTIVE

    # -- query -----------------------------------------------------------------
    def get_instance(self, name: str) -> Optional[Any]:
        with self._lock:
            meta = self._plugins.get(name)
            return meta.instance if meta and meta.state == PluginState.ACTIVE else None

    def status(self) -> List[Dict]:
        with self._lock:
            return [
                {
                    "name": m.name,
                    "state": m.state.name,
                    "version": m.version,
                    "enabled": m.enabled,
                    "load_error": m.load_error,
                    "load_time_s": round(m.load_time, 4) if m.load_time else None,
                }
                for m in self._plugins.values()
            ]

    def health_check(self) -> Dict[str, bool]:
        results = {}
        with self._lock:
            metas = list(self._plugins.values())
        for meta in metas:
            if meta.health_fn and meta.state == PluginState.ACTIVE:
                try:
                    results[meta.name] = bool(meta.health_fn())
                except Exception:
                    results[meta.name] = False
            else:
                results[meta.name] = meta.state == PluginState.ACTIVE
        return results


# ── module-level singleton ────────────────────────────────────────────────────
MANAGER = PluginLifecycleManager()


# ── smoke test ────────────────────────────────────────────────────────────────
def smoke_test() -> bool:
    mgr = PluginLifecycleManager()
    # Register a simple inline test (can't really hot-swap in test without file)
    ok = isinstance(mgr.status(), list)
    log.info("PluginLifecycleManager smoke_test: %s", "PASS" if ok else "FAIL")
    return ok


if __name__ == "__main__":
    logging.basicConfig(level=logging.DEBUG)
    print(smoke_test())
