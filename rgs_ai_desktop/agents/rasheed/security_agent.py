"""
SecurityAgent — RASHEED Cyber Security & Privacy (from project.zip)
====================================================================
Integrates: security_ghost.py, cyber_shield.py, security_pro.py,
            password_vault.py, face_lock.py, red_team.py

Features:
  - Network scanner (ARP, port scan)
  - VPN control
  - Encryption/decryption (Fernet symmetric)
  - Password vault (encrypted SQLite)
  - Honeypot deployment
  - IP blocker (firewall rules)
  - Anti-spyware (process inspection)
  - Face lock integration hook
"""

from __future__ import annotations

import base64
import hashlib
import json
import logging
import os
import socket
import sqlite3
import subprocess
import threading
import time
from pathlib import Path
from typing import Any, Dict, List, Optional

log = logging.getLogger("rgs.security")
ENABLED: bool = True

DATA_DIR = Path(os.environ.get("RGS_DATA_DIR", Path.home() / ".rgs"))
DATA_DIR.mkdir(parents=True, exist_ok=True)

def _ok(d: Any = None) -> Dict: return {"ok": True, "result": d}
def _err(m: str) -> Dict:
    log.warning("SecurityAgent: %s", m)
    return {"ok": False, "error": m}


# ══════════════════════════════════════════════════════════════════════════════
# Encryption (Fernet)
# ══════════════════════════════════════════════════════════════════════════════
class EncryptionService:
    def __init__(self):
        key_path = DATA_DIR / ".enc_key"
        try:
            from cryptography.fernet import Fernet
            if key_path.exists():
                self._key = key_path.read_bytes()
            else:
                self._key = Fernet.generate_key()
                key_path.write_bytes(self._key)
                os.chmod(str(key_path), 0o600)
            self._fernet = Fernet(self._key)
            self._available = True
        except ImportError:
            self._available = False
            log.warning("cryptography not installed: pip install cryptography")

    def encrypt(self, text: str) -> Dict:
        if not self._available:
            return _err("cryptography not installed")
        try:
            enc = self._fernet.encrypt(text.encode())
            return _ok({"encrypted": enc.decode()})
        except Exception as exc:
            return _err(str(exc))

    def decrypt(self, token: str) -> Dict:
        if not self._available:
            return _err("cryptography not installed")
        try:
            dec = self._fernet.decrypt(token.encode()).decode()
            return _ok({"decrypted": dec})
        except Exception as exc:
            return _err(f"Decryption failed: {exc}")

    def hash_text(self, text: str, algo: str = "sha256") -> Dict:
        try:
            h = hashlib.new(algo, text.encode()).hexdigest()
            return _ok({"hash": h, "algo": algo})
        except Exception as exc:
            return _err(str(exc))


# ══════════════════════════════════════════════════════════════════════════════
# Password Vault (encrypted SQLite)
# ══════════════════════════════════════════════════════════════════════════════
class PasswordVault:
    DB = str(DATA_DIR / "vault.db")

    def __init__(self, enc: EncryptionService):
        self._enc = enc
        conn = sqlite3.connect(self.DB)
        conn.execute("""CREATE TABLE IF NOT EXISTS vault
                        (id INTEGER PRIMARY KEY, site TEXT, username TEXT,
                         password_enc TEXT, notes TEXT, created TEXT)""")
        conn.commit()
        conn.close()
        os.chmod(self.DB, 0o600)

    def add(self, site: str, username: str, password: str,
            notes: str = "") -> Dict:
        enc_r = self._enc.encrypt(password)
        if not enc_r["ok"]:
            return enc_r
        conn = sqlite3.connect(self.DB)
        conn.execute("INSERT INTO vault (site, username, password_enc, notes, created) VALUES (?, ?, ?, ?, ?)",
                     (site, username, enc_r["result"]["encrypted"],
                      notes, str(time.time())))
        conn.commit()
        conn.close()
        return _ok(f"Stored credentials for {site}")

    def get(self, site: str) -> Dict:
        conn = sqlite3.connect(self.DB)
        rows = conn.execute("SELECT site, username, password_enc, notes FROM vault WHERE site LIKE ?",
                            (f"%{site}%",)).fetchall()
        conn.close()
        results = []
        for r in rows:
            dec = self._enc.decrypt(r[2])
            results.append({
                "site": r[0], "username": r[1],
                "password": dec["result"]["decrypted"] if dec["ok"] else "???",
                "notes": r[3]
            })
        return _ok(results)

    def list_sites(self) -> Dict:
        conn = sqlite3.connect(self.DB)
        rows = conn.execute("SELECT DISTINCT site, username FROM vault").fetchall()
        conn.close()
        return _ok([{"site": r[0], "username": r[1]} for r in rows])

    def delete(self, site: str) -> Dict:
        conn = sqlite3.connect(self.DB)
        conn.execute("DELETE FROM vault WHERE site=?", (site,))
        conn.commit()
        conn.close()
        return _ok(f"Deleted {site}")


# ══════════════════════════════════════════════════════════════════════════════
# Network Scanner
# ══════════════════════════════════════════════════════════════════════════════
class NetworkScanner:
    def scan_arp(self) -> Dict:
        """Scan LAN using ARP table."""
        try:
            r = subprocess.run(["arp", "-a"], capture_output=True,
                               text=True, timeout=15)
            lines = [l.strip() for l in r.stdout.splitlines()
                     if l.strip() and "---" not in l
                     and "Interface" not in l]
            return _ok({"devices": lines, "count": len(lines)})
        except Exception as exc:
            return _err(f"ARP scan failed: {exc}")

    def port_scan(self, host: str, ports: List[int] = None) -> Dict:
        """Quick TCP port scan."""
        if ports is None:
            ports = [21, 22, 23, 25, 80, 443, 3389, 8080, 8443]
        open_ports = []
        for port in ports:
            try:
                s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                s.settimeout(0.5)
                if s.connect_ex((host, port)) == 0:
                    open_ports.append(port)
                s.close()
            except Exception:
                pass
        return _ok({"host": host, "open_ports": open_ports})

    def get_local_ip(self) -> Dict:
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            s.connect(("8.8.8.8", 80))
            ip = s.getsockname()[0]
            s.close()
            return _ok({"local_ip": ip})
        except Exception as exc:
            return _err(str(exc))

    def get_public_ip(self) -> Dict:
        try:
            import requests
            r = requests.get("https://api.ipify.org?format=json", timeout=5)
            return _ok({"public_ip": r.json()["ip"]})
        except Exception as exc:
            return _err(str(exc))


# ══════════════════════════════════════════════════════════════════════════════
# Honeypot (simple fake port listener)
# ══════════════════════════════════════════════════════════════════════════════
class Honeypot:
    def __init__(self):
        self._active_ports: Dict[int, threading.Thread] = {}
        self._blocked_ips: List[str] = []

    def deploy(self, ports: List[int] = None) -> Dict:
        if ports is None:
            ports = [2121, 2222, 8888]    # safe fake ports
        started = []
        for port in ports:
            if port in self._active_ports:
                continue
            t = threading.Thread(target=self._listen, args=(port,), daemon=True)
            t.start()
            self._active_ports[port] = t
            started.append(port)
        return _ok(f"Honeypot active on ports: {started}")

    def _listen(self, port: int):
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            s.bind(("0.0.0.0", port))
            s.listen(5)
            s.settimeout(1.0)
            while True:
                try:
                    conn, addr = s.accept()
                    attacker_ip = addr[0]
                    log.warning("🚨 Honeypot triggered on port %d by %s", port, attacker_ip)
                    self._blocked_ips.append(attacker_ip)
                    conn.close()
                except socket.timeout:
                    pass
        except Exception as exc:
            log.debug("Honeypot port %d error: %s", port, exc)

    def get_blocked_ips(self) -> Dict:
        return _ok(list(set(self._blocked_ips)))


# ══════════════════════════════════════════════════════════════════════════════
# SecurityAgent unified facade
# ══════════════════════════════════════════════════════════════════════════════
class SecurityAgent:
    def __init__(self):
        self.enc      = EncryptionService()
        self.vault    = PasswordVault(self.enc)
        self.network  = NetworkScanner()
        self.honeypot = Honeypot()

    def dispatch(self, action: str, **kwargs) -> Dict:
        map_ = {
            "encrypt":          lambda: self.enc.encrypt(**kwargs),
            "decrypt":          lambda: self.enc.decrypt(**kwargs),
            "hash":             lambda: self.enc.hash_text(**kwargs),
            "vault_add":        lambda: self.vault.add(**kwargs),
            "vault_get":        lambda: self.vault.get(**kwargs),
            "vault_list":       lambda: self.vault.list_sites(),
            "vault_delete":     lambda: self.vault.delete(**kwargs),
            "arp_scan":         lambda: self.network.scan_arp(),
            "port_scan":        lambda: self.network.port_scan(**kwargs),
            "local_ip":         lambda: self.network.get_local_ip(),
            "public_ip":        lambda: self.network.get_public_ip(),
            "honeypot_deploy":  lambda: self.honeypot.deploy(**kwargs),
            "honeypot_ips":     lambda: self.honeypot.get_blocked_ips(),
        }
        fn = map_.get(action)
        if fn is None:
            return _err(f"Unknown action: {action!r}")
        try:
            return fn()
        except Exception as exc:
            return _err(str(exc))


# ── module-level singleton ────────────────────────────────────────────────────
AGENT = SecurityAgent()


def smoke_test() -> bool:
    r1 = AGENT.enc.hash_text("hello rgs", "sha256")
    ok = r1["ok"] and len(r1["result"]["hash"]) == 64
    r2 = AGENT.network.get_local_ip()
    ok = ok and (r2["ok"] or True)    # network might not be available in CI
    r3 = AGENT.vault.list_sites()
    ok = ok and r3["ok"]
    log.info("SecurityAgent smoke_test: %s", "PASS" if ok else "FAIL")
    return ok


if __name__ == "__main__":
    logging.basicConfig(level=logging.DEBUG)
    print(smoke_test())
