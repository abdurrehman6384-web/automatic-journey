"""ADB discovery + connection helpers (USB and WiFi/TCP-IP).

Resolution order for the ``adb`` binary:

1. ``$ADB_PATH`` environment variable
2. ``adb`` on ``PATH``
3. ``$ANDROID_HOME/platform-tools/adb`` or ``$ANDROID_SDK_ROOT/platform-tools/adb``
4. The binary bundled inside the ``adbutils`` wheel (works with zero setup)

Step 4 is what makes this package install-and-go on a clean machine: ``adbutils``
is a hard dependency of ``uiautomator2`` and ships a real platform-tools ``adb``.
"""

from __future__ import annotations

import os
import shutil
import subprocess
import time
from dataclasses import dataclass
from typing import List, Optional

from .errors import AdbNotFoundError, DeviceOfflineError

__all__ = ["find_adb", "adb_version", "list_devices", "AdbDevice",
           "connect_wifi", "disconnect", "enable_tcpip", "wait_for_device", "AdbRunner"]


@dataclass
class AdbDevice:
    """One row of ``adb devices -l``."""
    serial: str
    state: str                      # device | offline | unauthorized | no permissions
    model: Optional[str] = None
    product: Optional[str] = None
    transport_id: Optional[str] = None

    @property
    def is_usb(self) -> bool:
        return ":" not in self.serial

    @property
    def ready(self) -> bool:
        return self.state == "device"


def find_adb() -> str:
    """Return an absolute path to a working ``adb`` binary.

    Raises:
        AdbNotFoundError: nothing usable was found.
    """
    candidates: List[str] = []

    env_path = os.environ.get("ADB_PATH")
    if env_path:
        candidates.append(env_path)

    on_path = shutil.which("adb")
    if on_path:
        candidates.append(on_path)

    for var in ("ANDROID_HOME", "ANDROID_SDK_ROOT"):
        root = os.environ.get(var)
        if root:
            candidates.append(os.path.join(root, "platform-tools", "adb"))

    # Bundled with the adbutils wheel -- no download, no SDK install needed.
    try:
        import adbutils
        bundled = adbutils.adb_path()
        if bundled:
            candidates.append(bundled)
    except Exception:
        pass

    for cand in candidates:
        if cand and os.path.isfile(cand) and os.access(cand, os.X_OK):
            return os.path.abspath(cand)

    raise AdbNotFoundError(
        "Could not find an `adb` binary. Looked at: %s. "
        "Install platform-tools, set ADB_PATH, or `pip install adbutils`."
        % (", ".join(candidates) or "<nothing>")
    )


def adb_version(adb: Optional[str] = None) -> str:
    """First two lines of ``adb version``."""
    adb = adb or find_adb()
    out = subprocess.run([adb, "version"], capture_output=True, text=True, timeout=15)
    return (out.stdout or out.stderr).strip()


class AdbRunner:
    """Thin, testable wrapper around the ``adb`` binary."""

    def __init__(self, adb_path: Optional[str] = None):
        self.adb = adb_path or find_adb()

    def run(self, *args: str, serial: Optional[str] = None, timeout: int = 60) -> str:
        cmd = [self.adb]
        if serial:
            cmd += ["-s", serial]
        cmd += list(args)
        proc = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)
        if proc.returncode != 0:
            raise RuntimeError(
                f"`{' '.join(cmd)}` failed (exit {proc.returncode}): {(proc.stderr or proc.stdout).strip()}"
            )
        return proc.stdout.strip()

    def devices(self) -> List[AdbDevice]:
        """Parse ``adb devices -l`` into structured records."""
        raw = self.run("devices", "-l")
        result: List[AdbDevice] = []
        for line in raw.splitlines()[1:]:
            line = line.strip()
            if not line or line.startswith("*"):
                continue
            parts = line.split()
            if len(parts) < 2:
                continue
            serial, state = parts[0], parts[1]
            kv = {}
            for tok in parts[2:]:
                if ":" in tok:
                    k, _, v = tok.partition(":")
                    kv[k] = v
            result.append(AdbDevice(
                serial=serial,
                state=state,
                model=kv.get("model"),
                product=kv.get("product"),
                transport_id=kv.get("transport_id"),
            ))
        return result


def list_devices(adb: Optional[str] = None) -> List[AdbDevice]:
    """All devices adb currently knows about."""
    return AdbRunner(adb).devices()


def connect_wifi(host: str, port: int = 5555, adb: Optional[str] = None,
                 timeout: int = 15) -> str:
    """``adb connect host:port`` for wireless debugging.

    Returns the ``host:port`` serial on success.
    """
    runner = AdbRunner(adb)
    target = host if ":" in host else f"{host}:{port}"
    out = runner.run("connect", target, timeout=timeout)
    if "connected" not in out.lower():
        raise DeviceOfflineError(target, out)
    return target


def disconnect(target: str, adb: Optional[str] = None) -> str:
    return AdbRunner(adb).run("disconnect", target)


def enable_tcpip(serial: str, port: int = 5555, adb: Optional[str] = None) -> str:
    """Flip a USB-connected device into TCP/IP mode (``adb tcpip <port>``)."""
    return AdbRunner(adb).run("tcpip", str(port), serial=serial)


def wait_for_device(serial: Optional[str] = None, timeout: float = 30.0,
                    adb: Optional[str] = None) -> AdbDevice:
    """Block until a device reaches the ``device`` state."""
    runner = AdbRunner(adb)
    deadline = time.time() + timeout
    last: Optional[AdbDevice] = None
    while time.time() < deadline:
        for dev in runner.devices():
            if serial and dev.serial != serial:
                continue
            last = dev
            if dev.ready:
                return dev
        time.sleep(1.0)
    if last is not None:
        raise DeviceOfflineError(last.serial, last.state)
    raise DeviceOfflineError(serial or "<any>", "absent")
