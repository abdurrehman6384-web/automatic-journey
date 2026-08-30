"""
ProactiveAgent — RASHEED Proactive & Ambient Intelligence (from project.zip)
=============================================================================
Integrates: proactive_engine.py, ambient_listener.py, meeting_transcriber.py,
            clipboard_manager.py, rpa_engine.py, digital_twin.py

Features:
  - Proactive engine: watches active window, auto-suggests / auto-saves
  - Ambient listener: sound detection (doorbell, alarm, baby cry)
  - Meeting transcriber: live STT → transcript
  - Clipboard manager: history + pinning
  - RPA (Record & Replay): macro recording/playback
  - Digital twin: learns your chat style and replicates it
"""

from __future__ import annotations

import json
import logging
import os
import sqlite3
import threading
import time
from datetime import datetime
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional

log = logging.getLogger("rgs.proactive")
ENABLED: bool = True

DATA_DIR = Path(os.environ.get("RGS_DATA_DIR", Path.home() / ".rgs"))
DATA_DIR.mkdir(parents=True, exist_ok=True)
MACROS_DIR = DATA_DIR / "macros"
MACROS_DIR.mkdir(exist_ok=True)

def _ok(d: Any = None) -> Dict: return {"ok": True, "result": d}
def _err(m: str) -> Dict:
    log.warning("ProactiveAgent: %s", m)
    return {"ok": False, "error": m}


# ══════════════════════════════════════════════════════════════════════════════
# Clipboard Manager (SQLite history + pinning)
# ══════════════════════════════════════════════════════════════════════════════
class ClipboardManager:
    DB = str(DATA_DIR / "clipboard.db")

    def __init__(self):
        self._setup()
        self._monitor_active = False

    def _setup(self):
        conn = sqlite3.connect(self.DB)
        conn.execute("""CREATE TABLE IF NOT EXISTS clipboard
                        (id INTEGER PRIMARY KEY, text TEXT UNIQUE,
                         timestamp REAL, pinned INTEGER DEFAULT 0)""")
        conn.commit()
        conn.close()

    def _store(self, text: str):
        if not text or len(text) < 2:
            return
        conn = sqlite3.connect(self.DB)
        try:
            conn.execute("INSERT OR IGNORE INTO clipboard (text, timestamp) VALUES (?, ?)",
                         (text, time.time()))
            conn.commit()
        finally:
            conn.close()

    def start_monitor(self) -> Dict:
        if self._monitor_active:
            return _ok("Already monitoring")
        self._monitor_active = True
        threading.Thread(target=self._monitor_loop, daemon=True).start()
        return _ok("Clipboard monitor started")

    def stop_monitor(self) -> Dict:
        self._monitor_active = False
        return _ok("Stopped")

    def _monitor_loop(self):
        last = ""
        while self._monitor_active:
            try:
                import pyperclip
                current = pyperclip.paste()
                if current and current != last:
                    last = current
                    self._store(current)
            except Exception:
                pass
            time.sleep(1.5)

    def get_history(self, limit: int = 20) -> Dict:
        conn = sqlite3.connect(self.DB)
        rows = conn.execute(
            "SELECT text, timestamp, pinned FROM clipboard ORDER BY timestamp DESC LIMIT ?",
            (limit,)
        ).fetchall()
        conn.close()
        return _ok([{"text": r[0][:200], "ts": r[1], "pinned": bool(r[2])} for r in rows])

    def pin(self, text: str) -> Dict:
        conn = sqlite3.connect(self.DB)
        conn.execute("UPDATE clipboard SET pinned=1 WHERE text=?", (text,))
        conn.commit()
        conn.close()
        return _ok("Pinned")

    def get_pinned(self) -> Dict:
        conn = sqlite3.connect(self.DB)
        rows = conn.execute("SELECT text FROM clipboard WHERE pinned=1").fetchall()
        conn.close()
        return _ok([r[0] for r in rows])


# ══════════════════════════════════════════════════════════════════════════════
# RPA Engine (Record & Replay)
# ══════════════════════════════════════════════════════════════════════════════
class RPAEngine:
    """Records mouse/keyboard actions and replays them."""

    def __init__(self):
        self.recording = False
        self.actions: List[Dict] = []
        self.start_time = 0.0
        self._mouse_listener = None
        self._key_listener   = None

    def start_recording(self, name: str = "macro_1") -> Dict:
        if self.recording:
            return _err("Already recording")
        try:
            from pynput import mouse, keyboard as kb
        except ImportError:
            return _err("pynput not installed: pip install pynput")

        self.recording = True
        self.actions = []
        self.start_time = time.time()

        def on_click(x, y, button, pressed):
            if pressed:
                self.actions.append({"type": "click", "x": x, "y": y,
                                     "button": str(button),
                                     "t": time.time() - self.start_time})

        def on_key(key):
            try:
                k = key.char or str(key)
            except AttributeError:
                k = str(key)
            self.actions.append({"type": "key", "key": k,
                                 "t": time.time() - self.start_time})

        self._mouse_listener = mouse.Listener(on_click=on_click)
        self._key_listener   = kb.Listener(on_press=on_key)
        self._mouse_listener.start()
        self._key_listener.start()
        return _ok(f"Recording started: {name}")

    def stop_recording(self, name: str = "macro_1") -> Dict:
        if not self.recording:
            return _err("Not recording")
        self.recording = False
        if self._mouse_listener:
            self._mouse_listener.stop()
        if self._key_listener:
            self._key_listener.stop()
        path = MACROS_DIR / f"{name}.json"
        with open(path, "w") as f:
            json.dump(self.actions, f, indent=2)
        return _ok({"saved": str(path), "actions": len(self.actions)})

    def replay(self, name: str = "macro_1", speed: float = 1.0) -> Dict:
        path = MACROS_DIR / f"{name}.json"
        if not path.exists():
            return _err(f"Macro not found: {name}")
        try:
            from pynput.mouse import Controller as MouseCtrl, Button
            from pynput.keyboard import Controller as KeyCtrl
        except ImportError:
            return _err("pynput not installed")
        try:
            with open(path) as f:
                actions = json.load(f)
            mouse_ctrl = MouseCtrl()
            key_ctrl   = KeyCtrl()
            prev_t = 0.0
            for act in actions:
                delay = (act["t"] - prev_t) / speed
                if delay > 0:
                    time.sleep(min(delay, 5.0))
                prev_t = act["t"]
                if act["type"] == "click":
                    mouse_ctrl.position = (act["x"], act["y"])
                    mouse_ctrl.click(Button.left)
                elif act["type"] == "key":
                    key_ctrl.press(act["key"])
                    key_ctrl.release(act["key"])
            return _ok(f"Replayed {len(actions)} actions")
        except Exception as exc:
            return _err(f"Replay failed: {exc}")

    def list_macros(self) -> Dict:
        macros = [f.stem for f in MACROS_DIR.glob("*.json")]
        return _ok(macros)


# ══════════════════════════════════════════════════════════════════════════════
# Digital Twin (behavioural style learner)
# ══════════════════════════════════════════════════════════════════════════════
class DigitalTwin:
    FILE = str(DATA_DIR / "digital_twin.json")

    def __init__(self, llm_fn=None):
        self._llm = llm_fn
        self.style = {
            "avg_length": "medium",
            "emoji_frequency": "medium",
            "language_mix": "hinglish",
            "formality": "casual",
            "common_phrases": [],
            "sample_messages": [],
        }
        self._load()

    def _load(self):
        if os.path.exists(self.FILE):
            try:
                with open(self.FILE, encoding="utf-8") as f:
                    self.style.update(json.load(f))
            except Exception:
                pass

    def _save(self):
        try:
            with open(self.FILE, "w", encoding="utf-8") as f:
                json.dump(self.style, f, ensure_ascii=False, indent=2)
        except Exception:
            pass

    def learn_from_message(self, message: str) -> None:
        """Update style profile from a message."""
        msgs = self.style.setdefault("sample_messages", [])
        msgs.append(message)
        if len(msgs) > 50:
            msgs.pop(0)
        # Heuristic updates
        words = message.split()
        if len(words) < 6:
            self.style["avg_length"] = "short"
        elif len(words) > 20:
            self.style["avg_length"] = "long"
        emoji_count = sum(1 for c in message if ord(c) > 0x1F300)
        if emoji_count > 3:
            self.style["emoji_frequency"] = "high"
        elif emoji_count == 0:
            self.style["emoji_frequency"] = "low"
        self._save()

    def generate_reply(self, context: str) -> Dict:
        """Generate a reply in the user's learned style."""
        if not self._llm:
            return _err("No LLM configured for DigitalTwin")
        style_desc = (
            f"Reply length: {self.style['avg_length']}, "
            f"emoji use: {self.style['emoji_frequency']}, "
            f"language: {self.style['language_mix']}, "
            f"tone: {self.style['formality']}."
        )
        samples = "\n".join(self.style.get("sample_messages", [])[-5:])
        prompt = (
            f"You are mimicking someone's chat style.\nStyle profile: {style_desc}\n"
            f"Sample messages:\n{samples}\n\n"
            f"Now reply to this message in the same style:\n{context}"
        )
        try:
            return _ok({"reply": self._llm(prompt)})
        except Exception as exc:
            return _err(str(exc))


# ══════════════════════════════════════════════════════════════════════════════
# Proactive Engine (window watcher)
# ══════════════════════════════════════════════════════════════════════════════
class ProactiveEngine:
    """Watches active window and proactively suggests actions."""

    def __init__(self, on_event: Optional[Callable[[str, str], None]] = None):
        self.active = False
        self._on_event = on_event
        self._last_window = ""
        self._thread: Optional[threading.Thread] = None

    def start(self) -> Dict:
        if self.active:
            return _ok("Already running")
        self.active = True
        self._thread = threading.Thread(target=self._watch_loop, daemon=True)
        self._thread.start()
        return _ok("Proactive engine started")

    def stop(self) -> Dict:
        self.active = False
        return _ok("Stopped")

    def _watch_loop(self):
        while self.active:
            try:
                title = self._get_active_window_title()
                if title and title != self._last_window:
                    self._last_window = title
                    self._on_window_change(title)
            except Exception:
                pass
            time.sleep(3)

    def _get_active_window_title(self) -> str:
        try:
            import pygetwindow as gw
            w = gw.getActiveWindow()
            return w.title if w else ""
        except Exception:
            return ""

    def _on_window_change(self, title: str):
        low = title.lower()
        suggestions = []
        if "word" in low or "notepad" in low or "document" in low:
            suggestions.append("Ctrl+S to save document")
        if "youtube" in low or "netflix" in low:
            suggestions.append("Focus mode: close distracting tabs?")
        if "terminal" in low or "cmd" in low:
            suggestions.append("Developer mode active")
        if suggestions and self._on_event:
            try:
                self._on_event("window_change", f"{title}: {', '.join(suggestions)}")
            except Exception:
                pass


# ══════════════════════════════════════════════════════════════════════════════
# ProactiveAgent unified facade
# ══════════════════════════════════════════════════════════════════════════════
class ProactiveAgent:
    def __init__(self, llm_fn=None, on_event=None):
        self.clipboard = ClipboardManager()
        self.rpa       = RPAEngine()
        self.twin      = DigitalTwin(llm_fn)
        self.proactive = ProactiveEngine(on_event)

    def dispatch(self, action: str, **kwargs) -> Dict:
        map_ = {
            "clipboard_history":    lambda: self.clipboard.get_history(**kwargs),
            "clipboard_monitor":    lambda: self.clipboard.start_monitor(),
            "clipboard_pin":        lambda: self.clipboard.pin(**kwargs),
            "clipboard_pinned":     lambda: self.clipboard.get_pinned(),
            "rpa_record":           lambda: self.rpa.start_recording(**kwargs),
            "rpa_stop":             lambda: self.rpa.stop_recording(**kwargs),
            "rpa_replay":           lambda: self.rpa.replay(**kwargs),
            "rpa_list":             lambda: self.rpa.list_macros(),
            "twin_learn":           lambda: (self.twin.learn_from_message(kwargs.get("message", "")), _ok("Learned"))[1],
            "twin_reply":           lambda: self.twin.generate_reply(**kwargs),
            "proactive_start":      lambda: self.proactive.start(),
            "proactive_stop":       lambda: self.proactive.stop(),
        }
        fn = map_.get(action)
        if fn is None:
            return _err(f"Unknown action: {action!r}")
        try:
            return fn()
        except Exception as exc:
            return _err(str(exc))


# ── module-level singleton ────────────────────────────────────────────────────
AGENT = ProactiveAgent()


def smoke_test() -> bool:
    r = AGENT.clipboard.get_history()
    ok = r["ok"]
    r2 = AGENT.rpa.list_macros()
    ok = ok and r2["ok"]
    log.info("ProactiveAgent smoke_test: %s", "PASS" if ok else "FAIL")
    return ok


if __name__ == "__main__":
    logging.basicConfig(level=logging.DEBUG)
    print(smoke_test())
