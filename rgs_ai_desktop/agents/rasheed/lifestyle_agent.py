"""
LifestyleAgent — RASHEED Lifestyle Features (from abdurrehman-ai project.zip)
==============================================================================
Integrates: lifestyle.py, budget_manager.py, idea_capture.py,
            reminder.py, quant_finance_pro.py, knowledge_graph.py

Features:
  - Islamic Prayer Times (Aladhan API)
  - Crypto/stock prices (Binance/CoinGecko)
  - Budget & expense tracker (SQLite)
  - Pomodoro timer
  - Reminders (system scheduler)
  - Knowledge Graph (entity-relationship memory)
  - Idea/Dream journal
  - Finance tracker (arbitrage, sentiment)
"""

from __future__ import annotations

import json
import logging
import os
import sqlite3
import subprocess
import sys
import threading
import time
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

log = logging.getLogger("rgs.lifestyle")
ENABLED: bool = True

DATA_DIR = Path(os.environ.get("RGS_DATA_DIR", Path.home() / ".rgs"))
DATA_DIR.mkdir(parents=True, exist_ok=True)


def _ok(d: Any = None) -> Dict: return {"ok": True, "result": d}
def _err(m: str) -> Dict:
    log.warning("LifestyleAgent: %s", m)
    return {"ok": False, "error": m}

try:
    import requests as _requests
    _HAS_REQUESTS = True
except ImportError:
    _HAS_REQUESTS = False


# ══════════════════════════════════════════════════════════════════════════════
# Prayer Times (Aladhan API)
# ══════════════════════════════════════════════════════════════════════════════
class PrayerTimesService:
    def get_times(self, city: str = "Lahore", country: str = "Pakistan") -> Dict:
        if not _HAS_REQUESTS:
            return _err("requests not installed")
        try:
            url = (f"http://api.aladhan.com/v1/timingsByCity"
                   f"?city={city}&country={country}&method=1")
            r = _requests.get(url, timeout=8)
            data = r.json()["data"]["timings"]
            return _ok({
                "city": city,
                "Fajr":    data.get("Fajr"),
                "Sunrise": data.get("Sunrise"),
                "Dhuhr":   data.get("Dhuhr"),
                "Asr":     data.get("Asr"),
                "Maghrib": data.get("Maghrib"),
                "Isha":    data.get("Isha"),
            })
        except Exception as exc:
            return _err(f"Prayer times error: {exc}")


# ══════════════════════════════════════════════════════════════════════════════
# Crypto Tracker
# ══════════════════════════════════════════════════════════════════════════════
class CryptoTracker:
    def get_price(self, symbol: str = "BTC") -> Dict:
        if not _HAS_REQUESTS:
            return _err("requests not installed")
        # Try Binance first, then CoinGecko
        try:
            r = _requests.get(
                f"https://api.binance.com/api/v3/ticker/price?symbol={symbol.upper()}USDT",
                timeout=5
            )
            if r.ok:
                price = float(r.json()["price"])
                return _ok({"symbol": symbol.upper(), "price_usd": round(price, 4),
                            "source": "binance"})
        except Exception:
            pass
        try:
            r = _requests.get(
                f"https://api.coingecko.com/api/v3/simple/price?ids={symbol.lower()}&vs_currencies=usd",
                timeout=5
            )
            if r.ok:
                data = r.json()
                price = list(data.values())[0].get("usd", 0) if data else 0
                return _ok({"symbol": symbol, "price_usd": price, "source": "coingecko"})
        except Exception as exc:
            return _err(f"crypto price error: {exc}")
        return _err("Could not fetch price")

    def get_fear_greed(self) -> Dict:
        if not _HAS_REQUESTS:
            return _err("requests not installed")
        try:
            r = _requests.get("https://api.alternative.me/fng/?limit=1", timeout=5)
            d = r.json()["data"][0]
            return _ok({"index": int(d["value"]), "label": d["value_classification"]})
        except Exception as exc:
            return _err(str(exc))


# ══════════════════════════════════════════════════════════════════════════════
# Budget Manager (SQLite)
# ══════════════════════════════════════════════════════════════════════════════
class BudgetManager:
    DB = str(DATA_DIR / "budget.db")

    AUTO_CATEGORIES = {
        "lunch": "Food", "dinner": "Food", "breakfast": "Food", "chai": "Food",
        "petrol": "Transport", "uber": "Transport", "taxi": "Transport",
        "electricity": "Bills", "gas": "Bills", "internet": "Bills",
        "medicine": "Health", "doctor": "Health",
    }

    def __init__(self):
        self._setup()

    def _setup(self):
        conn = sqlite3.connect(self.DB)
        c = conn.cursor()
        c.execute("""CREATE TABLE IF NOT EXISTS expenses
                     (id INTEGER PRIMARY KEY, amount REAL, category TEXT,
                      description TEXT, date TEXT)""")
        c.execute("""CREATE TABLE IF NOT EXISTS budget_limits
                     (category TEXT PRIMARY KEY, limit_amount REAL)""")
        conn.commit()
        conn.close()

    def _auto_cat(self, desc: str) -> str:
        for kw, cat in self.AUTO_CATEGORIES.items():
            if kw in desc.lower():
                return cat
        return "Other"

    def add_expense(self, amount: float, description: str,
                    category: Optional[str] = None) -> Dict:
        cat = category or self._auto_cat(description)
        conn = sqlite3.connect(self.DB)
        c = conn.cursor()
        c.execute("INSERT INTO expenses (amount, category, description, date) VALUES (?, ?, ?, ?)",
                  (amount, cat, description, datetime.now().isoformat()))
        conn.commit()
        conn.close()
        return _ok({"added": True, "amount": amount, "category": cat})

    def get_summary(self, days: int = 30) -> Dict:
        conn = sqlite3.connect(self.DB)
        c = conn.cursor()
        c.execute("""SELECT category, SUM(amount), COUNT(*) FROM expenses
                     WHERE date >= datetime('now', ?)
                     GROUP BY category ORDER BY SUM(amount) DESC""",
                  (f"-{days} days",))
        rows = c.fetchall()
        total = sum(r[1] for r in rows)
        conn.close()
        return _ok({"days": days, "total": round(total, 2),
                    "breakdown": [{"category": r[0], "amount": round(r[1], 2),
                                   "count": r[2]} for r in rows]})

    def set_budget_limit(self, category: str, limit: float) -> Dict:
        conn = sqlite3.connect(self.DB)
        conn.execute("INSERT OR REPLACE INTO budget_limits VALUES (?, ?)", (category, limit))
        conn.commit()
        conn.close()
        return _ok(f"Limit set: {category} = {limit}")


# ══════════════════════════════════════════════════════════════════════════════
# Reminder System
# ══════════════════════════════════════════════════════════════════════════════
class ReminderService:
    """Simple thread-based reminder — OS-agnostic."""

    def __init__(self):
        self._reminders: List[Dict] = []
        self._thread: Optional[threading.Thread] = None
        self._running = False
        self._lock = threading.Lock()

    def set_reminder(self, message: str, at: str,
                     notify_fn=None) -> Dict:
        """
        Set a reminder.
        at: "HH:MM" today OR "YYYY-MM-DD HH:MM"
        """
        try:
            try:
                dt = datetime.strptime(at, "%Y-%m-%d %H:%M")
            except ValueError:
                today = datetime.now().strftime("%Y-%m-%d")
                dt = datetime.strptime(f"{today} {at}", "%Y-%m-%d %H:%M")
            if dt <= datetime.now():
                return _err("Reminder time is in the past")
            with self._lock:
                self._reminders.append({
                    "message": message, "dt": dt,
                    "notify": notify_fn, "fired": False
                })
            self._ensure_thread()
            return _ok(f"Reminder set for {dt.strftime('%Y-%m-%d %H:%M')}: {message}")
        except Exception as exc:
            return _err(f"set_reminder failed: {exc}")

    def _ensure_thread(self):
        if not self._running:
            self._running = True
            self._thread = threading.Thread(target=self._loop, daemon=True)
            self._thread.start()

    def _loop(self):
        while self._running:
            now = datetime.now()
            with self._lock:
                for r in self._reminders:
                    if not r["fired"] and now >= r["dt"]:
                        r["fired"] = True
                        try:
                            if r["notify"]:
                                r["notify"](r["message"])
                            else:
                                log.info("REMINDER: %s", r["message"])
                        except Exception:
                            pass
            time.sleep(20)

    def list_reminders(self) -> Dict:
        with self._lock:
            return _ok([{"message": r["message"],
                          "at": r["dt"].isoformat(),
                          "fired": r["fired"]}
                        for r in self._reminders])


# ══════════════════════════════════════════════════════════════════════════════
# Knowledge Graph (entity-relationship memory)
# ══════════════════════════════════════════════════════════════════════════════
class KnowledgeGraph:
    """
    Stores entities and relationships.
    E.g.: 'Ahmed is my brother, lives in Dubai, likes Biryani'
    """
    FILE = str(DATA_DIR / "knowledge_graph.json")

    def __init__(self):
        self.entities: Dict[str, Dict] = {}
        self.relations: List[Dict] = []
        self._load()

    def _load(self):
        if os.path.exists(self.FILE):
            try:
                with open(self.FILE, encoding="utf-8") as f:
                    d = json.load(f)
                    self.entities = d.get("entities", {})
                    self.relations = d.get("relations", [])
            except Exception:
                pass

    def _save(self):
        try:
            with open(self.FILE, "w", encoding="utf-8") as f:
                json.dump({"entities": self.entities, "relations": self.relations},
                          f, ensure_ascii=False, indent=2)
        except Exception as exc:
            log.error("KnowledgeGraph save error: %s", exc)

    def add_entity(self, name: str, entity_type: str = "person",
                   attributes: Optional[Dict] = None) -> Dict:
        name = name.strip().title()
        if name not in self.entities:
            self.entities[name] = {"type": entity_type, "attributes": {}}
        if attributes:
            self.entities[name]["attributes"].update(attributes)
        self._save()
        return _ok(f"Entity '{name}' saved")

    def add_relation(self, from_: str, relation: str, to: str) -> Dict:
        self.relations.append({"from": from_.title(), "relation": relation,
                                "to": to.title()})
        self._save()
        return _ok(f"{from_} -{relation}-> {to}")

    def query(self, name: str) -> Dict:
        name = name.strip().title()
        entity = self.entities.get(name, {})
        rels = [r for r in self.relations if r["from"] == name or r["to"] == name]
        return _ok({"entity": name, "data": entity, "relations": rels})

    def search(self, query: str) -> Dict:
        q = query.lower()
        found = {k: v for k, v in self.entities.items() if q in k.lower()}
        return _ok(found)


# ══════════════════════════════════════════════════════════════════════════════
# Idea / Dream Journal
# ══════════════════════════════════════════════════════════════════════════════
class IdeaJournal:
    DB = str(DATA_DIR / "ideas.db")

    def __init__(self):
        conn = sqlite3.connect(self.DB)
        conn.execute("""CREATE TABLE IF NOT EXISTS ideas
                        (id INTEGER PRIMARY KEY, type TEXT, content TEXT,
                         mood TEXT, timestamp TEXT)""")
        conn.commit()
        conn.close()

    def _add(self, idea_type: str, content: str, mood: str = "") -> Dict:
        conn = sqlite3.connect(self.DB)
        conn.execute("INSERT INTO ideas (type, content, mood, timestamp) VALUES (?, ?, ?, ?)",
                     (idea_type, content, mood, datetime.now().isoformat()))
        conn.commit()
        conn.close()
        return _ok(f"{idea_type.title()} saved")

    def log_idea(self, content: str, mood: str = "") -> Dict:
        return self._add("idea", content, mood)

    def log_dream(self, content: str) -> Dict:
        return self._add("dream", content)

    def list_ideas(self, idea_type: Optional[str] = None, limit: int = 20) -> Dict:
        conn = sqlite3.connect(self.DB)
        if idea_type:
            rows = conn.execute("SELECT type, content, mood, timestamp FROM ideas WHERE type=? ORDER BY id DESC LIMIT ?",
                                (idea_type, limit)).fetchall()
        else:
            rows = conn.execute("SELECT type, content, mood, timestamp FROM ideas ORDER BY id DESC LIMIT ?",
                                (limit,)).fetchall()
        conn.close()
        return _ok([{"type": r[0], "content": r[1], "mood": r[2], "ts": r[3]} for r in rows])


# ══════════════════════════════════════════════════════════════════════════════
# Pomodoro Timer
# ══════════════════════════════════════════════════════════════════════════════
class PomodoroTimer:
    def __init__(self):
        self._active = False
        self._thread: Optional[threading.Thread] = None

    def start(self, work_min: int = 25, break_min: int = 5,
              on_notify=None) -> Dict:
        if self._active:
            return _err("Pomodoro already running")
        self._active = True

        def _run():
            session = 0
            while self._active:
                session += 1
                time.sleep(work_min * 60)
                if not self._active:
                    break
                msg = f"🍅 Session {session} done! Take a {break_min}min break."
                log.info(msg)
                if on_notify:
                    try:
                        on_notify(msg)
                    except Exception:
                        pass
                time.sleep(break_min * 60)

        self._thread = threading.Thread(target=_run, daemon=True)
        self._thread.start()
        return _ok(f"Pomodoro started: {work_min}min work / {break_min}min break")

    def stop(self) -> Dict:
        self._active = False
        return _ok("Pomodoro stopped")


# ══════════════════════════════════════════════════════════════════════════════
# LifestyleAgent (unified facade)
# ══════════════════════════════════════════════════════════════════════════════
class LifestyleAgent:
    def __init__(self):
        self.prayer   = PrayerTimesService()
        self.crypto   = CryptoTracker()
        self.budget   = BudgetManager()
        self.reminder = ReminderService()
        self.kg       = KnowledgeGraph()
        self.journal  = IdeaJournal()
        self.pomodoro = PomodoroTimer()

    def dispatch(self, action: str, **kwargs) -> Dict:
        """Route action strings to sub-services."""
        dispatch_map = {
            "prayer_times":      lambda: self.prayer.get_times(**kwargs),
            "crypto_price":      lambda: self.crypto.get_price(**kwargs),
            "fear_greed":        lambda: self.crypto.get_fear_greed(),
            "add_expense":       lambda: self.budget.add_expense(**kwargs),
            "budget_summary":    lambda: self.budget.get_summary(**kwargs),
            "set_reminder":      lambda: self.reminder.set_reminder(**kwargs),
            "list_reminders":    lambda: self.reminder.list_reminders(),
            "add_entity":        lambda: self.kg.add_entity(**kwargs),
            "add_relation":      lambda: self.kg.add_relation(**kwargs),
            "query_entity":      lambda: self.kg.query(**kwargs),
            "search_kg":         lambda: self.kg.search(**kwargs),
            "log_idea":          lambda: self.journal.log_idea(**kwargs),
            "log_dream":         lambda: self.journal.log_dream(**kwargs),
            "list_ideas":        lambda: self.journal.list_ideas(**kwargs),
            "start_pomodoro":    lambda: self.pomodoro.start(**kwargs),
            "stop_pomodoro":     lambda: self.pomodoro.stop(),
        }
        fn = dispatch_map.get(action)
        if fn is None:
            return _err(f"Unknown action: {action!r}. Available: {list(dispatch_map.keys())}")
        try:
            return fn()
        except Exception as exc:
            return _err(f"LifestyleAgent error: {exc}")


# ── module-level singleton ────────────────────────────────────────────────────
AGENT = LifestyleAgent()


def smoke_test() -> bool:
    # KnowledgeGraph
    r = AGENT.kg.add_entity("TestUser", "person", {"test": True})
    ok = r["ok"]
    # Budget
    r2 = AGENT.budget.add_expense(100, "test chai")
    ok = ok and r2["ok"]
    # Journal
    r3 = AGENT.journal.log_idea("test idea")
    ok = ok and r3["ok"]
    log.info("LifestyleAgent smoke_test: %s", "PASS" if ok else "FAIL")
    return ok


if __name__ == "__main__":
    logging.basicConfig(level=logging.DEBUG)
    print(smoke_test())
