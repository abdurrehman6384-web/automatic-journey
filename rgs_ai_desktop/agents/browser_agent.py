"""
BrowserAgent + KnowledgeBaseAgent
===================================
Extracted from OpenAgent (the-open-agent/openagent)

BrowserAgent     — browser-use: navigate, click, fill forms, extract content
KnowledgeBaseAgent — RAG: index documents, semantic search, answer with context

Capability slot: BROWSER-USE  (no other browser agent in the system)
"""

from __future__ import annotations

import hashlib
import json
import logging
import math
import os
import time
from dataclasses import dataclass, field
from pathlib import Path
from threading import RLock
from typing import Any, Callable, Dict, List, Optional

log = logging.getLogger("rgs.browser")

# ── feature flags ─────────────────────────────────────────────────────────────
BROWSER_ENABLED: bool = True
KB_ENABLED: bool = True

# ── optional deps ─────────────────────────────────────────────────────────────
try:
    from playwright.sync_api import sync_playwright, Page, Browser
    _HAS_PLAYWRIGHT = True
except ImportError:
    _HAS_PLAYWRIGHT = False

try:
    import requests
    _HAS_REQUESTS = True
except ImportError:
    _HAS_REQUESTS = False

try:
    from bs4 import BeautifulSoup
    _HAS_BS4 = True
except ImportError:
    _HAS_BS4 = False


def _ok(data: Any = None) -> Dict:
    return {"ok": True, "result": data}

def _err(msg: str) -> Dict:
    log.warning("BrowserAgent: %s", msg)
    return {"ok": False, "error": msg}


# ═══════════════════════════════════════════════════════════════════════════════
# BrowserAgent
# ═══════════════════════════════════════════════════════════════════════════════

class BrowserAgent:
    """
    Playwright-backed browser agent.

    Falls back to requests+BeautifulSoup for read-only tasks when Playwright
    is not installed.  All methods return {"ok": bool, ...} and never raise.
    """

    def __init__(self):
        self._pw = None
        self._browser: Optional[Any] = None
        self._page: Optional[Any] = None
        self._lock = RLock()

    # -- lifecycle -------------------------------------------------------------
    def _ensure_browser(self) -> Optional[str]:
        """Returns None on success, error string on failure."""
        if not BROWSER_ENABLED:
            return "BrowserAgent disabled (feature flag)"
        if not _HAS_PLAYWRIGHT:
            return "playwright not installed; run: pip install playwright && playwright install chromium"
        with self._lock:
            if self._browser is None:
                try:
                    self._pw = sync_playwright().start()
                    self._browser = self._pw.chromium.launch(headless=True)
                    self._page = self._browser.new_page()
                    log.info("Browser launched")
                except Exception as exc:
                    return f"Browser launch failed: {exc}"
        return None

    def close(self) -> None:
        with self._lock:
            try:
                if self._page:
                    self._page.close()
                if self._browser:
                    self._browser.close()
                if self._pw:
                    self._pw.stop()
            except Exception:
                pass
            self._pw = self._browser = self._page = None

    # -- navigation ------------------------------------------------------------
    def navigate(self, url: str, wait_until: str = "networkidle") -> Dict:
        if err := self._ensure_browser():
            return _err(err)
        try:
            self._page.goto(url, wait_until=wait_until, timeout=30_000)
            return _ok({"url": self._page.url, "title": self._page.title()})
        except Exception as exc:
            return _err(f"navigate failed: {exc}")

    def current_url(self) -> str:
        if self._page:
            return self._page.url
        return ""

    def get_page_text(self) -> Dict:
        if err := self._ensure_browser():
            return _err(err)
        try:
            text = self._page.inner_text("body")
            return _ok({"text": text[:8000], "url": self._page.url})
        except Exception as exc:
            return _err(f"get_page_text failed: {exc}")

    # -- interaction -----------------------------------------------------------
    def click(self, selector: str) -> Dict:
        if err := self._ensure_browser():
            return _err(err)
        try:
            self._page.click(selector, timeout=10_000)
            return _ok(f"clicked {selector!r}")
        except Exception as exc:
            return _err(f"click failed: {exc}")

    def fill(self, selector: str, value: str) -> Dict:
        if err := self._ensure_browser():
            return _err(err)
        try:
            self._page.fill(selector, value, timeout=10_000)
            return _ok(f"filled {selector!r}")
        except Exception as exc:
            return _err(f"fill failed: {exc}")

    def screenshot(self, path: Optional[str] = None) -> Dict:
        if err := self._ensure_browser():
            return _err(err)
        try:
            import base64
            png = self._page.screenshot(path=path)
            result: Dict = {}
            if path:
                result["path"] = path
            if png:
                result["base64"] = base64.b64encode(png).decode()
            return _ok(result)
        except Exception as exc:
            return _err(f"screenshot failed: {exc}")

    def evaluate(self, js: str) -> Dict:
        """Run arbitrary JavaScript in the page context."""
        if err := self._ensure_browser():
            return _err(err)
        try:
            result = self._page.evaluate(js)
            return _ok(result)
        except Exception as exc:
            return _err(f"evaluate failed: {exc}")

    # -- lightweight HTTP fallback --------------------------------------------
    def fetch_text(self, url: str) -> Dict:
        """No-browser HTTP GET, returns readable text (requests + BeautifulSoup)."""
        if not BROWSER_ENABLED:
            return _err("BrowserAgent disabled")
        if not _HAS_REQUESTS:
            return _err("requests not installed")
        try:
            resp = requests.get(url, timeout=15,
                                headers={"User-Agent": "RGS-AI-Desktop/1.0"})
            resp.raise_for_status()
            if _HAS_BS4:
                soup = BeautifulSoup(resp.text, "html.parser")
                for tag in soup(["script", "style", "head"]):
                    tag.decompose()
                text = soup.get_text(separator=" ", strip=True)
            else:
                text = resp.text
            return _ok({"text": text[:8000], "url": url,
                        "status": resp.status_code})
        except Exception as exc:
            return _err(f"fetch_text failed: {exc}")


# ═══════════════════════════════════════════════════════════════════════════════
# KnowledgeBaseAgent (RAG)
# ═══════════════════════════════════════════════════════════════════════════════

def _simple_embed(text: str, dim: int = 128) -> List[float]:
    """Hash-based pseudo-embedding (no ML model required)."""
    vec = [0.0] * dim
    for i in range(len(text) - 2):
        tri = hash(text[i:i+3]) % dim
        vec[tri] += 1.0
    norm = math.sqrt(sum(v * v for v in vec)) or 1.0
    return [v / norm for v in vec]


def _cosine(a: List[float], b: List[float]) -> float:
    dot = sum(x * y for x, y in zip(a, b))
    na = math.sqrt(sum(x * x for x in a))
    nb = math.sqrt(sum(x * x for x in b))
    return dot / (na * nb) if na and nb else 0.0


@dataclass
class KBDocument:
    id: str
    content: str
    metadata: Dict = field(default_factory=dict)
    embedding: List[float] = field(default_factory=list)
    chunk_index: int = 0


class KnowledgeBaseAgent:
    """
    Lightweight RAG engine: index text → chunk → embed → search → answer.

    Usage:
        kb = KnowledgeBaseAgent()
        kb.add_document("Python is a language", {"source": "manual"})
        results = kb.search("programming language", top_k=3)
        answer  = kb.answer("What is Python?", llm=my_llm)
    """

    def __init__(
        self,
        chunk_size: int = 400,
        chunk_overlap: int = 50,
        embed_fn: Optional[Callable] = None,
        persist_path: Optional[str] = None,
    ):
        self._docs: Dict[str, KBDocument] = {}
        self._lock = RLock()
        self._chunk_size = chunk_size
        self._chunk_overlap = chunk_overlap
        self._embed = embed_fn or _simple_embed
        self._persist_path = Path(os.path.expanduser(persist_path)) if persist_path else None
        if self._persist_path and self._persist_path.exists():
            self._load()

    # -- ingestion -------------------------------------------------------------
    def _chunk(self, text: str) -> List[str]:
        chunks, start = [], 0
        while start < len(text):
            end = start + self._chunk_size
            chunks.append(text[start:end])
            start += self._chunk_size - self._chunk_overlap
        return chunks

    def add_document(self, content: str, metadata: Optional[Dict] = None) -> List[str]:
        """
        Add a document; auto-chunks it.  Returns list of chunk IDs.
        """
        if not KB_ENABLED:
            return []
        chunks = self._chunk(content)
        ids = []
        with self._lock:
            for i, chunk in enumerate(chunks):
                doc_id = hashlib.md5(f"{chunk}{i}".encode()).hexdigest()[:12]
                doc = KBDocument(
                    id=doc_id, content=chunk,
                    metadata=metadata or {},
                    embedding=self._embed(chunk),
                    chunk_index=i,
                )
                self._docs[doc_id] = doc
                ids.append(doc_id)
        log.debug("KB: indexed %d chunks", len(ids))
        return ids

    def add_file(self, path: str) -> List[str]:
        """Read a text file and index it."""
        try:
            text = Path(path).read_text(encoding="utf-8", errors="ignore")
            return self.add_document(text, {"source": path})
        except Exception as exc:
            log.error("KB add_file failed: %s", exc)
            return []

    # -- retrieval -------------------------------------------------------------
    def search(self, query: str, top_k: int = 5) -> List[Dict]:
        if not KB_ENABLED or not self._docs:
            return []
        q_emb = self._embed(query)
        with self._lock:
            scored = sorted(
                (((_cosine(q_emb, doc.embedding), doc) for doc in self._docs.values())),
                key=lambda t: t[0], reverse=True,
            )
        return [
            {"id": doc.id, "content": doc.content[:500],
             "similarity": round(sim, 4), "metadata": doc.metadata}
            for sim, doc in scored[:top_k]
        ]

    def answer(self, question: str, llm: Optional[Callable] = None,
               top_k: int = 3) -> Dict:
        """
        RAG: retrieve context then call llm(prompt) -> str.
        Returns {"ok": bool, "result": {"answer": str, "sources": [...]}}
        """
        chunks = self.search(question, top_k=top_k)
        if not chunks:
            return _err("KB is empty — add documents first")
        context = "\n---\n".join(c["content"] for c in chunks)
        prompt = (
            f"Answer the following question using ONLY the context provided.\n\n"
            f"Context:\n{context}\n\nQuestion: {question}\nAnswer:"
        )
        if llm:
            try:
                ans = llm(prompt)
                return _ok({"answer": ans, "sources": chunks})
            except Exception as exc:
                return _err(f"LLM answer failed: {exc}")
        # no LLM: return raw context
        return _ok({"answer": context[:1000], "sources": chunks,
                    "note": "no LLM provided — returning raw context"})

    # -- persistence -----------------------------------------------------------
    def save(self) -> None:
        if not self._persist_path:
            return
        self._persist_path.parent.mkdir(parents=True, exist_ok=True)
        data = {
            "docs": {
                k: {"id": v.id, "content": v.content,
                    "metadata": v.metadata, "chunk_index": v.chunk_index}
                for k, v in self._docs.items()
            }
        }
        self._persist_path.write_text(json.dumps(data, indent=2))

    def _load(self) -> None:
        try:
            data = json.loads(self._persist_path.read_text())
            for did, d in data.get("docs", {}).items():
                self._docs[did] = KBDocument(
                    id=d["id"], content=d["content"],
                    metadata=d.get("metadata", {}),
                    embedding=self._embed(d["content"]),
                    chunk_index=d.get("chunk_index", 0),
                )
            log.info("KB loaded: %d docs", len(self._docs))
        except Exception as exc:
            log.error("KB load failed: %s", exc)


# ── singletons ────────────────────────────────────────────────────────────────
BROWSER = BrowserAgent()
KB = KnowledgeBaseAgent(
    persist_path=os.environ.get("RGS_KB_PATH", "~/.rgs/knowledge_base.json")
)


# ── smoke tests ───────────────────────────────────────────────────────────────
def smoke_test() -> bool:
    # KB test
    kb = KnowledgeBaseAgent()
    kb.add_document("The RGS AI Desktop is a PyQt6-based agent shell.")
    results = kb.search("PyQt6 agent")
    ok = bool(results)

    # Browser: only check instantiation (no network in CI)
    b = BrowserAgent()
    ok = ok and isinstance(b, BrowserAgent)
    log.info("BrowserAgent smoke_test: %s", "PASS" if ok else "FAIL")
    return ok


if __name__ == "__main__":
    logging.basicConfig(level=logging.DEBUG)
    print(smoke_test())
