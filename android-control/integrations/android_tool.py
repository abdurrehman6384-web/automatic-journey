"""Drop-in Android control for the RASHEED / RGS backend.

Your ``backend/actions/`` modules are plain module-level functions
(``Alert(Text)``, ``battery_Alert()``, ...). This file follows the same shape so
you can copy it straight in and ``from android_tool import ...`` alongside them.

Setup
-----
    # one time, from the android-control/ folder
    python -m venv .venv && .venv/bin/pip install -r requirements.txt

    # copy this file into your backend
    cp integrations/android_tool.py "<project>/costem agent/backend/actions/android_tool.py"

    # make androidctl importable (set once, or add to your .env)
    set ANDROIDCTL_HOME=C:\\path\\to\\android-control        (Windows)
    export ANDROIDCTL_HOME=/path/to/android-control          (Linux/macOS)

Usage
-----
    from android_tool import PHONE, android_available

    if android_available():
        PHONE.tap(540, 1200)
        PHONE.screenshot("shot.png")
        print(PHONE.ui_tree())          # compact text tree
        print(PHONE.shell("getprop ro.product.model").output)
        PHONE.launch("com.whatsapp")

Every function degrades gracefully: with no phone attached it returns a clear
error string instead of raising into your main loop.
"""

from __future__ import annotations

import os
import sys
import threading
from typing import Any, Dict, List, Optional

# ---------------------------------------------------------------------------
# locate the androidctl package
# ---------------------------------------------------------------------------
_HERE = os.path.dirname(os.path.abspath(__file__))

for _candidate in (
    os.environ.get("ANDROIDCTL_HOME", ""),
    _HERE,                                                    # if already inside android-control
    os.path.join(_HERE, "..", ".."),                          # backend/actions -> android-control
    os.path.abspath(os.path.join(_HERE, "..")),
):
    if _candidate and os.path.isfile(os.path.join(_candidate, "androidctl", "__init__.py")):
        if _candidate not in sys.path:
            sys.path.insert(0, os.path.abspath(_candidate))
        break

try:
    from androidctl import DeviceManager, AndroidCtlError, connect  # noqa: E402
    _IMPORT_ERROR: Optional[str] = None
except Exception as _exc:                                       # pragma: no cover
    DeviceManager = None                                        # type: ignore[assignment]
    AndroidCtlError = Exception                                 # type: ignore[assignment]
    connect = None                                              # type: ignore[assignment]
    _IMPORT_ERROR = f"{type(_exc).__name__}: {_exc}"


# ---------------------------------------------------------------------------
# lazy, thread-safe device handle
# ---------------------------------------------------------------------------
class PhoneProxy:
    """A module-level handle that connects on first real use.

    Importing this module never touches adb, so your app still starts with no
    phone plugged in. The connection is cached and re-established if it breaks.
    """

    def __init__(self, serial: Optional[str] = None):
        self._serial = serial
        self._device = None
        self._mgr: Optional[Any] = None
        self._lock = threading.RLock()

    # -- lifecycle -----------------------------------------------------
    @property
    def manager(self) -> Any:
        if self._mgr is None:
            if DeviceManager is None:
                raise RuntimeError(f"androidctl is not importable: {_IMPORT_ERROR}")
            self._mgr = DeviceManager()
        return self._mgr

    def _get(self):
        with self._lock:
            if self._device is None:
                self._device = self.manager.connect(self._serial)
            return self._device

    def reset(self) -> None:
        """Forget the cached connection (call after unplugging / re-authorising)."""
        with self._lock:
            self._device = None

    def __getattr__(self, name: str) -> Any:
        """Forward everything else to the underlying AndroidDevice."""
        return getattr(self._get(), name)

    def __repr__(self) -> str:
        state = "connected" if self._device else "lazy"
        return f"<PhoneProxy {self._serial or 'auto'} ({state})>"


PHONE = PhoneProxy(os.environ.get("ANDROID_SERIAL"))


# ---------------------------------------------------------------------------
# small functional helpers (match the style of your other action modules)
# ---------------------------------------------------------------------------
def android_available() -> bool:
    """True when at least one device is reachable. Never raises."""
    if DeviceManager is None:
        return False
    try:
        return len(PHONE.manager.serials) > 0
    except Exception:
        return False


def android_devices() -> List[Dict[str, Any]]:
    """Serial + state + model for every device adb sees."""
    if DeviceManager is None:
        return [{"error": _IMPORT_ERROR or "androidctl not installed"}]
    try:
        return [
            {"serial": d.serial, "state": d.state, "model": d.model,
             "transport": "usb" if d.is_usb else "wifi", "ready": d.ready}
            for d in PHONE.manager.discover(ready_only=False)
        ]
    except Exception as exc:
        return [{"error": str(exc)}]


def android_screenshot(path: str = "android_screenshot.png") -> str:
    """Save a screenshot; returns the path or an error string."""
    try:
        PHONE.screenshot(path)
        return os.path.abspath(path)
    except Exception as exc:
        return f"❌ screenshot failed: {exc}"


def android_tap(x: int, y: int) -> str:
    try:
        PHONE.tap(x, y)
        return f"✅ tapped ({x}, {y})"
    except Exception as exc:
        return f"❌ tap failed: {exc}"


def android_swipe(direction: str = "up") -> str:
    try:
        PHONE.swipe_direction(direction)
        return f"✅ swiped {direction}"
    except Exception as exc:
        return f"❌ swipe failed: {exc}"


def android_type(text: str, clear: bool = False) -> str:
    try:
        PHONE.type_text(text, clear=clear)
        return "✅ typed text"
    except Exception as exc:
        return f"❌ type failed: {exc}"


def android_ui_tree(max_nodes: int = 200) -> str:
    """Compact UI tree -- small enough to drop straight into an LLM prompt."""
    try:
        return PHONE.ui_text(max_nodes=max_nodes)
    except Exception as exc:
        return f"❌ ui_tree failed: {exc}"


def android_shell(command: str) -> str:
    try:
        res = PHONE.shell(command)
        return res.output if res.ok else f"❌ exit {res.exit_code}: {res.output}"
    except Exception as exc:
        return f"❌ shell failed: {exc}"


def android_launch(package: str) -> str:
    try:
        info = PHONE.launch(package)
        return f"✅ launched {info.get('package')} / {info.get('activity')}"
    except Exception as exc:
        return f"❌ launch failed: {exc}"


def android_current_app() -> str:
    try:
        cur = PHONE.current_app()
        return f"{cur.get('package')} / {cur.get('activity')}"
    except Exception as exc:
        return f"❌ current_app failed: {exc}"


def android_connect_wifi(host: str, port: int = 5555) -> str:
    """Wireless debugging: `adb connect`, then attach."""
    try:
        dev = PHONE.manager.connect_wifi(host, port)
        PHONE.reset()
        PHONE._serial = dev.serial          # pin subsequent calls to this device
        return f"✅ connected to {dev.serial}"
    except Exception as exc:
        return f"❌ wifi connect failed: {exc}"


def android_read_screen(max_nodes: int = 200) -> Dict[str, Any]:
    """Everything an LLM needs for one reasoning step."""
    try:
        state = PHONE.screen_state(max_nodes=max_nodes)
        state.pop("screenshot_png_b64", None)   # keep prompts text-only by default
        return state
    except Exception as exc:
        return {"error": str(exc)}


# ---------------------------------------------------------------------------
# tool schema for your executor / agent registry
# ---------------------------------------------------------------------------
ANDROID_TOOLS: List[Dict[str, Any]] = [
    {"name": "android_tap", "fn": android_tap,
     "description": "Tap pixel coordinates on the connected Android phone.",
     "args": ["x", "y"]},
    {"name": "android_swipe", "fn": android_swipe,
     "description": "Swipe/scroll the screen: up, down, left, right.",
     "args": ["direction"]},
    {"name": "android_type", "fn": android_type,
     "description": "Type text into the focused field.",
     "args": ["text", "clear"]},
    {"name": "android_screenshot", "fn": android_screenshot,
     "description": "Capture the phone screen to a PNG file.",
     "args": ["path"]},
    {"name": "android_ui_tree", "fn": android_ui_tree,
     "description": "Read the on-screen UI elements (compact text tree).",
     "args": ["max_nodes"]},
    {"name": "android_shell", "fn": android_shell,
     "description": "Run an adb shell command on the phone.",
     "args": ["command"]},
    {"name": "android_launch", "fn": android_launch,
     "description": "Open an app by package name.",
     "args": ["package"]},
    {"name": "android_current_app", "fn": android_current_app,
     "description": "Which app is in the foreground right now.",
     "args": []},
]


if __name__ == "__main__":
    # quick manual check:  python integrations/android_tool.py
    print("androidctl import :", "ok" if _IMPORT_ERROR is None else _IMPORT_ERROR)
    print("available         :", android_available())
    print("devices           :", android_devices())
    if android_available():
        print("current app       :", android_current_app())
        print("shell model       :", android_shell("getprop ro.product.model").strip())
        print("ui tree (5 lines) :")
        print("\n".join("  " + ln for ln in android_ui_tree().splitlines()[:5]))
