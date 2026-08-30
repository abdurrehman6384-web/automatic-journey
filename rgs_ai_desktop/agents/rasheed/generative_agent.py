"""
GenerativeAgent — RASHEED AI Image / Content Generation (from project.zip)
===========================================================================
Integrates: generative_suite.py, content_creator.py, pdf_assistant.py,
            ImageGeneration.py (HuggingFace SDXL), doc_generator.py

Features:
  - AI image generation (Stability AI / HuggingFace SDXL / DALL·E fallback)
  - YouTube script writer
  - SEO optimizer
  - PDF summarizer
  - Content/doc generator
  - Trend analyzer
"""

from __future__ import annotations

import asyncio
import base64
import json
import logging
import os
from pathlib import Path
from typing import Any, Dict, List, Optional

log = logging.getLogger("rgs.generative")
ENABLED: bool = True

DATA_DIR = Path(os.environ.get("RGS_DATA_DIR", Path.home() / ".rgs"))
DATA_DIR.mkdir(parents=True, exist_ok=True)

def _ok(d: Any = None) -> Dict: return {"ok": True, "result": d}
def _err(m: str) -> Dict:
    log.warning("GenerativeAgent: %s", m)
    return {"ok": False, "error": m}

try:
    import requests as _req
    _HAS_REQUESTS = True
except ImportError:
    _HAS_REQUESTS = False


class ImageGenerator:
    """
    AI image generator.
    Priority: Stability AI → HuggingFace SDXL → DALL·E 3
    """

    def generate(
        self,
        prompt: str,
        save_path: Optional[str] = None,
        width: int = 1024,
        height: int = 1024,
    ) -> Dict:
        if not ENABLED:
            return _err("GenerativeAgent disabled")
        if not _HAS_REQUESTS:
            return _err("requests not installed")

        # Try Stability AI
        stability_key = os.environ.get("STABILITY_API_KEY", "")
        if stability_key:
            r = self._stability(prompt, stability_key, save_path, width, height)
            if r["ok"]:
                return r

        # Try HuggingFace SDXL
        hf_key = os.environ.get("HUGGINGFACE_API_KEY", "")
        if hf_key:
            r = self._huggingface(prompt, hf_key, save_path)
            if r["ok"]:
                return r

        # Try OpenAI DALL·E 3
        openai_key = os.environ.get("OPENAI_API_KEY", "")
        if openai_key:
            return self._dalle(prompt, openai_key, save_path)

        return _err("No image generation API key found. Set STABILITY_API_KEY, HUGGINGFACE_API_KEY, or OPENAI_API_KEY")

    def _stability(self, prompt: str, api_key: str, save_path: Optional[str],
                   width: int, height: int) -> Dict:
        try:
            url = "https://api.stability.ai/v1/generation/stable-diffusion-xl-1024-v1-0/text-to-image"
            r = _req.post(url, headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json",
            }, json={
                "text_prompts": [{"text": prompt}],
                "cfg_scale": 7, "width": width, "height": height,
                "samples": 1, "steps": 30
            }, timeout=60)
            if r.status_code != 200:
                return _err(f"Stability error: {r.status_code}")
            img_b64 = r.json()["artifacts"][0]["base64"]
            img_data = base64.b64decode(img_b64)
            path = save_path or str(DATA_DIR / "generated_image.png")
            with open(path, "wb") as f:
                f.write(img_data)
            return _ok({"path": path, "source": "stability_ai", "base64": img_b64})
        except Exception as exc:
            return _err(f"Stability failed: {exc}")

    def _huggingface(self, prompt: str, api_key: str, save_path: Optional[str]) -> Dict:
        try:
            url = "https://api-inference.huggingface.co/models/stabilityai/stable-diffusion-xl-base-1.0"
            r = _req.post(url, headers={"Authorization": f"Bearer {api_key}"},
                          json={"inputs": f"{prompt}, quality=4k, ultra high detail"},
                          timeout=120)
            if r.status_code != 200:
                return _err(f"HuggingFace error: {r.status_code}")
            img_data = r.content
            path = save_path or str(DATA_DIR / "hf_image.png")
            with open(path, "wb") as f:
                f.write(img_data)
            return _ok({"path": path, "source": "huggingface_sdxl",
                        "base64": base64.b64encode(img_data).decode()})
        except Exception as exc:
            return _err(f"HuggingFace failed: {exc}")

    def _dalle(self, prompt: str, api_key: str, save_path: Optional[str]) -> Dict:
        try:
            import openai
            client = openai.OpenAI(api_key=api_key)
            resp = client.images.generate(model="dall-e-3", prompt=prompt,
                                          size="1024x1024", quality="standard", n=1)
            image_url = resp.data[0].url
            r = _req.get(image_url, timeout=30)
            path = save_path or str(DATA_DIR / "dalle_image.png")
            with open(path, "wb") as f:
                f.write(r.content)
            return _ok({"path": path, "source": "dalle3", "url": image_url})
        except ImportError:
            return _err("openai package not installed")
        except Exception as exc:
            return _err(f"DALL·E failed: {exc}")


class ContentCreator:
    """YouTube script, SEO, trends — uses LLM router."""

    def __init__(self, llm_fn=None):
        self._llm = llm_fn

    def _ask(self, prompt: str) -> str:
        if self._llm:
            return self._llm(prompt)
        return f"[LLM not configured] Prompt: {prompt[:100]}"

    def write_script(self, topic: str, duration: str = "5 minutes",
                     lang: str = "Hinglish") -> Dict:
        prompt = (
            f"Write a YouTube video script for: '{topic}' ({duration}).\n"
            f"Include: Hook, Main Content, CTA. Language: {lang}.\n"
            f"Make it engaging, use storytelling."
        )
        return _ok({"script": self._ask(prompt), "topic": topic})

    def thumbnail_prompt(self, topic: str) -> Dict:
        prompt = (
            f"Generate a detailed AI image prompt for a YouTube thumbnail about: '{topic}'.\n"
            f"Describe: colors, text overlay, style, emotion. Make it click-worthy."
        )
        return _ok({"prompt": self._ask(prompt)})

    def seo_optimize(self, title: str) -> Dict:
        prompt = (
            f"Generate SEO-optimized YouTube metadata for: '{title}'\n"
            f"Output:\n1. 5 Title options\n2. Description (200 words)\n3. 15 hashtags"
        )
        return _ok({"seo": self._ask(prompt)})

    def analyze_trends(self, niche: str = "technology") -> Dict:
        prompt = (
            f"What are the top 5 trending video ideas in '{niche}' niche right now?\n"
            f"Be specific, give titles, estimated views potential."
        )
        return _ok({"trends": self._ask(prompt)})

    def write_email(self, to: str, subject: str, context: str) -> Dict:
        prompt = (
            f"Write a professional email.\nTo: {to}\nSubject: {subject}\n"
            f"Context: {context}\nTone: Professional, concise."
        )
        return _ok({"email": self._ask(prompt)})

    def write_code(self, description: str, language: str = "Python") -> Dict:
        prompt = (
            f"Write clean {language} code for: {description}\n"
            f"Include comments. Follow best practices."
        )
        return _ok({"code": self._ask(prompt), "language": language})


class PDFAssistant:
    """PDF summarizer, converter."""

    def __init__(self, llm_fn=None):
        self._llm = llm_fn

    def summarize(self, pdf_path: str, max_pages: int = 30) -> Dict:
        if not os.path.exists(pdf_path):
            return _err(f"File not found: {pdf_path}")
        try:
            import PyPDF2
            text = ""
            with open(pdf_path, "rb") as f:
                reader = PyPDF2.PdfReader(f)
                for i, page in enumerate(reader.pages[:max_pages]):
                    pt = page.extract_text()
                    if pt:
                        text += pt + "\n"
            if not text.strip():
                return _err("No text extracted from PDF (might be scanned)")
            if self._llm:
                prompt = (
                    f"Summarize this document in clear bullet points:\n\n{text[:6000]}"
                )
                summary = self._llm(prompt)
            else:
                summary = text[:2000] + ("..." if len(text) > 2000 else "")
            return _ok({"summary": summary, "pages_read": min(max_pages, len(reader.pages))})
        except ImportError:
            return _err("PyPDF2 not installed: pip install PyPDF2")
        except Exception as exc:
            return _err(f"PDF summarize failed: {exc}")

    def extract_text(self, pdf_path: str) -> Dict:
        if not os.path.exists(pdf_path):
            return _err(f"Not found: {pdf_path}")
        try:
            import PyPDF2
            text = ""
            with open(pdf_path, "rb") as f:
                reader = PyPDF2.PdfReader(f)
                for page in reader.pages:
                    pt = page.extract_text()
                    if pt:
                        text += pt + "\n"
            return _ok({"text": text, "pages": len(reader.pages)})
        except ImportError:
            return _err("PyPDF2 not installed")
        except Exception as exc:
            return _err(str(exc))


class GenerativeAgent:
    """Unified facade for all generative AI features."""

    def __init__(self, llm_fn=None):
        self.images   = ImageGenerator()
        self.content  = ContentCreator(llm_fn)
        self.pdf      = PDFAssistant(llm_fn)
        self._llm     = llm_fn

    def set_llm(self, fn):
        self._llm = fn
        self.content._llm = fn
        self.pdf._llm = fn

    def dispatch(self, action: str, **kwargs) -> Dict:
        map_ = {
            "generate_image":   lambda: self.images.generate(**kwargs),
            "write_script":     lambda: self.content.write_script(**kwargs),
            "thumbnail_prompt": lambda: self.content.thumbnail_prompt(**kwargs),
            "seo_optimize":     lambda: self.content.seo_optimize(**kwargs),
            "analyze_trends":   lambda: self.content.analyze_trends(**kwargs),
            "write_email":      lambda: self.content.write_email(**kwargs),
            "write_code":       lambda: self.content.write_code(**kwargs),
            "summarize_pdf":    lambda: self.pdf.summarize(**kwargs),
            "extract_pdf":      lambda: self.pdf.extract_text(**kwargs),
        }
        fn = map_.get(action)
        if fn is None:
            return _err(f"Unknown action: {action!r}")
        try:
            return fn()
        except Exception as exc:
            return _err(str(exc))


# ── module-level singleton ────────────────────────────────────────────────────
AGENT = GenerativeAgent()


def smoke_test() -> bool:
    r = AGENT.content.write_email("test@test.com", "Test", "Testing RGS AI Desktop")
    ok = r["ok"]
    log.info("GenerativeAgent smoke_test: %s", "PASS" if ok else "FAIL")
    return ok


if __name__ == "__main__":
    logging.basicConfig(level=logging.DEBUG)
    print(smoke_test())
