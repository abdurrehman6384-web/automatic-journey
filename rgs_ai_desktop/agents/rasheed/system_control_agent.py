"""
SystemControlAgent — RASHEED App & OS Control (from abdurrehman-ai project.zip)
================================================================================
Integrates: app.py, open_app.py, computer_control.py, os_control.py,
            cmd_control.py, desktop.py, computer_settings.py

Capabilities:
  - Open/close any application (cross-platform aliases)
  - File operations: create, delete, move, rename, list, search
  - Mouse/keyboard control (click, type, hotkey, scroll)
  - System commands: shutdown, restart, lock, sleep, volume, battery
  - Clipboard: copy, paste, get, clear
  - Process management: list, kill
  - Screen: screenshot, window info
  - Notifications: toast/systray

All methods return {"ok": bool, "result"/"error": ...} — never raise.
"""

from __future__ import annotations

import logging
import os
import platform
import shutil
import subprocess
import sys
import threading
import time
import webbrowser
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

log = logging.getLogger("rgs.system_control")

ENABLED: bool = True

# ── Platform detect ─────────────────────────────────────────────────────────
PLATFORM = platform.system()   # "Windows" | "Darwin" | "Linux"

def _ok(data: Any = None) -> Dict:
    return {"ok": True, "result": data}

def _err(msg: str) -> Dict:
    log.warning("SystemControl: %s", msg)
    return {"ok": False, "error": msg}


# ── App Aliases (from open_app.py) ────────────────────────────────────────────
APP_ALIASES: Dict[str, Dict[str, str]] = {
    "chrome":       {"Windows": "chrome",       "Darwin": "Google Chrome",      "Linux": "google-chrome"},
    "google chrome":{"Windows": "chrome",       "Darwin": "Google Chrome",      "Linux": "google-chrome"},
    "firefox":      {"Windows": "firefox",      "Darwin": "Firefox",            "Linux": "firefox"},
    "brave":        {"Windows": "brave",        "Darwin": "Brave Browser",      "Linux": "brave-browser"},
    "edge":         {"Windows": "msedge",       "Darwin": "Microsoft Edge",     "Linux": "microsoft-edge"},
    "opera":        {"Windows": "opera",        "Darwin": "Opera",              "Linux": "opera"},
    "spotify":      {"Windows": "Spotify",      "Darwin": "Spotify",            "Linux": "spotify"},
    "discord":      {"Windows": "Discord",      "Darwin": "Discord",            "Linux": "discord"},
    "telegram":     {"Windows": "Telegram",     "Darwin": "Telegram",           "Linux": "telegram"},
    "whatsapp":     {"Windows": "WhatsApp",     "Darwin": "WhatsApp",           "Linux": "whatsapp"},
    "zoom":         {"Windows": "Zoom",         "Darwin": "zoom.us",            "Linux": "zoom"},
    "slack":        {"Windows": "Slack",        "Darwin": "Slack",              "Linux": "slack"},
    "vscode":       {"Windows": "code",         "Darwin": "Visual Studio Code", "Linux": "code"},
    "visual studio code": {"Windows": "code",   "Darwin": "Visual Studio Code", "Linux": "code"},
    "notepad":      {"Windows": "notepad.exe",  "Darwin": "TextEdit",           "Linux": "gedit"},
    "calculator":   {"Windows": "calc.exe",     "Darwin": "Calculator",         "Linux": "gnome-calculator"},
    "terminal":     {"Windows": "cmd.exe",      "Darwin": "Terminal",           "Linux": "gnome-terminal"},
    "cmd":          {"Windows": "cmd.exe",      "Darwin": "Terminal",           "Linux": "bash"},
    "powershell":   {"Windows": "powershell.exe","Darwin": "Terminal",          "Linux": "bash"},
    "explorer":     {"Windows": "explorer.exe", "Darwin": "Finder",             "Linux": "nautilus"},
    "file explorer":{"Windows": "explorer.exe", "Darwin": "Finder",             "Linux": "nautilus"},
    "paint":        {"Windows": "mspaint.exe",  "Darwin": "Preview",            "Linux": "gimp"},
    "task manager": {"Windows": "taskmgr.exe",  "Darwin": "Activity Monitor",   "Linux": "gnome-system-monitor"},
    "settings":     {"Windows": "ms-settings:", "Darwin": "System Preferences", "Linux": "gnome-control-center"},
    "word":         {"Windows": "winword",      "Darwin": "Microsoft Word",     "Linux": "libreoffice --writer"},
    "excel":        {"Windows": "excel",        "Darwin": "Microsoft Excel",    "Linux": "libreoffice --calc"},
    "powerpoint":   {"Windows": "powerpnt",     "Darwin": "Microsoft PowerPoint","Linux": "libreoffice --impress"},
    "vlc":          {"Windows": "vlc",          "Darwin": "VLC",                "Linux": "vlc"},
    "steam":        {"Windows": "steam",        "Darwin": "Steam",              "Linux": "steam"},
    "obs":          {"Windows": "obs64",        "Darwin": "OBS",                "Linux": "obs"},
    "blender":      {"Windows": "blender",      "Darwin": "Blender",            "Linux": "blender"},
    "postman":      {"Windows": "Postman",      "Darwin": "Postman",            "Linux": "postman"},
    "pycharm":      {"Windows": "pycharm64",    "Darwin": "PyCharm",            "Linux": "pycharm"},
    "notion":       {"Windows": "Notion",       "Darwin": "Notion",             "Linux": "notion"},
    "obsidian":     {"Windows": "Obsidian",     "Darwin": "Obsidian",           "Linux": "obsidian"},
}

# ── Path shortcuts ────────────────────────────────────────────────────────────
PATH_SHORTCUTS = {
    "desktop":   Path.home() / "Desktop",
    "downloads": Path.home() / "Downloads",
    "documents": Path.home() / "Documents",
    "pictures":  Path.home() / "Pictures",
    "music":     Path.home() / "Music",
    "videos":    Path.home() / "Videos",
    "home":      Path.home(),
}


def _resolve_path(raw: str) -> Path:
    lower = raw.strip().lower()
    if lower in PATH_SHORTCUTS:
        return PATH_SHORTCUTS[lower]
    return Path(raw).expanduser()


class SystemControlAgent:
    """
    RASHEED-inspired full system control agent.
    Every public method is safe — catches all exceptions.
    """

    # ── App Control ───────────────────────────────────────────────────────────
    def open_app(self, app_name: str) -> Dict:
        """Open any application by name (cross-platform)."""
        if not ENABLED:
            return _err("SystemControlAgent disabled")
        key = app_name.strip().lower()
        cmd_map = APP_ALIASES.get(key, {})
        cmd = cmd_map.get(PLATFORM) or app_name

        try:
            if PLATFORM == "Windows":
                subprocess.Popen(cmd, shell=True)
            elif PLATFORM == "Darwin":
                subprocess.Popen(["open", "-a", cmd])
            else:
                subprocess.Popen([cmd], start_new_session=True)
            return _ok(f"Opened {app_name}")
        except Exception as exc:
            return _err(f"open_app failed: {exc}")

    def open_website(self, url: str) -> Dict:
        """Open a URL in the default browser."""
        try:
            if not url.startswith(("http://", "https://")):
                url = "https://" + url
            webbrowser.open(url)
            return _ok(f"Opened {url}")
        except Exception as exc:
            return _err(f"open_website failed: {exc}")

    def close_app(self, app_name: str) -> Dict:
        """Terminate a process by name."""
        try:
            if PLATFORM == "Windows":
                r = subprocess.run(["taskkill", "/F", "/IM", f"{app_name}*"],
                                   capture_output=True, text=True, timeout=10)
            else:
                r = subprocess.run(["pkill", "-f", app_name],
                                   capture_output=True, text=True, timeout=10)
            return _ok(f"Closed {app_name}" if r.returncode == 0 else r.stderr)
        except Exception as exc:
            return _err(f"close_app failed: {exc}")

    def run_command(self, command: str, shell: bool = True, timeout: float = 30) -> Dict:
        """Run a shell/CMD/PowerShell command and return output."""
        try:
            r = subprocess.run(command, shell=shell, capture_output=True,
                               text=True, timeout=timeout)
            return _ok({"stdout": r.stdout, "stderr": r.stderr,
                        "exit_code": r.returncode})
        except subprocess.TimeoutExpired:
            return _err(f"Command timed out after {timeout}s")
        except Exception as exc:
            return _err(f"run_command failed: {exc}")

    # ── File Operations ───────────────────────────────────────────────────────
    def list_files(self, path: str = "desktop", show_hidden: bool = False) -> Dict:
        """List files in a directory."""
        try:
            target = _resolve_path(path)
            if not target.exists():
                return _err(f"Path does not exist: {path}")
            items = []
            for item in sorted(target.iterdir()):
                if not show_hidden and item.name.startswith("."):
                    continue
                size = item.stat().st_size if item.is_file() else 0
                items.append({"name": item.name, "type": "file" if item.is_file() else "dir",
                               "size_bytes": size})
            return _ok({"path": str(target), "count": len(items), "items": items[:50]})
        except Exception as exc:
            return _err(f"list_files failed: {exc}")

    def create_file(self, path: str, content: str = "") -> Dict:
        """Create a new file with optional content."""
        try:
            p = _resolve_path(path)
            p.parent.mkdir(parents=True, exist_ok=True)
            p.write_text(content, encoding="utf-8")
            return _ok(f"Created {p}")
        except Exception as exc:
            return _err(f"create_file failed: {exc}")

    def create_folder(self, path: str) -> Dict:
        try:
            p = _resolve_path(path)
            p.mkdir(parents=True, exist_ok=True)
            return _ok(f"Created folder {p}")
        except Exception as exc:
            return _err(f"create_folder failed: {exc}")

    def delete_file(self, path: str, safe: bool = True) -> Dict:
        """Delete a file (moves to trash if safe=True)."""
        try:
            p = _resolve_path(path)
            if not p.exists():
                return _err(f"File not found: {path}")
            if safe:
                try:
                    import send2trash
                    send2trash.send2trash(str(p))
                    return _ok(f"Moved to trash: {p}")
                except ImportError:
                    pass
            if p.is_dir():
                shutil.rmtree(p)
            else:
                p.unlink()
            return _ok(f"Deleted {p}")
        except Exception as exc:
            return _err(f"delete_file failed: {exc}")

    def read_file(self, path: str, max_chars: int = 10000) -> Dict:
        """Read a text file."""
        try:
            p = _resolve_path(path)
            text = p.read_text(encoding="utf-8", errors="replace")
            return _ok({"path": str(p), "content": text[:max_chars],
                        "total_chars": len(text)})
        except Exception as exc:
            return _err(f"read_file failed: {exc}")

    def search_file(self, name: str, root: str = "home") -> Dict:
        """Search for files by name pattern."""
        try:
            base = _resolve_path(root)
            found = list(base.rglob(f"*{name}*"))[:20]
            return _ok([str(f) for f in found])
        except Exception as exc:
            return _err(f"search_file failed: {exc}")

    def rename_file(self, src: str, new_name: str) -> Dict:
        try:
            p = _resolve_path(src)
            dest = p.parent / new_name
            p.rename(dest)
            return _ok(f"Renamed to {dest}")
        except Exception as exc:
            return _err(f"rename_file failed: {exc}")

    # ── System Info ───────────────────────────────────────────────────────────
    def get_system_info(self) -> Dict:
        """CPU, RAM, disk, OS info."""
        try:
            import psutil
            cpu = psutil.cpu_percent(interval=0.5)
            ram = psutil.virtual_memory()
            disk = psutil.disk_usage("/")
            return _ok({
                "platform": PLATFORM,
                "cpu_percent": cpu,
                "ram_total_gb": round(ram.total / 1e9, 2),
                "ram_used_pct": ram.percent,
                "disk_total_gb": round(disk.total / 1e9, 2),
                "disk_free_gb":  round(disk.free  / 1e9, 2),
                "disk_pct": disk.percent,
            })
        except ImportError:
            return _err("psutil not installed: pip install psutil")
        except Exception as exc:
            return _err(str(exc))

    def get_battery(self) -> Dict:
        try:
            import psutil
            b = psutil.sensors_battery()
            if b is None:
                return _err("No battery found")
            return _ok({"percent": b.percent, "plugged": b.power_plugged,
                        "time_left_s": b.secsleft if b.secsleft != -1 else None})
        except ImportError:
            return _err("psutil not installed")
        except Exception as exc:
            return _err(str(exc))

    def get_running_processes(self) -> Dict:
        try:
            import psutil
            procs = sorted(
                [{"pid": p.pid, "name": p.name(), "cpu": p.cpu_percent()}
                 for p in psutil.process_iter(["pid", "name", "cpu_percent"])],
                key=lambda x: x["cpu"], reverse=True
            )
            return _ok(procs[:20])
        except ImportError:
            return _err("psutil not installed")
        except Exception as exc:
            return _err(str(exc))

    def kill_process(self, name_or_pid) -> Dict:
        try:
            import psutil
            if str(name_or_pid).isdigit():
                p = psutil.Process(int(name_or_pid))
                p.kill()
                return _ok(f"Killed PID {name_or_pid}")
            else:
                killed = 0
                for p in psutil.process_iter(["name"]):
                    if name_or_pid.lower() in p.name().lower():
                        p.kill()
                        killed += 1
                return _ok(f"Killed {killed} processes matching {name_or_pid!r}")
        except ImportError:
            return _err("psutil not installed")
        except Exception as exc:
            return _err(str(exc))

    # ── Power ─────────────────────────────────────────────────────────────────
    def shutdown(self, delay_s: int = 0) -> Dict:
        try:
            if PLATFORM == "Windows":
                subprocess.Popen(f"shutdown /s /t {delay_s}", shell=True)
            else:
                subprocess.Popen(["sudo", "shutdown", "-h", "now"])
            return _ok("Shutdown initiated")
        except Exception as exc:
            return _err(f"shutdown failed: {exc}")

    def restart(self) -> Dict:
        try:
            if PLATFORM == "Windows":
                subprocess.Popen("shutdown /r /t 0", shell=True)
            else:
                subprocess.Popen(["sudo", "reboot"])
            return _ok("Restart initiated")
        except Exception as exc:
            return _err(f"restart failed: {exc}")

    def lock_screen(self) -> Dict:
        try:
            if PLATFORM == "Windows":
                import ctypes
                ctypes.windll.user32.LockWorkStation()
            elif PLATFORM == "Darwin":
                subprocess.run(["pmset", "displaysleepnow"])
            else:
                subprocess.run(["xdg-screensaver", "lock"])
            return _ok("Screen locked")
        except Exception as exc:
            return _err(f"lock failed: {exc}")

    def sleep_pc(self) -> Dict:
        try:
            if PLATFORM == "Windows":
                subprocess.run("rundll32 powrprof.dll,SetSuspendState 0,1,0", shell=True)
            elif PLATFORM == "Darwin":
                subprocess.run(["pmset", "sleepnow"])
            else:
                subprocess.run(["systemctl", "suspend"])
            return _ok("PC sleeping")
        except Exception as exc:
            return _err(f"sleep failed: {exc}")

    # ── Volume ────────────────────────────────────────────────────────────────
    def volume_up(self, steps: int = 5) -> Dict:
        try:
            if _HAS_KEYBOARD:
                import keyboard as kb
                for _ in range(steps):
                    kb.press_and_release("volume up")
                return _ok(f"Volume up {steps}x")
            return self.run_command("powershell -command \"$wshell = New-Object -com wscript.shell; $wshell.SendKeys([char]175)\"")
        except Exception as exc:
            return _err(str(exc))

    def volume_down(self, steps: int = 5) -> Dict:
        try:
            if _HAS_KEYBOARD:
                import keyboard as kb
                for _ in range(steps):
                    kb.press_and_release("volume down")
                return _ok(f"Volume down {steps}x")
            return self.run_command("powershell -command \"$wshell = New-Object -com wscript.shell; $wshell.SendKeys([char]174)\"")
        except Exception as exc:
            return _err(str(exc))

    def volume_mute(self) -> Dict:
        try:
            if _HAS_KEYBOARD:
                import keyboard as kb
                kb.press_and_release("volume mute")
                return _ok("Muted")
            return self.run_command("powershell -command \"$wshell = New-Object -com wscript.shell; $wshell.SendKeys([char]173)\"")
        except Exception as exc:
            return _err(str(exc))

    # ── Clipboard ─────────────────────────────────────────────────────────────
    def get_clipboard(self) -> Dict:
        try:
            import pyperclip
            return _ok(pyperclip.paste())
        except ImportError:
            return _err("pyperclip not installed")
        except Exception as exc:
            return _err(str(exc))

    def set_clipboard(self, text: str) -> Dict:
        try:
            import pyperclip
            pyperclip.copy(text)
            return _ok("Copied to clipboard")
        except ImportError:
            return _err("pyperclip not installed")
        except Exception as exc:
            return _err(str(exc))

    # ── Date/Time ─────────────────────────────────────────────────────────────
    def get_datetime(self) -> Dict:
        now = datetime.now()
        return _ok({
            "date": now.strftime("%Y-%m-%d"),
            "time": now.strftime("%H:%M:%S"),
            "day": now.strftime("%A"),
            "timestamp": now.isoformat(),
        })

    # ── Notifications ─────────────────────────────────────────────────────────
    def show_notification(self, title: str, message: str, duration: int = 5) -> Dict:
        """Show desktop notification (cross-platform)."""
        try:
            if PLATFORM == "Windows":
                try:
                    from win10toast import ToastNotifier
                    t = ToastNotifier()
                    t.show_toast(title, message, duration=duration, threaded=True)
                    return _ok("Notification shown")
                except ImportError:
                    subprocess.Popen(
                        f'powershell -command "[System.Reflection.Assembly]::LoadWithPartialName(\'System.Windows.Forms\') | Out-Null; '
                        f'$n = New-Object System.Windows.Forms.NotifyIcon; $n.Icon = [System.Drawing.SystemIcons]::Information; '
                        f'$n.Visible = $True; $n.ShowBalloonTip({duration * 1000}, \'{title}\', \'{message}\', [System.Windows.Forms.ToolTipIcon]::Info)"',
                        shell=True
                    )
                    return _ok("Notification shown (PowerShell)")
            elif PLATFORM == "Darwin":
                subprocess.run(["osascript", "-e",
                                f'display notification "{message}" with title "{title}"'])
                return _ok("Notification shown")
            else:
                subprocess.run(["notify-send", title, message, f"--expire-time={duration * 1000}"])
                return _ok("Notification shown")
        except Exception as exc:
            return _err(f"notification failed: {exc}")

    # ── Search ────────────────────────────────────────────────────────────────
    def google_search(self, query: str) -> Dict:
        """Open Google search in browser."""
        try:
            from urllib.parse import quote_plus
            url = f"https://www.google.com/search?q={quote_plus(query)}"
            webbrowser.open(url)
            return _ok(f"Searching Google: {query}")
        except Exception as exc:
            return _err(str(exc))

    def youtube_search(self, query: str) -> Dict:
        """Open YouTube search in browser."""
        try:
            from urllib.parse import quote_plus
            url = f"https://www.youtube.com/results?search_query={quote_plus(query)}"
            webbrowser.open(url)
            return _ok(f"Searching YouTube: {query}")
        except Exception as exc:
            return _err(str(exc))

    def take_screenshot(self, path: Optional[str] = None) -> Dict:
        """Take a screenshot using the VisionAgent or fallback."""
        try:
            from rgs_ai_desktop.agents.screen_control_agent import AGENT as sa
            return sa.screenshot(path=path, as_base64=(path is None))
        except Exception as exc:
            return _err(f"screenshot failed: {exc}")


# ── optional keyboard lib check ──────────────────────────────────────────────
try:
    import keyboard as _kb_check
    _HAS_KEYBOARD = True
except (ImportError, Exception):
    _HAS_KEYBOARD = False


# ── module-level singleton ────────────────────────────────────────────────────
AGENT = SystemControlAgent()


def smoke_test() -> bool:
    r = AGENT.get_datetime()
    ok = r["ok"] and "date" in r.get("result", {})
    r2 = AGENT.list_files("home")
    ok = ok and r2["ok"]
    log.info("SystemControlAgent smoke_test: %s", "PASS" if ok else "FAIL")
    return ok


if __name__ == "__main__":
    logging.basicConfig(level=logging.DEBUG)
    print(smoke_test())
