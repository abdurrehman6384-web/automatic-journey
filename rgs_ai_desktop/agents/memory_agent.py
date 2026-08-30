"""
MemoryAgent — CANONICAL memory implementation
==============================================
Extracted from Hermes Agent (MIT, NousResearch/hermes-agent)

Provides:
  • Persistent episodic memory (conversation history, events)
  • Skill / fact learning (key-value store with embedding search)
  • Session snapshots to disk (JSON, portable)
  • Lightweight embedding similarity search (without requiring heavy deps)

Capability slot: MEMORY
This is the ONE memory implementation for the whole system.
No other module should maintain its own separate memory store.
"""

from __future__ import annotations

import json
import logging
import math
import os
import time
import uuid
from dataclasses import asdict, dataclass, field
from pathlib import Path
from threading import RLock
from typing import Any, Dict, List, Optional, Tuple

log = logging.getLogger("rgs.memory")

# ── feature flag ──────────────────────────────────────────────────────────────
ENABLED: bool = True

# ── optional embedding support ───────────────────────────────────────────────
try:
    import numpy as np
    _HAS_NUMPY = True
except ImportError:
    _HAS_NUMPY = False


# ── data structures ──────────────────────────────────────────────────────────
@dataclass
class MemoryEntry:
    id: str = field(default_factory=lambda: str(uuid.uuid4())[:8])
    kind: str = "fact"        # "fact" | "episode" | "skill"
    content: str = ""
    metadata: Dict[str, Any] = field(default_factory=dict)
    timestamp: float = field(default_factory=time.time)
    embedding: Optional[List[float]] = None
    access_count: int = 0

    def to_dict(self) -> Dict:
        d = asdict(self)
        d["embedding"] = None   # don't serialise embeddings by default (large)
        return d


@dataclass
class ConversationTurn:
    role: str           # "user" | "assistant" | "system"
    content: str
    timestamp: float = field(default_factory=time.time)
    metadata: Dict[str, Any] = field(default_factory=dict)


# ── simple cosine similarity (no numpy required path) ────────────────────────
def _cosine(a: List[float], b: List[float]) -> float:
    if _HAS_NUMPY:
        va, vb = np.array(a, dtype=float), np.array(b, dtype=float)
        denom = (np.linalg.norm(va) * np.linalg.norm(vb))
        return float(np.dot(va, vb) / denom) if denom else 0.0
    dot = sum(x * y for x, y in zip(a, b))
    norm_a = math.sqrt(sum(x * x for x in a))
    norm_b = math.sqrt(sum(x * x for x in b))
    return dot / (norm_a * norm_b) if norm_a and norm_b else 0.0


# ── hash-based pseudo embedding (no model required) ──────────────────────────
def _hash_embed(text: str, dim: int = 64) -> List[float]:
    """
    Ultra-lightweight deterministic 'embedding' from character n-grams.
    Good enough for deduplication and rough similarity.  Replace with a real
    sentence-transformer when one is available.
    """
    vec = [0.0] * dim
    for i in range(len(text) - 1):
        bi = hash(text[i:i+2]) % dim
        vec[bi] += 1.0
    norm = math.sqrt(sum(v * v for v in vec)) or 1.0
    return [v / norm for v in vec]


# ── MemoryAgent ───────────────────────────────────────────────────────────────
class MemoryAgent:
    """
    Hermes-inspired persistent memory with skill learning.

    Usage:
        mem = MemoryAgent(persist_path="~/.rgs/memory.json")
        mem.remember("The user prefers dark mode", kind="fact")
        mem.add_turn("user", "Hello")
        results = mem.search("dark mode preferences")
    """

    def __init__(
        self,
        persist_path: Optional[str] = None,
        max_history: int = 200,
        embed_fn=None,
    ):
        self._lock = RLock()
        self._entries: Dict[str, MemoryEntry] = {}
        self._history: List[ConversationTurn] = []
        self._max_history = max_history
        self._embed_fn = embed_fn or _hash_embed
        self._dirty = False

        if persist_path:
            self._path = Path(os.path.expanduser(persist_path))
            self._path.parent.mkdir(parents=True, exist_ok=True)
            self._load()
        else:
            self._path = None

    # -- conversation history -------------------------------------------------

    def add_turn(self, role: str, content: str, metadata: Optional[Dict] = None) -> None:
        if not ENABLED:
            return
        with self._lock:
            self._history.append(ConversationTurn(role=role, content=content,
                                                   metadata=metadata or {}))
            if len(self._history) > self._max_history:
                self._history = self._history[-self._max_history:]
            self._dirty = True

    def get_history(self, last_n: int = 20) -> List[Dict]:
        with self._lock:
            return [
                {"role": t.role, "content": t.content, "ts": t.timestamp}
                for t in self._history[-last_n:]
            ]

    def clear_history(self) -> None:
        with self._lock:
            self._history.clear()
            self._dirty = True

    # -- long-term memory ------------------------------------------------------

    def remember(
        self,
        content: str,
        kind: str = "fact",
        metadata: Optional[Dict] = None,
        deduplicate: bool = True,
    ) -> str:
        """Store a fact/skill/episode.  Returns the entry id."""
        if not ENABLED:
            return ""
        with self._lock:
            emb = self._embed_fn(content)
            if deduplicate and self._entries:
                # skip if very similar entry already exists
                for existing in self._entries.values():
                    if existing.embedding and _cosine(existing.embedding, emb) > 0.95:
                        log.debug("memory deduplicated: %s", content[:60])
                        return existing.id
            entry = MemoryEntry(content=content, kind=kind,
                                metadata=metadata or {}, embedding=emb)
            self._entries[entry.id] = entry
            self._dirty = True
            log.debug("memory stored [%s] %s", kind, content[:60])
            return entry.id

    def forget(self, entry_id: str) -> bool:
        with self._lock:
            removed = self._entries.pop(entry_id, None) is not None
            if removed:
                self._dirty = True
            return removed

    def search(
        self,
        query: str,
        top_k: int = 5,
        kind: Optional[str] = None,
    ) -> List[Dict]:
        """Return top-k memory entries most similar to *query*."""
        if not ENABLED or not self._entries:
            return []
        q_emb = self._embed_fn(query)
        with self._lock:
            scored: List[Tuple[float, MemoryEntry]] = []
            for e in self._entries.values():
                if kind and e.kind != kind:
                    continue
                if e.embedding:
                    sim = _cosine(q_emb, e.embedding)
                else:
                    # keyword fallback
                    sim = float(query.lower() in e.content.lower())
                scored.append((sim, e))
            scored.sort(key=lambda t: t[0], reverse=True)
            results = []
            for sim, e in scored[:top_k]:
                e.access_count += 1
                results.append({
                    "id": e.id, "kind": e.kind, "content": e.content,
                    "similarity": round(sim, 4), "metadata": e.metadata,
                })
            return results

    def list_all(self, kind: Optional[str] = None) -> List[Dict]:
        with self._lock:
            entries = list(self._entries.values())
        if kind:
            entries = [e for e in entries if e.kind == kind]
        return [e.to_dict() for e in entries]

    # -- skill learning --------------------------------------------------------

    def learn_skill(self, name: str, description: str, code_or_steps: str) -> str:
        """Store a learned skill (name + description + implementation)."""
        return self.remember(
            content=f"SKILL:{name}\n{description}\n{code_or_steps}",
            kind="skill",
            metadata={"skill_name": name},
        )

    def recall_skill(self, query: str) -> List[Dict]:
        return self.search(query, kind="skill")

    # -- persistence -----------------------------------------------------------

    def save(self) -> None:
        if self._path is None:
            return
        with self._lock:
            data = {
                "entries": {k: v.to_dict() for k, v in self._entries.items()},
                "history": [
                    {"role": t.role, "content": t.content, "ts": t.timestamp}
                    for t in self._history
                ],
            }
            tmp = self._path.with_suffix(".tmp")
            tmp.write_text(json.dumps(data, indent=2))
            tmp.replace(self._path)
            self._dirty = False
        log.info("Memory saved to %s", self._path)

    def _load(self) -> None:
        if self._path is None or not self._path.exists():
            return
        try:
            data = json.loads(self._path.read_text())
            for eid, ed in data.get("entries", {}).items():
                e = MemoryEntry(
                    id=ed["id"], kind=ed.get("kind", "fact"),
                    content=ed["content"], metadata=ed.get("metadata", {}),
                    timestamp=ed.get("timestamp", time.time()),
                    embedding=self._embed_fn(ed["content"]),
                )
                self._entries[eid] = e
            for t in data.get("history", []):
                self._history.append(ConversationTurn(
                    role=t["role"], content=t["content"],
                    timestamp=t.get("ts", time.time()),
                ))
            log.info("Memory loaded: %d entries, %d turns",
                     len(self._entries), len(self._history))
        except Exception as exc:
            log.error("Could not load memory: %s", exc)

    def auto_save_if_dirty(self) -> None:
        if self._dirty:
            self.save()

    def summary(self) -> Dict:
        with self._lock:
            kinds: Dict[str, int] = {}
            for e in self._entries.values():
                kinds[e.kind] = kinds.get(e.kind, 0) + 1
            return {
                "total_entries": len(self._entries),
                "history_turns": len(self._history),
                "by_kind": kinds,
                "persist_path": str(self._path) if self._path else None,
            }


# ── module-level singleton ────────────────────────────────────────────────────
AGENT = MemoryAgent(persist_path=os.environ.get("RGS_MEMORY_PATH", "~/.rgs/memory.json"))


# ── smoke test ────────────────────────────────────────────────────────────────
def smoke_test() -> bool:
    mem = MemoryAgent()          # in-memory only
    eid = mem.remember("Python uses indentation", kind="fact")
    results = mem.search("Python")
    ok = bool(results and results[0]["id"] == eid)
    mem.add_turn("user", "hello")
    ok = ok and len(mem.get_history()) == 1
    log.info("MemoryAgent smoke_test: %s", "PASS" if ok else "FAIL")
    return ok


if __name__ == "__main__":
    logging.basicConfig(level=logging.DEBUG)
    print(smoke_test())
    print(json.dumps(AGENT.summary(), indent=2))
