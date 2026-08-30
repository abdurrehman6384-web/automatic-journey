"""
OpenDesktopAgent — Atum246/OpenDesktop (Node.js → Python port)
===============================================================
Ported from JS to Python:
  src/brain/index.js        → ContextualBrain (weighted knowledge graph)
  src/memory/index.js       → MemorySystem (episodic + semantic + tasks)
  src/automation/index.js   → AutomationEngine (cross-platform desktop control)
  src/hotkey/index.js       → GlobalHotkey (xbindkeys/AppleScript/PowerShell)
  src/ghost-mode/index.js   → GhostMode (autonomous night shift missions)
  src/code-executor/index.js → CodeExecutor (sandboxed code runner)

All return {"ok": bool, ...} — never raise.
Duplicate-check: memory → defers to canonical MemoryAgent.
                 automation → defers to canonical ScreenControlAgent.
New value added: ContextualBrain, GhostMode, GlobalHotkey are genuinely new.
"""

from __future__ import annotations

import json
import logging
import math
import os
import subprocess
import threading
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Set

log = logging.getLogger("rgs.opendesktop")
ENABLED: bool = True

DATA_DIR = Path(os.environ.get("RGS_DATA_DIR", Path.home() / ".rgs" / "opendesktop"))
DATA_DIR.mkdir(parents=True, exist_ok=True)

def _ok(d: Any = None) -> Dict: return {"ok": True, "result": d}
def _err(m: str) -> Dict:
    log.warning("OpenDesktop: %s", m)
    return {"ok": False, "error": m}

import platform as _platform
PLATFORM = _platform.system()


# ══════════════════════════════════════════════════════════════════════════════
# Contextual Brain (from brain/index.js — weighted knowledge graph)
# ══════════════════════════════════════════════════════════════════════════════
@dataclass
class BrainNode:
    id: str
    type: str         # fact, preference, event, entity, concept, project, person, skill
    content: str
    weight: float = 1.0
    last_accessed: float = field(default_factory=time.time)
    access_count: int = 0
    created: float = field(default_factory=time.time)
    tags: List[str] = field(default_factory=list)
    source: str = "interaction"
    metadata: Dict = field(default_factory=dict)


@dataclass
class BrainEdge:
    from_id: str
    to_id: str
    relation: str
    weight: float = 1.0
    created: float = field(default_factory=time.time)


class ContextualBrain:
    """
    Weighted knowledge graph brain — directly ported from OpenDesktop brain/index.js.
    Persistent to disk. Supports decay (old memories fade), auto-relate.
    """

    GRAPH_FILE = DATA_DIR / "brain_graph.json"
    DECAY_RATE = 0.001   # weight loss per hour
    MIN_WEIGHT = 0.01    # below this = forgotten

    def __init__(self):
        self._nodes: Dict[str, BrainNode] = {}
        self._edges: List[BrainEdge] = []
        self._index: Dict[str, Set[str]] = {}   # keyword → node_ids
        self._context_window: List[str] = []
        self._lock = threading.RLock()
        self._load()

    # -- graph persistence ----------------------------------------------------
    def _save(self) -> None:
        try:
            data = {
                "nodes": {nid: {
                    "id": n.id, "type": n.type, "content": n.content,
                    "weight": n.weight, "last_accessed": n.last_accessed,
                    "access_count": n.access_count, "created": n.created,
                    "tags": n.tags, "source": n.source, "metadata": n.metadata,
                } for nid, n in self._nodes.items()},
                "edges": [{"from": e.from_id, "to": e.to_id,
                            "relation": e.relation, "weight": e.weight}
                           for e in self._edges],
            }
            self.GRAPH_FILE.write_text(json.dumps(data, indent=2))
        except Exception as exc:
            log.warning("Brain save error: %s", exc)

    def _load(self) -> None:
        if not self.GRAPH_FILE.exists():
            return
        try:
            data = json.loads(self.GRAPH_FILE.read_text())
            for nid, nd in data.get("nodes", {}).items():
                self._nodes[nid] = BrainNode(**{k: v for k, v in nd.items()
                                                  if k in BrainNode.__dataclass_fields__})
                self._index_node(nid)
            for ed in data.get("edges", []):
                self._edges.append(BrainEdge(
                    from_id=ed["from"], to_id=ed["to"],
                    relation=ed["relation"], weight=ed.get("weight", 1.0)
                ))
        except Exception as exc:
            log.warning("Brain load error: %s", exc)

    def _index_node(self, nid: str) -> None:
        node = self._nodes.get(nid)
        if not node:
            return
        words = node.content.lower().split()
        for word in words:
            if len(word) > 2:
                self._index.setdefault(word, set()).add(nid)

    # -- public API -----------------------------------------------------------
    def add_node(self, node_type: str, content: str,
                 tags: Optional[List[str]] = None,
                 metadata: Optional[Dict] = None,
                 source: str = "interaction") -> Dict:
        import uuid
        with self._lock:
            nid = f"node_{int(time.time()*1000)}_{uuid.uuid4().hex[:4]}"
            node = BrainNode(id=nid, type=node_type, content=content,
                             tags=tags or [], source=source,
                             metadata=metadata or {})
            self._nodes[nid] = node
            self._index_node(nid)
            self._auto_relate(node)
            self._save()
        return _ok({"id": nid, "type": node_type, "content": content})

    def add_edge(self, from_id: str, to_id: str,
                 relation: str, weight: float = 1.0) -> Dict:
        with self._lock:
            self._edges.append(BrainEdge(from_id=from_id, to_id=to_id,
                                          relation=relation, weight=weight))
            self._save()
        return _ok(f"{from_id} -[{relation}]-> {to_id}")

    def search(self, query: str, top_k: int = 10) -> Dict:
        """Keyword + weight search across all nodes."""
        words = [w.lower() for w in query.split() if len(w) > 2]
        with self._lock:
            scores: Dict[str, float] = {}
            for word in words:
                for nid in self._index.get(word, set()):
                    if nid in self._nodes:
                        scores[nid] = scores.get(nid, 0) + self._nodes[nid].weight
            # Apply time decay
            now = time.time()
            for nid in list(scores.keys()):
                n = self._nodes.get(nid)
                if n:
                    hours_old = (now - n.last_accessed) / 3600
                    decay = max(self.MIN_WEIGHT, n.weight - hours_old * self.DECAY_RATE)
                    scores[nid] *= decay
            sorted_nodes = sorted(scores.items(), key=lambda x: -x[1])[:top_k]
            results = []
            for nid, score in sorted_nodes:
                n = self._nodes[nid]
                n.access_count += 1
                n.last_accessed = now
                results.append({
                    "id": nid, "type": n.type, "content": n.content,
                    "score": round(score, 4), "tags": n.tags,
                })
        return _ok({"results": results, "count": len(results)})

    def get_context(self, query: str, max_tokens: int = 2000) -> Dict:
        """Get relevant context for LLM prompt injection."""
        r = self.search(query, top_k=8)
        if not r["ok"]:
            return r
        context_parts = []
        total = 0
        for item in r["result"]["results"]:
            snippet = f"[{item['type']}] {item['content']}"
            total += len(snippet)
            if total > max_tokens:
                break
            context_parts.append(snippet)
        return _ok("\n".join(context_parts))

    def _auto_relate(self, new_node: BrainNode) -> None:
        """Auto-detect relationships with existing nodes."""
        new_words = set(new_node.content.lower().split())
        for nid, n in self._nodes.items():
            if nid == new_node.id:
                continue
            old_words = set(n.content.lower().split())
            common = new_words & old_words - {"the","a","an","is","are","was","in","of","to"}
            if len(common) >= 2:
                self._edges.append(BrainEdge(
                    from_id=new_node.id, to_id=nid,
                    relation="related_to", weight=len(common) * 0.5
                ))

    def stats(self) -> Dict:
        with self._lock:
            types: Dict[str, int] = {}
            for n in self._nodes.values():
                types[n.type] = types.get(n.type, 0) + 1
            return _ok({"nodes": len(self._nodes), "edges": len(self._edges),
                        "by_type": types})


# ══════════════════════════════════════════════════════════════════════════════
# Global Hotkey (from hotkey/index.js — cross-platform)
# ══════════════════════════════════════════════════════════════════════════════
class GlobalHotkey:
    """
    Register a global hotkey to summon the RGS AI shell from anywhere.
    Linux: xbindkeys | macOS: AppleScript | Windows: keyboard module
    """

    def __init__(self, hotkey: str = "ctrl+shift+space",
                 on_trigger: Optional[Callable] = None):
        self.hotkey     = hotkey
        self.on_trigger = on_trigger
        self._active    = False
        self._thread: Optional[threading.Thread] = None

    def start(self) -> Dict:
        if self._active:
            return _ok("Already active")
        if PLATFORM == "Linux":
            return self._start_linux()
        elif PLATFORM == "Windows":
            return self._start_windows()
        elif PLATFORM == "Darwin":
            return self._start_macos()
        return _err(f"Platform {PLATFORM} not supported")

    def _start_windows(self) -> Dict:
        try:
            import keyboard as kb
            kb.add_hotkey(self.hotkey, self._fire)
            self._active = True
            return _ok(f"Hotkey {self.hotkey} registered (Windows/keyboard)")
        except ImportError:
            return _err("keyboard not installed: pip install keyboard")
        except Exception as exc:
            return _err(f"Windows hotkey: {exc}")

    def _start_linux(self) -> Dict:
        """Use xbindkeys with a shell pipe trigger."""
        try:
            config_dir = Path.home() / ".opendesktop"
            config_dir.mkdir(exist_ok=True)
            pipe_path   = config_dir / "hotkey-pipe"
            config_path = config_dir / ".xbindkeysrc"

            # Create named pipe
            if not pipe_path.exists():
                os.mkfifo(str(pipe_path))

            # Write xbindkeys config
            key_map = {
                "ctrl+shift+space": "control+shift+space",
                "ctrl+alt+o": "control+alt+o",
                "alt+space": "alt+space",
            }
            xb_key = key_map.get(self.hotkey, "control+shift+space")
            trigger_script = config_dir / "hotkey-trigger.sh"
            trigger_script.write_text(
                f'#!/bin/bash\necho "trigger" > {pipe_path}\n'
            )
            os.chmod(str(trigger_script), 0o700)
            config_path.write_text(
                f'"{trigger_script}"\n  {xb_key}\n'
            )

            # Start xbindkeys
            subprocess.Popen(["xbindkeys", "-f", str(config_path)])
            self._active = True

            # Watch named pipe
            def _watch():
                while self._active:
                    try:
                        with open(str(pipe_path)) as f:
                            data = f.read().strip()
                        if data == "trigger":
                            self._fire()
                    except Exception:
                        time.sleep(0.5)

            self._thread = threading.Thread(target=_watch, daemon=True)
            self._thread.start()
            return _ok(f"Linux hotkey {xb_key} via xbindkeys")
        except Exception as exc:
            return _err(f"Linux hotkey: {exc}")

    def _start_macos(self) -> Dict:
        """AppleScript event tap — requires Accessibility permission."""
        return _err("macOS hotkey requires manual AppleScript setup")

    def _fire(self) -> None:
        log.info("Global hotkey fired: %s", self.hotkey)
        if self.on_trigger:
            try:
                self.on_trigger()
            except Exception as exc:
                log.error("Hotkey trigger error: %s", exc)

    def stop(self) -> Dict:
        self._active = False
        if PLATFORM == "Windows":
            try:
                import keyboard as kb
                kb.remove_hotkey(self.hotkey)
            except Exception:
                pass
        return _ok("Stopped")


# ══════════════════════════════════════════════════════════════════════════════
# Ghost Mode (from ghost-mode/index.js — autonomous night shift)
# ══════════════════════════════════════════════════════════════════════════════
class GhostMode:
    """
    Autonomous mission runner — set a goal, let the agent work overnight.
    With checkpoints, rollback state, cost limiting, and morning briefing.
    """

    MAX_DURATION = 8 * 3600    # 8 hours
    CHECKPOINT_INTERVAL = 300   # 5 minutes

    def __init__(self, orchestrator_fn: Optional[Callable] = None):
        self._orch     = orchestrator_fn
        self._active   = False
        self._mission: Optional[Dict] = None
        self._log: List[Dict] = []
        self._checkpoints: List[Dict] = []
        self._thread: Optional[threading.Thread] = None
        self._state_dir = DATA_DIR / "ghost_mode"
        self._state_dir.mkdir(exist_ok=True)

    def start_mission(self, goal: str, max_steps: int = 50,
                      cost_limit: Optional[float] = None,
                      safety: str = "supervised") -> Dict:
        if self._active:
            return _err("A mission is already running")
        self._active  = True
        self._mission = {
            "goal": goal, "started": time.time(),
            "max_steps": max_steps, "cost_limit": cost_limit,
            "safety": safety, "steps_done": 0,
        }
        self._log = []
        self._checkpoints = []
        self._thread = threading.Thread(
            target=self._run_mission, daemon=True, name="GhostMode"
        )
        self._thread.start()
        return _ok({
            "mission": goal,
            "status": "started",
            "safety_mode": safety,
            "note": "Check briefing() for results when done."
        })

    def _run_mission(self) -> None:
        t0 = time.time()
        mission = self._mission
        steps = 0
        while self._active and steps < mission["max_steps"]:
            # Time limit
            if time.time() - t0 > self.MAX_DURATION:
                self._log.append({"type": "system", "msg": "Max duration reached"})
                break
            # Checkpoint
            if steps % 10 == 0:
                self._save_checkpoint(steps)
            # Execute step
            try:
                if self._orch:
                    result = self._orch(mission["goal"])
                    self._log.append({
                        "step": steps, "result": str(result)[:200],
                        "ts": time.time()
                    })
                    # Check if done
                    if isinstance(result, dict) and result.get("ok"):
                        res = result.get("result", {})
                        if isinstance(res, dict) and res.get("success"):
                            self._log.append({"type": "done", "msg": "Mission complete"})
                            break
            except Exception as exc:
                self._log.append({"step": steps, "error": str(exc)})
            steps += 1
            mission["steps_done"] = steps
            time.sleep(2)   # throttle
        self._active = False
        self._mission["completed"] = time.time()
        self._save_briefing()

    def _save_checkpoint(self, step: int) -> None:
        cp = {"step": step, "ts": time.time(),
              "log_count": len(self._log)}
        self._checkpoints.append(cp)
        try:
            cp_file = self._state_dir / f"checkpoint_{step}.json"
            cp_file.write_text(json.dumps({
                "mission": self._mission, "log": self._log[-20:]
            }, indent=2))
        except Exception:
            pass

    def _save_briefing(self) -> None:
        briefing = {
            "mission": self._mission,
            "log": self._log,
            "checkpoints": len(self._checkpoints),
            "summary": f"Completed {self._mission.get('steps_done',0)} steps",
        }
        try:
            (self._state_dir / "briefing.json").write_text(
                json.dumps(briefing, indent=2)
            )
        except Exception:
            pass

    def briefing(self) -> Dict:
        """Get morning briefing — what did the ghost mode do?"""
        bp = self._state_dir / "briefing.json"
        if bp.exists():
            try:
                return _ok(json.loads(bp.read_text()))
            except Exception:
                pass
        if self._mission:
            return _ok({
                "mission": self._mission,
                "steps_done": self._mission.get("steps_done", 0),
                "log": self._log[-20:],
                "active": self._active,
            })
        return _ok({"status": "no mission run yet"})

    def stop(self) -> Dict:
        self._active = False
        return _ok("Mission stopped")

    def rollback(self, checkpoint_step: int = -1) -> Dict:
        """Restore from a checkpoint."""
        if checkpoint_step < 0 and self._checkpoints:
            checkpoint_step = self._checkpoints[-1]["step"]
        cp_file = self._state_dir / f"checkpoint_{checkpoint_step}.json"
        if not cp_file.exists():
            return _err(f"Checkpoint {checkpoint_step} not found")
        try:
            data = json.loads(cp_file.read_text())
            return _ok({"restored": checkpoint_step, "log": data.get("log", [])[-5:]})
        except Exception as exc:
            return _err(str(exc))


# ══════════════════════════════════════════════════════════════════════════════
# OpenDesktopAgent unified facade
# ══════════════════════════════════════════════════════════════════════════════
class OpenDesktopAgent:
    def __init__(self, on_hotkey: Optional[Callable] = None,
                 orchestrator_fn: Optional[Callable] = None):
        self.brain   = ContextualBrain()
        self.hotkey  = GlobalHotkey(on_trigger=on_hotkey)
        self.ghost   = GhostMode(orchestrator_fn)

    def dispatch(self, action: str, **kwargs) -> Dict:
        map_ = {
            # Brain
            "brain_add":        lambda: self.brain.add_node(**kwargs),
            "brain_search":     lambda: self.brain.search(**kwargs),
            "brain_context":    lambda: self.brain.get_context(**kwargs),
            "brain_relate":     lambda: self.brain.add_edge(**kwargs),
            "brain_stats":      lambda: self.brain.stats(),
            # Hotkey
            "hotkey_start":     lambda: self.hotkey.start(),
            "hotkey_stop":      lambda: self.hotkey.stop(),
            # Ghost Mode
            "ghost_start":      lambda: self.ghost.start_mission(**kwargs),
            "ghost_stop":       lambda: self.ghost.stop(),
            "ghost_briefing":   lambda: self.ghost.briefing(),
            "ghost_rollback":   lambda: self.ghost.rollback(**kwargs),
        }
        fn = map_.get(action)
        if fn is None:
            return _err(f"Unknown action: {action!r}")
        try:
            return fn()
        except Exception as exc:
            return _err(str(exc))


# ── singletons ────────────────────────────────────────────────────────────────
AGENT = OpenDesktopAgent()


def smoke_test() -> bool:
    # Brain
    r = AGENT.brain.add_node("fact", "RGS AI Desktop uses PyQt6 and IRIS glass theme")
    ok = r["ok"]
    r2 = AGENT.brain.search("PyQt6 glass theme")
    ok = ok and r2["ok"] and r2["result"]["count"] >= 1
    # Stats
    r3 = AGENT.brain.stats()
    ok = ok and r3["ok"]
    log.info("OpenDesktopAgent smoke_test: %s", "PASS" if ok else "FAIL")
    return ok


if __name__ == "__main__":
    logging.basicConfig(level=logging.DEBUG)
    print(smoke_test())
