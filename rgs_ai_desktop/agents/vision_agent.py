"""
VisionAgent — extracted from Self-Operating Computer (OthersideAI)
===================================================================
OCR / Set-of-Marks (SoM) based screen understanding.

Understands what is on the screen, locates interactive elements by
description, and provides coordinates back to the orchestrator.

Capability slot: VISION
Source inspiration: self-operating-computer VisionAgent
"""

from __future__ import annotations

import base64
import json
import logging
import re
from typing import Any, Dict, List, Optional, Tuple

log = logging.getLogger("rgs.vision")

# ── feature flag ──────────────────────────────────────────────────────────────
ENABLED: bool = True

# ── optional deps ─────────────────────────────────────────────────────────────
try:
    import pytesseract
    from PIL import Image
    import io as _io
    _HAS_OCR = True
except ImportError:
    _HAS_OCR = False

try:
    import cv2
    import numpy as np
    _HAS_CV2 = True
except ImportError:
    _HAS_CV2 = False


def _ok(data: Any = None) -> Dict:
    return {"ok": True, "result": data}

def _err(msg: str) -> Dict:
    log.warning("VisionAgent: %s", msg)
    return {"ok": False, "error": msg}


# ── SoM / OCR helpers ────────────────────────────────────────────────────────
class VisionAgent:
    """
    Screen-understanding agent.

    Primary flow:
      1. screenshot() or accept an existing PNG bytes / base64
      2. ocr()        -> text + bounding boxes
      3. find_text()  -> (x, y) of a string on screen
      4. describe()   -> GPT-4V / local-vision model description (LLM injected)

    All methods return {"ok": bool, "result"/"error": ...} and never raise.
    """

    def __init__(self, llm_callable=None):
        """
        llm_callable: optional callable(prompt, image_b64) -> str
        Used by describe() and find_element_by_description().
        """
        self.llm = llm_callable

    # -- image loading ---------------------------------------------------------
    def _load_image(self, image_source) -> Optional[Any]:
        """Accept path, bytes, base64-str, or PIL Image.  Returns PIL Image."""
        if not _HAS_OCR:
            return None
        try:
            if isinstance(image_source, str):
                # could be file path OR base64
                try:
                    raw = base64.b64decode(image_source)
                    return Image.open(_io.BytesIO(raw))
                except Exception:
                    return Image.open(image_source)
            elif isinstance(image_source, bytes):
                return Image.open(_io.BytesIO(image_source))
            else:
                return image_source          # assume PIL Image already
        except Exception as exc:
            log.debug("_load_image failed: %s", exc)
            return None

    # -- OCR -------------------------------------------------------------------
    def ocr(self, image_source, lang: str = "eng") -> Dict:
        """
        Run Tesseract OCR on image_source.
        Returns {"ok": True, "result": {"text": str, "data": [...]}}
        """
        if not ENABLED:
            return _err("VisionAgent disabled (feature flag)")
        if not _HAS_OCR:
            return _err("pytesseract / Pillow not installed; pip install pytesseract pillow")
        img = self._load_image(image_source)
        if img is None:
            return _err("Could not load image")
        try:
            full_text = pytesseract.image_to_string(img, lang=lang)
            data = pytesseract.image_to_data(img, lang=lang,
                                             output_type=pytesseract.Output.DICT)
            # Build word-level bounding boxes
            words = []
            for i, word in enumerate(data["text"]):
                word = word.strip()
                if word and int(data["conf"][i]) > 30:
                    words.append({
                        "word": word,
                        "x": data["left"][i],
                        "y": data["top"][i],
                        "w": data["width"][i],
                        "h": data["height"][i],
                        "conf": data["conf"][i],
                    })
            return _ok({"text": full_text.strip(), "words": words})
        except Exception as exc:
            return _err(f"OCR failed: {exc}")

    # -- text location ---------------------------------------------------------
    def find_text(self, image_source, query: str,
                  case_sensitive: bool = False) -> Dict:
        """
        Find the centre (x, y) of the first occurrence of *query* on screen.
        Returns {"ok": True, "result": {"x": int, "y": int}} or error.
        """
        r = self.ocr(image_source)
        if not r["ok"]:
            return r
        q = query if case_sensitive else query.lower()
        for w in r["result"]["words"]:
            word = w["word"] if case_sensitive else w["word"].lower()
            if q in word:
                cx = w["x"] + w["w"] // 2
                cy = w["y"] + w["h"] // 2
                return _ok({"x": cx, "y": cy, "word": w["word"],
                             "bbox": (w["x"], w["y"], w["w"], w["h"])})
        return _err(f"text {query!r} not found on screen")

    # -- vision-model description ---------------------------------------------
    def describe(self, image_source, prompt: str = "Describe what you see.") -> Dict:
        """
        Use the injected vision-capable LLM to describe the screen.
        Falls back to OCR-based summary when no LLM is available.
        """
        if not ENABLED:
            return _err("VisionAgent disabled (feature flag)")
        if self.llm:
            try:
                if isinstance(image_source, str) and not image_source.startswith("/"):
                    b64 = image_source          # already base64
                else:
                    img = self._load_image(image_source)
                    if img is None:
                        return _err("Could not load image for describe()")
                    buf = _io.BytesIO()
                    img.save(buf, format="PNG")
                    b64 = base64.b64encode(buf.getvalue()).decode()
                answer = self.llm(prompt, b64)
                return _ok({"description": answer})
            except Exception as exc:
                return _err(f"LLM describe failed: {exc}")
        else:
            r = self.ocr(image_source)
            if r["ok"]:
                return _ok({"description": f"[OCR fallback] {r['result']['text'][:500]}"})
            return r

    # -- element finder by natural language -----------------------------------
    def find_element_by_description(self, image_source, description: str) -> Dict:
        """
        Ask the vision LLM: 'Where is [description]?  Reply with x,y only.'
        Returns {"ok": True, "result": {"x": int, "y": int}}
        """
        if not ENABLED:
            return _err("VisionAgent disabled (feature flag)")
        if not self.llm:
            # graceful fallback: try plain OCR text match
            return self.find_text(image_source, description)
        try:
            if isinstance(image_source, str) and not image_source.startswith("/"):
                b64 = image_source
            else:
                img = self._load_image(image_source)
                buf = _io.BytesIO()
                img.save(buf, format="PNG")
                b64 = base64.b64encode(buf.getvalue()).decode()
            prompt = (
                f"Look at this screenshot. Find the UI element that matches: '{description}'.\n"
                "Reply with ONLY two integers: the x and y pixel coordinates of its center.\n"
                "Format: x,y\nDo not add any explanation."
            )
            reply = self.llm(prompt, b64).strip()
            m = re.search(r"(\d+)\s*[,x]\s*(\d+)", reply)
            if m:
                return _ok({"x": int(m.group(1)), "y": int(m.group(2))})
            return _err(f"LLM did not return valid coordinates: {reply!r}")
        except Exception as exc:
            return _err(f"find_element_by_description failed: {exc}")

    # -- Som (Set-of-Marks) overlay -------------------------------------------
    def annotate_screenshot(self, image_source,
                            output_path: Optional[str] = None) -> Dict:
        """
        Draw numbered bounding boxes around detected text words (SoM style).
        Returns base64 PNG and optionally saves to output_path.
        """
        if not ENABLED:
            return _err("VisionAgent disabled (feature flag)")
        if not _HAS_OCR or not _HAS_CV2:
            return _err("pytesseract + opencv-python required for annotate_screenshot")
        img = self._load_image(image_source)
        if img is None:
            return _err("Could not load image")
        try:
            r = self.ocr(img)
            if not r["ok"]:
                return r
            cv_img = cv2.cvtColor(np.array(img), cv2.COLOR_RGB2BGR)
            for idx, w in enumerate(r["result"]["words"][:50]):
                x, y, ww, wh = w["x"], w["y"], w["w"], w["h"]
                cv2.rectangle(cv_img, (x, y), (x + ww, y + wh), (0, 255, 0), 1)
                cv2.putText(cv_img, str(idx), (x, max(0, y - 2)),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.35, (0, 200, 255), 1)
            _, buf = cv2.imencode(".png", cv_img)
            b64 = base64.b64encode(buf.tobytes()).decode()
            if output_path:
                with open(output_path, "wb") as f:
                    f.write(buf.tobytes())
            return _ok({"base64": b64, "marks": len(r["result"]["words"])})
        except Exception as exc:
            return _err(f"annotate_screenshot failed: {exc}")


# ── module-level singleton ────────────────────────────────────────────────────
AGENT = VisionAgent()


# ── smoke test ────────────────────────────────────────────────────────────────
def smoke_test() -> bool:
    ok = True
    if not _HAS_OCR:
        log.info("VisionAgent smoke_test: SKIP (pytesseract not installed — acceptable)")
    else:
        # minimal test: create a tiny white image and OCR it
        try:
            from PIL import Image as _Image
            img = _Image.new("RGB", (100, 30), color="white")
            r = AGENT.ocr(img)
            ok = r["ok"]
        except Exception:
            ok = False
    log.info("VisionAgent smoke_test: %s", "PASS" if ok else "FAIL")
    return ok


if __name__ == "__main__":
    logging.basicConfig(level=logging.DEBUG)
    print(smoke_test())
