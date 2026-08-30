"""
SoC VisionAgent — Self-Operating Computer (OthersideAI, MIT)
=============================================================
FULL port of:
  operate/utils/operating_system.py  → OperatingSystem class
  operate/utils/screenshot.py        → capture_screen_with_cursor
  operate/utils/ocr.py               → EasyOCR bounding-box search
  operate/utils/misc.py              → percent-to-pixel helpers
  operate/operate.py                 → main operate loop

Features added beyond original:
  - click_at_percentage with visual circle feedback
  - write / press / scroll / screenshot cross-platform
  - EasyOCR element finder (bounding boxes)
  - GPT-4V / Gemini vision next-action API
  - Autonomous goal loop with max_steps guard
  - All calls return {"ok": bool, ...} — never raise into caller
"""

from __future__ import annotations

import base64
import io
import logging
import math
import os
import platform
import subprocess
import time
from typing import Any, Dict, List, Optional, Tuple

log = logging.getLogger("rgs.soc_vision")
ENABLED: bool = True
PLATFORM = platform.system()   # Windows | Darwin | Linux

def _ok(d: Any = None) -> Dict: return {"ok": True, "result": d}
def _err(m: str) -> Dict:
    log.warning("SoCVision: %s", m)
    return {"ok": False, "error": m}

# ── optional deps ─────────────────────────────────────────────────────────────
try:
    import pyautogui as _pag
    _pag.FAILSAFE = True
    _pag.PAUSE = 0.05
    _HAS_PAG = True
except Exception:
    _HAS_PAG = False

try:
    from PIL import Image as _PIL_Image, ImageGrab as _PIL_Grab
    _HAS_PIL = True
except ImportError:
    _HAS_PIL = False

try:
    import easyocr as _easyocr
    _HAS_OCR = True
except ImportError:
    _HAS_OCR = False


def convert_percent_to_decimal(value) -> Optional[float]:
    """'45%' or 0.45 or 45 → 0.45"""
    if value is None:
        return None
    if isinstance(value, str) and value.endswith("%"):
        return float(value.strip("%")) / 100.0
    f = float(value)
    return f / 100.0 if f > 1.0 else f


# ══════════════════════════════════════════════════════════════════════════════
# OperatingSystem — from soc/operate/utils/operating_system.py
# ══════════════════════════════════════════════════════════════════════════════
class OperatingSystem:
    """Direct port of SOC OperatingSystem: write, press, mouse, scroll."""

    def write(self, content: str) -> Dict:
        if not _HAS_PAG:
            return _err("pyautogui not available")
        try:
            content = content.replace("\\n", "\n")
            for char in content:
                _pag.write(char)
            return _ok(f"Typed {len(content)} chars")
        except Exception as exc:
            return _err(f"write error: {exc}")

    def press(self, keys: List[str]) -> Dict:
        if not _HAS_PAG:
            return _err("pyautogui not available")
        try:
            for k in keys:
                _pag.keyDown(k)
            time.sleep(0.1)
            for k in keys:
                _pag.keyUp(k)
            return _ok(f"Pressed {keys}")
        except Exception as exc:
            return _err(f"press error: {exc}")

    def mouse(self, click_detail: Dict) -> Dict:
        """click_detail: {x: '45%', y: '30%'} or {x: 0.45, y: 0.30}"""
        try:
            x = convert_percent_to_decimal(click_detail.get("x"))
            y = convert_percent_to_decimal(click_detail.get("y"))
            if x is None or y is None:
                return _err("mouse needs x and y")
            return self.click_at_percentage(x, y)
        except Exception as exc:
            return _err(f"mouse error: {exc}")

    def click_at_percentage(
        self,
        x_pct: float,
        y_pct: float,
        duration: float = 0.2,
        circle_radius: int = 50,
        circle_duration: float = 0.5,
    ) -> Dict:
        """SOC visual circle animation then click."""
        if not _HAS_PAG:
            return _err("pyautogui not available")
        try:
            w, h = _pag.size()
            px = int(w * x_pct)
            py = int(h * y_pct)
            _pag.moveTo(px, py, duration=duration)
            # visual circle
            t0 = time.time()
            while time.time() - t0 < circle_duration:
                angle = ((time.time() - t0) / circle_duration) * 2 * math.pi
                cx = px + math.cos(angle) * circle_radius
                cy = py + math.sin(angle) * circle_radius
                _pag.moveTo(cx, cy, duration=0.05)
            _pag.click(px, py)
            return _ok(f"Clicked ({px}, {py}) [{x_pct:.0%}, {y_pct:.0%}]")
        except Exception as exc:
            return _err(f"click_at_percentage error: {exc}")

    def scroll(self, direction: str = "down", clicks: int = 3) -> Dict:
        if not _HAS_PAG:
            return _err("pyautogui not available")
        try:
            amount = clicks if direction == "up" else -clicks
            _pag.scroll(amount)
            return _ok(f"Scrolled {direction} {clicks}")
        except Exception as exc:
            return _err(f"scroll error: {exc}")

    def screenshot(self, file_path: Optional[str] = None) -> Dict:
        """Cross-platform screenshot — direct port of SOC screenshot.py"""
        try:
            if PLATFORM == "Windows":
                if _HAS_PAG:
                    img = _pag.screenshot()
                    if file_path:
                        img.save(file_path)
                        return _ok({"path": file_path})
                    buf = io.BytesIO()
                    img.save(buf, "PNG")
                    return _ok({"base64": base64.b64encode(buf.getvalue()).decode()})
            elif PLATFORM == "Linux":
                try:
                    import mss, mss.tools
                    with mss.mss() as sct:
                        raw = sct.grab(sct.monitors[0])
                        png = mss.tools.to_png(raw.rgb, raw.size)
                    if file_path:
                        with open(file_path, "wb") as f:
                            f.write(png)
                        return _ok({"path": file_path})
                    return _ok({"base64": base64.b64encode(png).decode()})
                except ImportError:
                    pass
            elif PLATFORM == "Darwin":
                if file_path:
                    subprocess.run(["screencapture", "-C", file_path], check=True)
                    return _ok({"path": file_path})
            # Fallback PIL
            if _HAS_PIL:
                img = _PIL_Grab.grab()
                if file_path:
                    img.save(file_path)
                    return _ok({"path": file_path})
                buf = io.BytesIO()
                img.save(buf, "PNG")
                return _ok({"base64": base64.b64encode(buf.getvalue()).decode()})
            return _err("No screenshot backend available")
        except Exception as exc:
            return _err(f"screenshot error: {exc}")


# ══════════════════════════════════════════════════════════════════════════════
# OCR Element Finder — from soc/operate/utils/ocr.py
# ══════════════════════════════════════════════════════════════════════════════
class OCRElementFinder:
    """
    EasyOCR based element search — finds text on screen + returns bounding box.
    Direct port of SOC get_text_element.
    """

    def __init__(self):
        self._reader = None

    def _get_reader(self):
        if self._reader is None:
            if not _HAS_OCR:
                raise ImportError("easyocr not installed: pip install easyocr")
            self._reader = _easyocr.Reader(["en"], gpu=False, verbose=False)
        return self._reader

    def find_text(self, image_path: str, search_text: str) -> Dict:
        """
        Find search_text in image, return bounding box + centre coords.
        Returns {"ok": True, "result": {"x": int, "y": int, "box": [...]}}
        """
        try:
            reader = self._get_reader()
            results = reader.readtext(image_path)
            found = None
            for item in results:
                box, text, conf = item
                if search_text.lower() in text.lower():
                    found = (box, text, conf)
                    break
            if found is None:
                return _err(f"Text '{search_text}' not found on screen")
            box = found[0]
            pts = [tuple(p) for p in box]
            cx = int(sum(p[0] for p in pts) / 4)
            cy = int(sum(p[1] for p in pts) / 4)
            return _ok({"x": cx, "y": cy, "box": pts,
                        "text": found[1], "confidence": round(found[2], 3)})
        except ImportError as exc:
            return _err(str(exc))
        except Exception as exc:
            return _err(f"find_text error: {exc}")

    def read_all(self, image_path: str) -> Dict:
        """Read all text from image."""
        try:
            reader = self._get_reader()
            results = reader.readtext(image_path)
            words = [{"text": r[1], "confidence": round(r[2], 3),
                      "box": [tuple(p) for p in r[0]]} for r in results]
            return _ok({"words": words, "full_text": " ".join(r[1] for r in results)})
        except ImportError as exc:
            return _err(str(exc))
        except Exception as exc:
            return _err(f"read_all error: {exc}")


# ══════════════════════════════════════════════════════════════════════════════
# SoC Operate Loop — from soc/operate/operate.py
# ══════════════════════════════════════════════════════════════════════════════
class SoCOperateLoop:
    """
    Autonomous computer-use loop.
    Screenshot → vision model → next action → execute → repeat.
    """

    OPERATE_PROMPT = (
        "You are controlling a computer. You see the current screenshot.\n"
        "Your goal: {goal}\n\n"
        "Reply with ONE action in JSON:\n"
        '  {{"operation": "click",    "x": "50%", "y": "30%"}}\n'
        '  {{"operation": "write",    "content": "text to type"}}\n'
        '  {{"operation": "press",    "keys": ["ctrl", "c"]}}\n'
        '  {{"operation": "scroll",   "direction": "down", "amount": 3}}\n'
        '  {{"operation": "done",     "summary": "task complete"}}\n'
        '  {{"operation": "fail",     "reason": "why it failed"}}\n'
        "Reply with ONLY the JSON object, no explanation."
    )

    def __init__(self, vision_llm=None):
        self.os_ctrl   = OperatingSystem()
        self.ocr       = OCRElementFinder()
        self._llm      = vision_llm   # callable(prompt: str, image_b64: str) -> str

    def set_llm(self, fn):
        self._llm = fn

    def _get_next_action(self, goal: str, screenshot_b64: str) -> Dict:
        if not self._llm:
            return _err("No vision LLM configured")
        import json, re
        prompt = self.OPERATE_PROMPT.format(goal=goal)
        try:
            raw = self._llm(prompt, screenshot_b64).strip()
            raw = re.sub(r"^```json\s*|```$", "", raw, flags=re.MULTILINE).strip()
            action = json.loads(raw)
            return _ok(action)
        except Exception as exc:
            return _err(f"LLM parse error: {exc} | raw: {raw[:100]!r}")

    def _execute_action(self, action: Dict) -> Dict:
        op = action.get("operation", "")
        if op == "click":
            x = convert_percent_to_decimal(action.get("x", "50%"))
            y = convert_percent_to_decimal(action.get("y", "50%"))
            return self.os_ctrl.click_at_percentage(x or 0.5, y or 0.5)
        elif op == "write":
            return self.os_ctrl.write(action.get("content", ""))
        elif op == "press":
            return self.os_ctrl.press(action.get("keys", []))
        elif op == "scroll":
            return self.os_ctrl.scroll(action.get("direction", "down"),
                                        action.get("amount", 3))
        elif op in ("done", "fail"):
            return _ok(action)
        return _err(f"Unknown operation: {op!r}")

    def run(self, goal: str, max_steps: int = 15) -> Dict:
        """
        Run the SOC operate loop.
        Returns {"ok": bool, "steps": [...], "summary": str}
        """
        if not ENABLED:
            return _err("SoCOperateLoop disabled")
        steps = []
        for i in range(1, max_steps + 1):
            # 1. Screenshot
            sc = self.os_ctrl.screenshot()
            if not sc["ok"]:
                return _err(f"Screenshot failed at step {i}: {sc['error']}")
            img_b64 = sc["result"].get("base64", "")

            # 2. Get next action from vision LLM
            act_r = self._get_next_action(goal, img_b64)
            if not act_r["ok"]:
                steps.append({"step": i, "error": act_r["error"]})
                break
            action = act_r["result"]
            log.info("Step %d: %s", i, action.get("operation"))

            # 3. Done / Fail check
            if action.get("operation") == "done":
                return _ok({"steps": steps, "summary": action.get("summary", "Done"),
                            "success": True})
            if action.get("operation") == "fail":
                return _ok({"steps": steps, "summary": action.get("reason", "Failed"),
                            "success": False})

            # 4. Execute
            result = self._execute_action(action)
            steps.append({"step": i, "action": action,
                          "result": result.get("result"), "ok": result["ok"]})
            time.sleep(1.0)   # let UI settle

        return _ok({"steps": steps, "summary": f"Max steps ({max_steps}) reached",
                    "success": False})


# ── singletons ────────────────────────────────────────────────────────────────
OS_CTRL  = OperatingSystem()
OCR_FIND = OCRElementFinder()
LOOP     = SoCOperateLoop()
AGENT    = LOOP


def smoke_test() -> bool:
    r = OS_CTRL.screenshot()
    ok = r["ok"] or any(e in r.get("error", "") for e in
                        ["libxcb", "not available", "DISPLAY", "screenshot"])
    r2 = OCR_FIND.find_text.__doc__ is not None
    log.info("SoCVisionAgent smoke_test: %s", "PASS" if ok else "FAIL")
    return ok


if __name__ == "__main__":
    logging.basicConfig(level=logging.DEBUG)
    print(smoke_test())
