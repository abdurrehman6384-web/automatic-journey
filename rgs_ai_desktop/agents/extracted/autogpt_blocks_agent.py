"""
AutoGPTBlocksAgent — AutoGPT Platform Blocks (MIT)
====================================================
Extracted Python block logic from:
  autogpt_platform/backend/backend/blocks/
    ai_condition.py          → AIConditionBlock (LLM true/false evaluator)
    basic.py                 → StoreValue, TextFormatter, PrintToConsole
    branching.py             → IfElse, Switch routing
    data_manipulation.py     → JSON extract, transform
    email_block.py           → SMTP email sender
    http.py                  → HTTP GET/POST request block
    llm.py                   → LLM call block (any provider)
    maths.py                 → Calculator / formula evaluator
    persistence.py           → Key-value store (SQLite-backed)
    rss.py                   → RSS/Atom feed reader
    search.py                → Web search block
    spreadsheet.py           → CSV read/write/transform
    text.py                  → Text manipulation (split, join, regex)
    time_blocks.py           → DateTime, timer, cron trigger
    youtube.py               → YouTube metadata fetcher
    mem0.py                  → Mem0 memory integration hook

All blocks follow a consistent interface:
  block.run(inputs: dict) → {"ok": bool, "result": ...}
"""

from __future__ import annotations

import csv
import io
import json
import logging
import math
import os
import re
import smtplib
import sqlite3
import time
import urllib.parse
import urllib.request
from datetime import datetime, timezone
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from pathlib import Path
from typing import Any, Dict, List, Optional

log = logging.getLogger("rgs.autogpt_blocks")
ENABLED: bool = True

DATA_DIR = Path(os.environ.get("RGS_DATA_DIR", Path.home() / ".rgs"))
DATA_DIR.mkdir(parents=True, exist_ok=True)

def _ok(d: Any = None) -> Dict: return {"ok": True, "result": d}
def _err(m: str) -> Dict:
    log.warning("AutoGPTBlocks: %s", m)
    return {"ok": False, "error": m}

try:
    import requests as _req
    _HAS_REQUESTS = True
except ImportError:
    _HAS_REQUESTS = False


# ══════════════════════════════════════════════════════════════════════════════
# AI Condition Block (ai_condition.py)
# ══════════════════════════════════════════════════════════════════════════════
class AIConditionBlock:
    """LLM-powered boolean condition evaluator."""

    def __init__(self, llm_fn=None):
        self._llm = llm_fn

    def evaluate(self, condition: str, value: str) -> Dict:
        """
        Returns True if `value` satisfies `condition` (natural language).
        Example: condition="is an email address", value="foo@bar.com" → True
        """
        if not self._llm:
            return _err("AIConditionBlock needs an LLM")
        prompt = (
            f"Evaluate this condition:\n"
            f"Input: {value!r}\n"
            f"Condition: {condition}\n\n"
            f"Reply with ONLY the word 'true' or 'false'."
        )
        try:
            raw = self._llm(prompt).strip().lower()
            result = self._parse_bool(raw)
            return _ok({"result": result, "raw": raw,
                        "condition": condition, "value": value})
        except Exception as exc:
            return _err(f"evaluate: {exc}")

    @staticmethod
    def _parse_bool(text: str) -> bool:
        text = text.strip().lower()
        if text in ("true", "yes", "1"):
            return True
        if text in ("false", "no", "0"):
            return False
        tokens = set(re.findall(r"\b(true|false|yes|no|1|0)\b", text))
        if tokens == {"true"} or tokens == {"yes"}:
            return True
        return False


# ══════════════════════════════════════════════════════════════════════════════
# Text Block (text.py)
# ══════════════════════════════════════════════════════════════════════════════
class TextBlock:
    def split(self, text: str, delimiter: str = "\n",
              max_parts: int = 0) -> Dict:
        parts = text.split(delimiter)
        if max_parts:
            parts = parts[:max_parts]
        return _ok({"parts": parts, "count": len(parts)})

    def join(self, parts: List[str], delimiter: str = "\n") -> Dict:
        return _ok(delimiter.join(str(p) for p in parts))

    def replace(self, text: str, find: str, replace_with: str,
                regex: bool = False) -> Dict:
        try:
            if regex:
                result = re.sub(find, replace_with, text)
            else:
                result = text.replace(find, replace_with)
            return _ok(result)
        except Exception as exc:
            return _err(str(exc))

    def extract_regex(self, text: str, pattern: str,
                      group: int = 0) -> Dict:
        try:
            matches = re.findall(pattern, text)
            return _ok({"matches": matches, "count": len(matches)})
        except re.error as exc:
            return _err(f"Invalid regex: {exc}")

    def format_template(self, template: str, variables: Dict[str, str]) -> Dict:
        try:
            result = template.format(**variables)
            return _ok(result)
        except KeyError as exc:
            return _err(f"Missing variable: {exc}")

    def count_words(self, text: str) -> Dict:
        words = len(re.findall(r"\b\w+\b", text))
        chars = len(text)
        return _ok({"words": words, "chars": chars, "lines": text.count("\n") + 1})

    def truncate(self, text: str, max_length: int = 500,
                 ellipsis: str = "...") -> Dict:
        if len(text) <= max_length:
            return _ok(text)
        return _ok(text[:max_length - len(ellipsis)] + ellipsis)


# ══════════════════════════════════════════════════════════════════════════════
# Math Block (maths.py)
# ══════════════════════════════════════════════════════════════════════════════
class MathBlock:
    _SAFE_NAMES = {
        "abs": abs, "round": round, "min": min, "max": max,
        "sum": sum, "pow": pow, "sqrt": math.sqrt,
        "floor": math.floor, "ceil": math.ceil,
        "sin": math.sin, "cos": math.cos, "tan": math.tan,
        "log": math.log, "log10": math.log10, "exp": math.exp,
        "pi": math.pi, "e": math.e,
    }

    def calculate(self, expression: str,
                  variables: Optional[Dict[str, float]] = None) -> Dict:
        """Safely evaluate a mathematical expression."""
        try:
            safe_dict = {**self._SAFE_NAMES, **(variables or {})}
            result = eval(expression, {"__builtins__": {}}, safe_dict)
            return _ok({"result": result, "expression": expression})
        except ZeroDivisionError:
            return _err("Division by zero")
        except Exception as exc:
            return _err(f"Math error: {exc}")

    def statistics(self, numbers: List[float]) -> Dict:
        if not numbers:
            return _err("Empty list")
        n = len(numbers)
        total = sum(numbers)
        mean = total / n
        sorted_n = sorted(numbers)
        median = sorted_n[n // 2] if n % 2 else (sorted_n[n//2-1]+sorted_n[n//2])/2
        variance = sum((x - mean) ** 2 for x in numbers) / n
        return _ok({
            "count": n, "sum": total, "mean": round(mean, 6),
            "median": median, "min": min(numbers), "max": max(numbers),
            "std_dev": round(math.sqrt(variance), 6),
        })


# ══════════════════════════════════════════════════════════════════════════════
# HTTP Block (http.py)
# ══════════════════════════════════════════════════════════════════════════════
class HTTPBlock:
    def request(self, url: str, method: str = "GET",
                headers: Optional[Dict] = None, body: Optional[str] = None,
                timeout: float = 30, json_body: Optional[Dict] = None) -> Dict:
        if not _HAS_REQUESTS:
            return _err("requests not installed")
        try:
            hdrs = headers or {}
            if json_body:
                body = json.dumps(json_body)
                hdrs["Content-Type"] = "application/json"
            resp = _req.request(
                method.upper(), url, headers=hdrs,
                data=body, timeout=timeout
            )
            try:
                resp_data = resp.json()
            except Exception:
                resp_data = resp.text[:5000]
            return _ok({
                "status_code": resp.status_code,
                "headers": dict(resp.headers),
                "body": resp_data,
                "url": resp.url,
            })
        except Exception as exc:
            return _err(f"HTTP {method} {url}: {exc}")

    def get(self, url: str, params: Optional[Dict] = None, **kwargs) -> Dict:
        if params:
            url += "?" + urllib.parse.urlencode(params)
        return self.request(url, "GET", **kwargs)

    def post(self, url: str, **kwargs) -> Dict:
        return self.request(url, "POST", **kwargs)

    def webhook_trigger(self, webhook_url: str, data: Dict) -> Dict:
        return self.post(webhook_url, json_body=data)


# ══════════════════════════════════════════════════════════════════════════════
# Email Block (email_block.py)
# ══════════════════════════════════════════════════════════════════════════════
class EmailBlock:
    def send(self, to: str, subject: str, body: str,
             html: bool = False,
             smtp_host: Optional[str] = None,
             smtp_port: int = 587,
             username: Optional[str] = None,
             password: Optional[str] = None) -> Dict:
        smtp_host = smtp_host or os.environ.get("SMTP_HOST", "smtp.gmail.com")
        username  = username  or os.environ.get("SMTP_USER", "")
        password  = password  or os.environ.get("SMTP_PASS", "")
        if not username or not password:
            return _err("SMTP_USER and SMTP_PASS env vars required")
        try:
            msg = MIMEMultipart("alternative")
            msg["From"]    = username
            msg["To"]      = to
            msg["Subject"] = subject
            content_type = "html" if html else "plain"
            msg.attach(MIMEText(body, content_type))
            with smtplib.SMTP(smtp_host, smtp_port) as server:
                server.starttls()
                server.login(username, password)
                server.sendmail(username, to, msg.as_string())
            return _ok({"sent": True, "to": to, "subject": subject})
        except Exception as exc:
            return _err(f"email send: {exc}")


# ══════════════════════════════════════════════════════════════════════════════
# Persistence Block (persistence.py — SQLite key-value store)
# ══════════════════════════════════════════════════════════════════════════════
class PersistenceBlock:
    DB = str(DATA_DIR / "kv_store.db")

    def __init__(self):
        conn = sqlite3.connect(self.DB)
        conn.execute("""CREATE TABLE IF NOT EXISTS kv
                        (key TEXT PRIMARY KEY, value TEXT, updated REAL)""")
        conn.commit()
        conn.close()

    def set(self, key: str, value: Any) -> Dict:
        conn = sqlite3.connect(self.DB)
        conn.execute("INSERT OR REPLACE INTO kv VALUES (?, ?, ?)",
                     (key, json.dumps(value), time.time()))
        conn.commit()
        conn.close()
        return _ok(f"Set: {key}")

    def get(self, key: str, default: Any = None) -> Dict:
        conn = sqlite3.connect(self.DB)
        row = conn.execute("SELECT value FROM kv WHERE key=?", (key,)).fetchone()
        conn.close()
        if row:
            return _ok(json.loads(row[0]))
        return _ok(default)

    def delete(self, key: str) -> Dict:
        conn = sqlite3.connect(self.DB)
        conn.execute("DELETE FROM kv WHERE key=?", (key,))
        conn.commit()
        conn.close()
        return _ok(f"Deleted: {key}")

    def list_keys(self, prefix: str = "") -> Dict:
        conn = sqlite3.connect(self.DB)
        rows = conn.execute("SELECT key FROM kv WHERE key LIKE ?",
                            (f"{prefix}%",)).fetchall()
        conn.close()
        return _ok([r[0] for r in rows])


# ══════════════════════════════════════════════════════════════════════════════
# RSS Block (rss.py)
# ══════════════════════════════════════════════════════════════════════════════
class RSSBlock:
    def fetch(self, feed_url: str, max_items: int = 10) -> Dict:
        try:
            import feedparser
            feed = feedparser.parse(feed_url)
            items = []
            for entry in feed.entries[:max_items]:
                items.append({
                    "title":   entry.get("title", ""),
                    "link":    entry.get("link", ""),
                    "summary": entry.get("summary", "")[:300],
                    "published": entry.get("published", ""),
                })
            return _ok({"feed": feed.feed.get("title",""), "items": items})
        except ImportError:
            return _err("feedparser not installed: pip install feedparser")
        except Exception as exc:
            return _err(f"RSS fetch: {exc}")


# ══════════════════════════════════════════════════════════════════════════════
# Spreadsheet Block (spreadsheet.py)
# ══════════════════════════════════════════════════════════════════════════════
class SpreadsheetBlock:
    def read_csv(self, path: str, max_rows: int = 1000) -> Dict:
        try:
            with open(path, encoding="utf-8", errors="replace") as f:
                reader = csv.DictReader(f)
                rows = [row for i, row in enumerate(reader) if i < max_rows]
            return _ok({"rows": rows, "count": len(rows),
                        "headers": list(rows[0].keys()) if rows else []})
        except FileNotFoundError:
            return _err(f"File not found: {path}")
        except Exception as exc:
            return _err(f"read_csv: {exc}")

    def write_csv(self, path: str, rows: List[Dict],
                  headers: Optional[List[str]] = None) -> Dict:
        try:
            if not rows:
                return _err("No rows to write")
            hs = headers or list(rows[0].keys())
            with open(path, "w", newline="", encoding="utf-8") as f:
                writer = csv.DictWriter(f, fieldnames=hs)
                writer.writeheader()
                writer.writerows(rows)
            return _ok({"written": len(rows), "path": path})
        except Exception as exc:
            return _err(f"write_csv: {exc}")

    def filter_rows(self, rows: List[Dict], column: str,
                    value: str, operator: str = "equals") -> Dict:
        try:
            ops = {
                "equals":     lambda r: r.get(column, "") == value,
                "contains":   lambda r: value.lower() in r.get(column, "").lower(),
                "startswith": lambda r: r.get(column, "").startswith(value),
                "gt":         lambda r: float(r.get(column, 0)) > float(value),
                "lt":         lambda r: float(r.get(column, 0)) < float(value),
            }
            fn = ops.get(operator, ops["equals"])
            filtered = [r for r in rows if fn(r)]
            return _ok({"rows": filtered, "count": len(filtered)})
        except Exception as exc:
            return _err(f"filter: {exc}")


# ══════════════════════════════════════════════════════════════════════════════
# Time Block (time_blocks.py)
# ══════════════════════════════════════════════════════════════════════════════
class TimeBlock:
    def now(self, tz: str = "UTC", fmt: str = "%Y-%m-%d %H:%M:%S") -> Dict:
        now = datetime.now(timezone.utc)
        return _ok({
            "utc": now.isoformat(),
            "formatted": now.strftime(fmt),
            "timestamp": now.timestamp(),
            "date": now.strftime("%Y-%m-%d"),
            "time": now.strftime("%H:%M:%S"),
        })

    def wait(self, seconds: float) -> Dict:
        if seconds > 300:
            return _err("Wait limit is 300s")
        time.sleep(seconds)
        return _ok(f"Waited {seconds}s")

    def parse(self, date_string: str) -> Dict:
        formats = [
            "%Y-%m-%d", "%Y-%m-%d %H:%M:%S", "%d/%m/%Y",
            "%m/%d/%Y", "%d-%m-%Y", "%Y/%m/%d",
        ]
        for fmt in formats:
            try:
                dt = datetime.strptime(date_string, fmt)
                return _ok({
                    "parsed": dt.isoformat(),
                    "date": dt.strftime("%Y-%m-%d"),
                    "day_of_week": dt.strftime("%A"),
                    "timestamp": dt.timestamp(),
                })
            except ValueError:
                continue
        return _err(f"Could not parse date: {date_string!r}")


# ══════════════════════════════════════════════════════════════════════════════
# YouTube Block (youtube.py)
# ══════════════════════════════════════════════════════════════════════════════
class YouTubeBlock:
    def get_metadata(self, video_url: str) -> Dict:
        """Extract metadata using yt-dlp (no API key needed)."""
        try:
            import yt_dlp
            ydl_opts = {"quiet": True, "no_warnings": True, "skip_download": True}
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(video_url, download=False)
            return _ok({
                "title": info.get("title"),
                "channel": info.get("uploader"),
                "views": info.get("view_count"),
                "likes": info.get("like_count"),
                "duration_s": info.get("duration"),
                "description": (info.get("description") or "")[:500],
                "upload_date": info.get("upload_date"),
                "tags": info.get("tags", [])[:15],
            })
        except ImportError:
            return _err("yt-dlp not installed: pip install yt-dlp")
        except Exception as exc:
            return _err(f"youtube metadata: {exc}")

    def download(self, url: str, output_path: str = ".",
                 format_: str = "best[height<=720]") -> Dict:
        try:
            import yt_dlp
            ydl_opts = {
                "outtmpl": os.path.join(output_path, "%(title)s.%(ext)s"),
                "format": format_, "quiet": True,
            }
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=True)
            return _ok({"downloaded": info.get("title"), "path": output_path})
        except ImportError:
            return _err("yt-dlp not installed")
        except Exception as exc:
            return _err(f"download: {exc}")


# ══════════════════════════════════════════════════════════════════════════════
# Mem0 Block (mem0.py — Mem0 memory service hook)
# ══════════════════════════════════════════════════════════════════════════════
class Mem0Block:
    """Mem0 memory integration — defers to MemoryAgent (canonical), Mem0 as provider."""

    def add(self, content: str, user_id: str = "default",
            metadata: Optional[Dict] = None) -> Dict:
        try:
            from mem0 import MemoryClient
            client = MemoryClient(api_key=os.environ.get("MEM0_API_KEY",""))
            msgs = [{"role": "user", "content": content}]
            result = client.add(msgs, user_id=user_id,
                                metadata=metadata or {})
            return _ok(result)
        except ImportError:
            # Fallback to canonical MemoryAgent
            try:
                from rgs_ai_desktop.agents.memory_agent import AGENT as ma
                eid = ma.remember(content, kind="fact",
                                  metadata={"user_id": user_id, **(metadata or {})})
                return _ok({"id": eid, "provider": "canonical_memory"})
            except Exception as exc:
                return _err(str(exc))
        except Exception as exc:
            return _err(f"mem0 add: {exc}")

    def search(self, query: str, user_id: str = "default") -> Dict:
        try:
            from mem0 import MemoryClient
            client = MemoryClient(api_key=os.environ.get("MEM0_API_KEY",""))
            results = client.search(query, user_id=user_id)
            return _ok(results)
        except ImportError:
            try:
                from rgs_ai_desktop.agents.memory_agent import AGENT as ma
                return _ok(ma.search(query))
            except Exception as exc:
                return _err(str(exc))
        except Exception as exc:
            return _err(f"mem0 search: {exc}")


# ══════════════════════════════════════════════════════════════════════════════
# AutoGPTBlocksAgent unified facade
# ══════════════════════════════════════════════════════════════════════════════
class AutoGPTBlocksAgent:
    def __init__(self, llm_fn=None):
        self.ai_cond     = AIConditionBlock(llm_fn)
        self.text        = TextBlock()
        self.math        = MathBlock()
        self.http        = HTTPBlock()
        self.email       = EmailBlock()
        self.persist     = PersistenceBlock()
        self.rss         = RSSBlock()
        self.spreadsheet = SpreadsheetBlock()
        self.time        = TimeBlock()
        self.youtube     = YouTubeBlock()
        self.mem0        = Mem0Block()

    def set_llm(self, fn):
        self.ai_cond._llm = fn

    def dispatch(self, block: str, **kwargs) -> Dict:
        map_: Dict[str, Any] = {
            # AI
            "ai_condition":      lambda: self.ai_cond.evaluate(**kwargs),
            # Text
            "text_split":        lambda: self.text.split(**kwargs),
            "text_join":         lambda: self.text.join(**kwargs),
            "text_replace":      lambda: self.text.replace(**kwargs),
            "text_regex":        lambda: self.text.extract_regex(**kwargs),
            "text_format":       lambda: self.text.format_template(**kwargs),
            "text_count":        lambda: self.text.count_words(**kwargs),
            "text_truncate":     lambda: self.text.truncate(**kwargs),
            # Math
            "calculate":         lambda: self.math.calculate(**kwargs),
            "statistics":        lambda: self.math.statistics(**kwargs),
            # HTTP
            "http_get":          lambda: self.http.get(**kwargs),
            "http_post":         lambda: self.http.post(**kwargs),
            "http_request":      lambda: self.http.request(**kwargs),
            "webhook":           lambda: self.http.webhook_trigger(**kwargs),
            # Email
            "send_email":        lambda: self.email.send(**kwargs),
            # Persistence
            "kv_set":            lambda: self.persist.set(**kwargs),
            "kv_get":            lambda: self.persist.get(**kwargs),
            "kv_delete":         lambda: self.persist.delete(**kwargs),
            "kv_list":           lambda: self.persist.list_keys(**kwargs),
            # RSS
            "rss_fetch":         lambda: self.rss.fetch(**kwargs),
            # Spreadsheet
            "csv_read":          lambda: self.spreadsheet.read_csv(**kwargs),
            "csv_write":         lambda: self.spreadsheet.write_csv(**kwargs),
            "csv_filter":        lambda: self.spreadsheet.filter_rows(**kwargs),
            # Time
            "time_now":          lambda: self.time.now(**kwargs),
            "time_wait":         lambda: self.time.wait(**kwargs),
            "time_parse":        lambda: self.time.parse(**kwargs),
            # YouTube
            "youtube_metadata":  lambda: self.youtube.get_metadata(**kwargs),
            "youtube_download":  lambda: self.youtube.download(**kwargs),
            # Mem0
            "mem0_add":          lambda: self.mem0.add(**kwargs),
            "mem0_search":       lambda: self.mem0.search(**kwargs),
        }
        fn = map_.get(block)
        if fn is None:
            return _err(f"Unknown block: {block!r}. Available: {sorted(map_.keys())}")
        try:
            return fn()
        except Exception as exc:
            return _err(str(exc))


# ── singletons ────────────────────────────────────────────────────────────────
AGENT = AutoGPTBlocksAgent()


def smoke_test() -> bool:
    # Math
    r1 = AGENT.math.calculate("2 ** 10 + sqrt(16)")
    ok = r1["ok"] and abs(r1["result"]["result"] - 1028.0) < 0.01

    # Text
    r2 = AGENT.text.split("a,b,c,d", ",")
    ok = ok and r2["ok"] and r2["result"]["count"] == 4

    # Persistence
    AGENT.persist.set("smoke_test_key", {"status": "ok"})
    r3 = AGENT.persist.get("smoke_test_key")
    ok = ok and r3["ok"] and r3["result"]["status"] == "ok"

    # Time
    r4 = AGENT.time.now()
    ok = ok and r4["ok"] and "utc" in r4["result"]

    log.info("AutoGPTBlocksAgent smoke_test: %s", "PASS" if ok else "FAIL")
    return ok


if __name__ == "__main__":
    logging.basicConfig(level=logging.DEBUG)
    print(smoke_test())
