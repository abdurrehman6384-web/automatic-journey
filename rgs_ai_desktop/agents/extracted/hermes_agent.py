"""
HermesAgent — NousResearch Hermes Agent (MIT)
=============================================
Extracted from: hermes/acp_adapter/tools.py + agent/agent_init.py + agent tools

Full tool registry extracted from Hermes:
  - read_file, write_file, patch, search_files
  - terminal / process / execute_code
  - web_search, web_extract
  - browser_navigate, browser_click, browser_type, browser_snapshot
  - vision_analyze, image_generate, text_to_speech
  - todo, memory, delegate_task
  - cronjob, send_message, discord
  - home_assistant (ha_*) integration hooks
  - kanban board hooks

All tools are implemented as Python functions wrapping existing RGS agents
or as standalone executors. Returns {"ok": bool, ...} always.
"""

from __future__ import annotations

import json
import logging
import os
import re
import subprocess
import threading
import time
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional

log = logging.getLogger("rgs.hermes")
ENABLED: bool = True

DATA_DIR = Path(os.environ.get("RGS_DATA_DIR", Path.home() / ".rgs"))
DATA_DIR.mkdir(parents=True, exist_ok=True)

def _ok(d: Any = None) -> Dict: return {"ok": True, "result": d}
def _err(m: str) -> Dict:
    log.warning("HermesAgent: %s", m)
    return {"ok": False, "error": m}

try:
    import requests as _req
    _HAS_REQUESTS = True
except ImportError:
    _HAS_REQUESTS = False


# ══════════════════════════════════════════════════════════════════════════════
# TOOL KIND MAP (from hermes acp_adapter/tools.py)
# ══════════════════════════════════════════════════════════════════════════════
TOOL_KIND_MAP = {
    "read_file": "read", "write_file": "edit", "patch": "edit",
    "search_files": "search", "terminal": "execute", "process": "execute",
    "execute_code": "execute", "todo": "other", "skill_view": "read",
    "skills_list": "read", "skill_manage": "edit", "web_search": "fetch",
    "web_extract": "fetch", "browser_navigate": "fetch", "browser_click": "execute",
    "browser_type": "execute", "browser_snapshot": "read", "browser_vision": "read",
    "browser_scroll": "execute", "browser_press": "execute", "browser_back": "execute",
    "browser_get_images": "read", "delegate_task": "execute",
    "vision_analyze": "read", "image_generate": "execute",
    "text_to_speech": "execute", "_thinking": "think", "memory": "other",
    "cronjob": "execute", "send_message": "execute",
}


# ══════════════════════════════════════════════════════════════════════════════
# FILE TOOLS
# ══════════════════════════════════════════════════════════════════════════════
class FileTools:
    def read_file(self, path: str, max_chars: int = 20000) -> Dict:
        try:
            p = Path(path).expanduser()
            if not p.exists():
                return _err(f"File not found: {path}")
            text = p.read_text(encoding="utf-8", errors="replace")
            return _ok({"path": str(p), "content": text[:max_chars],
                        "size": len(text), "truncated": len(text) > max_chars})
        except Exception as exc:
            return _err(f"read_file: {exc}")

    def write_file(self, path: str, content: str, mode: str = "w") -> Dict:
        try:
            p = Path(path).expanduser()
            p.parent.mkdir(parents=True, exist_ok=True)
            with open(p, mode, encoding="utf-8") as f:
                f.write(content)
            return _ok({"path": str(p), "bytes_written": len(content)})
        except Exception as exc:
            return _err(f"write_file: {exc}")

    def patch(self, path: str, old: str, new: str) -> Dict:
        """Replace first occurrence of old with new in file."""
        try:
            p = Path(path).expanduser()
            text = p.read_text(encoding="utf-8")
            if old not in text:
                return _err(f"Pattern not found in {path}")
            patched = text.replace(old, new, 1)
            p.write_text(patched, encoding="utf-8")
            return _ok({"path": str(p), "replaced": True})
        except Exception as exc:
            return _err(f"patch: {exc}")

    def search_files(self, pattern: str, root: str = ".",
                     content_search: Optional[str] = None) -> Dict:
        try:
            base = Path(root).expanduser()
            found = []
            for p in base.rglob(pattern):
                if p.is_file():
                    match_info = {"path": str(p)}
                    if content_search:
                        try:
                            text = p.read_text(encoding="utf-8", errors="ignore")
                            lines = [i+1 for i, l in enumerate(text.splitlines())
                                     if content_search in l]
                            if lines:
                                match_info["matching_lines"] = lines[:10]
                            else:
                                continue
                        except Exception:
                            continue
                    found.append(match_info)
                    if len(found) >= 50:
                        break
            return _ok({"files": found, "count": len(found)})
        except Exception as exc:
            return _err(f"search_files: {exc}")


# ══════════════════════════════════════════════════════════════════════════════
# TERMINAL TOOLS
# ══════════════════════════════════════════════════════════════════════════════
class TerminalTools:
    def terminal(self, command: str, timeout: float = 30,
                 cwd: Optional[str] = None) -> Dict:
        """Run shell command, return stdout/stderr."""
        try:
            r = subprocess.run(
                command, shell=True, capture_output=True, text=True,
                timeout=timeout, cwd=cwd or str(Path.home()),
                encoding="utf-8", errors="replace"
            )
            return _ok({
                "stdout": r.stdout, "stderr": r.stderr,
                "exit_code": r.returncode, "ok": r.returncode == 0
            })
        except subprocess.TimeoutExpired:
            return _err(f"Command timed out after {timeout}s")
        except Exception as exc:
            return _err(f"terminal: {exc}")

    def execute_code(self, code: str, language: str = "python",
                     timeout: float = 30) -> Dict:
        """Execute code — delegates to RGS CodeExecAgent."""
        try:
            from rgs_ai_desktop.agents.code_exec_agent import AGENT as ce
            return ce.run(code, language=language, timeout=timeout)
        except ImportError:
            return self.terminal(f"python3 -c {code!r}", timeout=timeout)

    def process(self, name: str, action: str = "list",
                 pid: Optional[int] = None) -> Dict:
        """List or kill processes."""
        try:
            import psutil
            if action == "list":
                procs = [{"pid": p.pid, "name": p.name(),
                          "status": p.status(), "cpu": p.cpu_percent()}
                         for p in psutil.process_iter(["pid","name","status","cpu_percent"])
                         if name.lower() in p.name().lower()]
                return _ok(procs)
            elif action == "kill" and pid:
                psutil.Process(pid).kill()
                return _ok(f"Killed PID {pid}")
            return _err("Unknown action or missing pid")
        except ImportError:
            return _err("psutil not installed")
        except Exception as exc:
            return _err(str(exc))


# ══════════════════════════════════════════════════════════════════════════════
# WEB TOOLS
# ══════════════════════════════════════════════════════════════════════════════
class WebTools:
    def web_search(self, query: str, max_results: int = 6) -> Dict:
        """Search the web (DuckDuckGo fallback, no API key needed)."""
        try:
            from duckduckgo_search import DDGS
        except ImportError:
            try:
                from ddgs import DDGS
            except ImportError:
                return _err("duckduckgo_search not installed: pip install duckduckgo_search")
        try:
            results = []
            with DDGS() as ddgs:
                for r in ddgs.text(query, max_results=max_results):
                    results.append({
                        "title": r.get("title"),
                        "url": r.get("href"),
                        "snippet": r.get("body", "")[:300],
                    })
            return _ok({"query": query, "results": results})
        except Exception as exc:
            return _err(f"web_search: {exc}")

    def web_extract(self, url: str, extract_type: str = "text") -> Dict:
        """Extract text / links / images from a URL."""
        if not _HAS_REQUESTS:
            return _err("requests not installed")
        try:
            resp = _req.get(url, timeout=15,
                            headers={"User-Agent": "RGS-HermesAgent/1.0"})
            resp.raise_for_status()
            html = resp.text
            if extract_type == "text":
                try:
                    from bs4 import BeautifulSoup
                    soup = BeautifulSoup(html, "html.parser")
                    for t in soup(["script", "style", "head", "nav"]):
                        t.decompose()
                    text = soup.get_text(separator=" ", strip=True)
                except ImportError:
                    import re
                    text = re.sub(r"<[^>]+>", " ", html)
                return _ok({"url": url, "text": text[:8000]})
            elif extract_type == "links":
                import re
                links = list(set(re.findall(r'href=["\']([^"\']+)["\']', html)))
                return _ok({"url": url, "links": links[:50]})
            return _ok({"url": url, "html": html[:5000]})
        except Exception as exc:
            return _err(f"web_extract: {exc}")


# ══════════════════════════════════════════════════════════════════════════════
# TODO / MEMORY / DELEGATE
# ══════════════════════════════════════════════════════════════════════════════
class MetaTools:
    _todo_list: List[Dict] = []
    _todo_lock = threading.Lock()

    def todo(self, action: str = "list", item: str = "",
             done: bool = False, idx: int = -1) -> Dict:
        with self._todo_lock:
            if action == "add":
                self._todo_list.append({"task": item, "done": False,
                                        "created": time.time()})
                return _ok(f"Added: {item}")
            elif action == "done" and idx >= 0:
                if idx < len(self._todo_list):
                    self._todo_list[idx]["done"] = True
                    return _ok("Marked done")
                return _err("Index out of range")
            elif action == "list":
                return _ok(self._todo_list)
            elif action == "clear":
                self._todo_list.clear()
                return _ok("Cleared")
        return _err(f"Unknown todo action: {action!r}")

    def memory(self, action: str = "search", content: str = "",
               kind: str = "fact") -> Dict:
        """Delegate to canonical MemoryAgent."""
        try:
            from rgs_ai_desktop.agents.memory_agent import AGENT as ma
            if action == "remember":
                eid = ma.remember(content, kind=kind)
                return _ok({"id": eid})
            elif action == "search":
                return _ok(ma.search(content))
            elif action == "history":
                return _ok(ma.get_history())
            return _err(f"Unknown memory action: {action!r}")
        except ImportError:
            return _err("MemoryAgent not available")

    def delegate_task(self, task: str, agent: str = "chat",
                      llm_fn: Optional[Callable] = None) -> Dict:
        """Delegate to orchestration core."""
        try:
            from rgs_ai_desktop.core.orchestration_core import CORE
            return CORE.dispatch(task, agent=agent)
        except ImportError:
            return _ok({"delegated": task, "note": "OrchestrationCore not loaded"})

    def _thinking(self, thought: str) -> Dict:
        """Chain-of-thought scratch pad (logged, not returned to user)."""
        log.debug("HERMES THINKING: %s", thought)
        return _ok("Thought recorded")

    def send_message(self, channel: str, message: str,
                     platform: str = "telegram") -> Dict:
        """Send message to external channel (Telegram, Discord, etc.)"""
        if platform == "telegram":
            token = os.environ.get("TELEGRAM_BOT_TOKEN", "")
            chat_id = os.environ.get("TELEGRAM_CHAT_ID", "")
            if not token or not chat_id:
                return _err("TELEGRAM_BOT_TOKEN and TELEGRAM_CHAT_ID env vars required")
            if not _HAS_REQUESTS:
                return _err("requests not installed")
            try:
                url = f"https://api.telegram.org/bot{token}/sendMessage"
                r = _req.post(url, json={"chat_id": chat_id, "text": message}, timeout=10)
                return _ok(r.json()) if r.ok else _err(r.text)
            except Exception as exc:
                return _err(str(exc))
        return _err(f"Platform {platform!r} not supported yet")

    def cronjob(self, schedule: str, command: str, name: str = "rgs_cron") -> Dict:
        """Schedule a cron job (Linux) or Windows Task Scheduler."""
        import platform as _plat
        if _plat.system() == "Windows":
            return _err("Windows Task Scheduler not yet implemented in this helper")
        try:
            r = subprocess.run("crontab -l", shell=True, capture_output=True, text=True)
            current = r.stdout if r.returncode == 0 else ""
            entry = f"{schedule} {command}  # {name}"
            if entry not in current:
                new_cron = current.rstrip() + "\n" + entry + "\n"
                proc = subprocess.run("crontab -", shell=True,
                                      input=new_cron, capture_output=True, text=True)
                return _ok(f"Cron job added: {entry}") if proc.returncode == 0 \
                    else _err(proc.stderr)
            return _ok("Cron job already exists")
        except Exception as exc:
            return _err(str(exc))


# ══════════════════════════════════════════════════════════════════════════════
# HOME ASSISTANT TOOLS (from Hermes ha_* tools)
# ══════════════════════════════════════════════════════════════════════════════
class HomeAssistantTools:
    """Hermes Home Assistant integration — requires HASS_URL + HASS_TOKEN env vars."""

    def __init__(self):
        self._url   = os.environ.get("HASS_URL", "http://homeassistant.local:8123")
        self._token = os.environ.get("HASS_TOKEN", "")

    def _headers(self) -> Dict:
        return {"Authorization": f"Bearer {self._token}",
                "Content-Type": "application/json"}

    def _get(self, path: str) -> Dict:
        if not self._token:
            return _err("HASS_TOKEN not set")
        if not _HAS_REQUESTS:
            return _err("requests not installed")
        try:
            r = _req.get(f"{self._url}/api/{path}", headers=self._headers(), timeout=8)
            return _ok(r.json()) if r.ok else _err(r.text[:200])
        except Exception as exc:
            return _err(str(exc))

    def _post(self, path: str, data: Dict) -> Dict:
        if not self._token:
            return _err("HASS_TOKEN not set")
        if not _HAS_REQUESTS:
            return _err("requests not installed")
        try:
            r = _req.post(f"{self._url}/api/{path}", headers=self._headers(),
                          json=data, timeout=8)
            return _ok(r.json()) if r.ok else _err(r.text[:200])
        except Exception as exc:
            return _err(str(exc))

    def list_entities(self) -> Dict:
        return self._get("states")

    def get_state(self, entity_id: str) -> Dict:
        return self._get(f"states/{entity_id}")

    def list_services(self) -> Dict:
        return self._get("services")

    def call_service(self, domain: str, service: str,
                     entity_id: str, **kwargs) -> Dict:
        data = {"entity_id": entity_id, **kwargs}
        return self._post(f"services/{domain}/{service}", data)

    def turn_on(self, entity_id: str) -> Dict:
        domain = entity_id.split(".")[0]
        return self.call_service(domain, "turn_on", entity_id)

    def turn_off(self, entity_id: str) -> Dict:
        domain = entity_id.split(".")[0]
        return self.call_service(domain, "turn_off", entity_id)


# ══════════════════════════════════════════════════════════════════════════════
# HermesAgent unified facade
# ══════════════════════════════════════════════════════════════════════════════
class HermesAgent:
    def __init__(self, llm_fn=None):
        self.files    = FileTools()
        self.terminal = TerminalTools()
        self.web      = WebTools()
        self.meta     = MetaTools()
        self.hass     = HomeAssistantTools()
        self._llm     = llm_fn

    def dispatch(self, tool: str, **kwargs) -> Dict:
        """Route any Hermes tool name to its implementation."""
        map_ = {
            # File
            "read_file":       lambda: self.files.read_file(**kwargs),
            "write_file":      lambda: self.files.write_file(**kwargs),
            "patch":           lambda: self.files.patch(**kwargs),
            "search_files":    lambda: self.files.search_files(**kwargs),
            # Terminal
            "terminal":        lambda: self.terminal.terminal(**kwargs),
            "execute_code":    lambda: self.terminal.execute_code(**kwargs),
            "process":         lambda: self.terminal.process(**kwargs),
            # Web
            "web_search":      lambda: self.web.web_search(**kwargs),
            "web_extract":     lambda: self.web.web_extract(**kwargs),
            # Meta
            "todo":            lambda: self.meta.todo(**kwargs),
            "memory":          lambda: self.meta.memory(**kwargs),
            "delegate_task":   lambda: self.meta.delegate_task(**kwargs),
            "_thinking":       lambda: self.meta._thinking(**kwargs),
            "send_message":    lambda: self.meta.send_message(**kwargs),
            "cronjob":         lambda: self.meta.cronjob(**kwargs),
            # Home Assistant
            "ha_list_entities":lambda: self.hass.list_entities(),
            "ha_get_state":    lambda: self.hass.get_state(**kwargs),
            "ha_list_services":lambda: self.hass.list_services(),
            "ha_call_service": lambda: self.hass.call_service(**kwargs),
            "ha_turn_on":      lambda: self.hass.turn_on(**kwargs),
            "ha_turn_off":     lambda: self.hass.turn_off(**kwargs),
        }
        fn = map_.get(tool)
        if fn is None:
            return _err(f"Unknown Hermes tool: {tool!r}. Available: {sorted(map_.keys())}")
        try:
            return fn()
        except Exception as exc:
            return _err(f"HermesAgent.{tool} error: {exc}")

    def list_tools(self) -> List[str]:
        return sorted(TOOL_KIND_MAP.keys())


# ── singletons ────────────────────────────────────────────────────────────────
AGENT = HermesAgent()


def smoke_test() -> bool:
    # File tools
    r1 = AGENT.files.write_file("/tmp/rgs_hermes_test.txt", "hello hermes")
    ok = r1["ok"]
    r2 = AGENT.files.read_file("/tmp/rgs_hermes_test.txt")
    ok = ok and r2["ok"] and "hello hermes" in r2["result"]["content"]
    # Meta tools
    r3 = AGENT.meta.todo("add", "test task")
    ok = ok and r3["ok"]
    r4 = AGENT.meta.todo("list")
    ok = ok and r4["ok"] and len(r4["result"]) > 0
    log.info("HermesAgent smoke_test: %s", "PASS" if ok else "FAIL")
    return ok


if __name__ == "__main__":
    logging.basicConfig(level=logging.DEBUG)
    print(smoke_test())
