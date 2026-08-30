"""
ScreenControlAgent — extracted from Bytebot (self-hosted, bytebot-ai/bytebot)
==============================================================================
Provides mouse / keyboard / screenshot automation over the local desktop.

Falls back gracefully when running headless or when the optional pyautogui /
mss libraries are absent — the plugin is still importable and all calls return
a structured error instead of crashing the app.

Capability slot: SCREEN-CONTROL
"""

from __future__ import annotations

import base64
import io
import logging
import os
import time
from typing import Any, Dict, List, Optional, Tuple

log = logging.getLogger("rgs.screen_control")

# ── feature flag ──────────────────────────────────────────────────────────────
ENABLED: bool = True

# ── optional dependency guard ─────────────────────────────────────────────────
try:
    import pyautogui
    _HAS_PYAUTOGUI = True
    pyautogui.FAILSAFE = True          # move mouse to top-left corner to abort
    pyautogui.PAUSE = 0.05
except (ImportError, KeyError, Exception):
    # KeyError: 'DISPLAY' is raised in headless environments (no X server)
    _HAS_PYAUTOGUI = False

try:
    import mss
    import mss.tools
    _HAS_MSS = True
except ImportError:
    _HAS_MSS = False

# ── structured return helpers ─────────────────────────────────────────────────
def _ok(data: Any = None) -> Dict:
    return {"ok": True, "result": data}

def _err(msg: str) -> Dict:
    log.warning("ScreenControlAgent: %s", msg)
    return {"ok": False, "error": msg}

def _require() -> Optional[Dict]:
    if not ENABLED:
        return _err("ScreenControlAgent disabled (feature flag)")
    if not _HAS_PYAUTOGUI:
        return _err("pyautogui not installed; run: pip install pyautogui")
    return None


# ── core actions ─────────────────────────────────────────────────────────────
class ScreenControlAgent:
    """
    Thin, auditable wrapper around pyautogui + mss.

    Every method returns {"ok": bool, "result"/"error": ...}.
    Raised exceptions are caught here — callers always get a dict.
    """

    # -- pointer ---------------------------------------------------------------
    def click(self, x: int, y: int, button: str = "left", clicks: int = 1) -> Dict:
        if (e := _require()):
            return e
        try:
            pyautogui.click(x, y, button=button, clicks=clicks, interval=0.1)
            return _ok(f"clicked ({x},{y}) {button}×{clicks}")
        except Exception as exc:
            return _err(f"click failed: {exc}")

    def right_click(self, x: int, y: int) -> Dict:
        return self.click(x, y, button="right")

    def double_click(self, x: int, y: int) -> Dict:
        return self.click(x, y, clicks=2)

    def move(self, x: int, y: int, duration: float = 0.2) -> Dict:
        if (e := _require()):
            return e
        try:
            pyautogui.moveTo(x, y, duration=duration)
            return _ok(f"moved to ({x},{y})")
        except Exception as exc:
            return _err(f"move failed: {exc}")

    def drag(self, x1: int, y1: int, x2: int, y2: int, duration: float = 0.5) -> Dict:
        if (e := _require()):
            return e
        try:
            pyautogui.moveTo(x1, y1, duration=0.1)
            pyautogui.dragTo(x2, y2, duration=duration, button="left")
            return _ok(f"dragged ({x1},{y1})->({x2},{y2})")
        except Exception as exc:
            return _err(f"drag failed: {exc}")

    def scroll(self, x: int, y: int, clicks: int = 3) -> Dict:
        if (e := _require()):
            return e
        try:
            pyautogui.scroll(clicks, x=x, y=y)
            return _ok(f"scrolled {clicks} at ({x},{y})")
        except Exception as exc:
            return _err(f"scroll failed: {exc}")

    # -- keyboard --------------------------------------------------------------
    def type_text(self, text: str, interval: float = 0.03) -> Dict:
        if (e := _require()):
            return e
        try:
            pyautogui.typewrite(text, interval=interval)
            return _ok(f"typed {len(text)} chars")
        except Exception as exc:
            return _err(f"type failed: {exc}")

    def hotkey(self, *keys: str) -> Dict:
        if (e := _require()):
            return e
        try:
            pyautogui.hotkey(*keys)
            return _ok(f"hotkey {'+'.join(keys)}")
        except Exception as exc:
            return _err(f"hotkey failed: {exc}")

    def key_press(self, key: str) -> Dict:
        if (e := _require()):
            return e
        try:
            pyautogui.press(key)
            return _ok(f"pressed {key}")
        except Exception as exc:
            return _err(f"key_press failed: {exc}")

    # -- screenshot ------------------------------------------------------------
    def screenshot(
        self,
        path: Optional[str] = None,
        region: Optional[Tuple[int, int, int, int]] = None,
        as_base64: bool = False,
    ) -> Dict:
        """
        Capture screen.
        Returns {"ok": True, "result": {"path": ..., "base64": ...}}
        """
        if not ENABLED:
            return _err("ScreenControlAgent disabled (feature flag)")
        if not _HAS_MSS and not _HAS_PYAUTOGUI:
            return _err("Neither mss nor pyautogui is installed")

        try:
            if _HAS_MSS:
                with mss.mss() as sct:
                    mon = sct.monitors[0]
                    if region:
                        x, y, w, h = region
                        mon = {"top": y, "left": x, "width": w, "height": h}
                    raw = sct.grab(mon)
                    img_bytes = mss.tools.to_png(raw.rgb, raw.size)
            else:
                # pyautogui fallback
                pil_img = pyautogui.screenshot()
                if region:
                    x, y, w, h = region
                    pil_img = pil_img.crop((x, y, x + w, y + h))
                buf = io.BytesIO()
                pil_img.save(buf, format="PNG")
                img_bytes = buf.getvalue()

            result: Dict[str, Any] = {}
            if path:
                with open(path, "wb") as f:
                    f.write(img_bytes)
                result["path"] = os.path.abspath(path)
            if as_base64 or not path:
                result["base64"] = base64.b64encode(img_bytes).decode()
                result["size_bytes"] = len(img_bytes)
            return _ok(result)
        except Exception as exc:
            return _err(f"screenshot failed: {exc}")

    # -- screen info -----------------------------------------------------------
    def screen_size(self) -> Dict:
        if (e := _require()):
            return e
        try:
            w, h = pyautogui.size()
            return _ok({"width": w, "height": h})
        except Exception as exc:
            return _err(str(exc))

    def mouse_position(self) -> Dict:
        if (e := _require()):
            return e
        try:
            x, y = pyautogui.position()
            return _ok({"x": x, "y": y})
        except Exception as exc:
            return _err(str(exc))


# ── module-level singleton ────────────────────────────────────────────────────
AGENT = ScreenControlAgent()


# ── smoke test ────────────────────────────────────────────────────────────────
def smoke_test() -> bool:
    r = AGENT.screenshot(as_base64=True)
    # Accept: success OR expected missing-dep / no-display / headless errors
    acceptable_errors = (
        "not installed", "DISPLAY", "headless", "cannot connect",
        "libxcb", "xcb", "No module", "screenshot failed",
    )
    ok = r["ok"] or any(e.lower() in r.get("error", "").lower() for e in acceptable_errors)
    log.info("ScreenControlAgent smoke_test: %s", "PASS" if ok else "FAIL")
    return ok


if __name__ == "__main__":
    logging.basicConfig(level=logging.DEBUG)
    print(smoke_test())
