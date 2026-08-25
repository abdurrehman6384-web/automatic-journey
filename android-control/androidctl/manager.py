"""Multi-device orchestration.

    from androidctl import DeviceManager
    mgr = DeviceManager()
    for dev in mgr.all():
        print(dev.serial, dev.current_app())

    results = mgr.broadcast(lambda d: d.shell("getprop ro.product.model"))

    mgr.parallel(lambda d: d.screenshot(f"{d.serial}.png"))
"""

from __future__ import annotations

import logging
from concurrent.futures import ThreadPoolExecutor
from typing import Any, Callable, Dict, Iterable, List, Optional

from .adb import AdbDevice, AdbRunner, connect_wifi, list_devices
from .device import AndroidDevice
from .errors import NoDeviceError

log = logging.getLogger("androidctl.manager")

__all__ = ["DeviceManager"]


class DeviceManager:
    """Registry + connection pool for many devices.

    Connections are cached per serial so repeated calls reuse one uiautomator2
    session (starting that session is the expensive part).
    """

    def __init__(self, adb_path: Optional[str] = None):
        self._adb = AdbRunner(adb_path)
        self._pool: Dict[str, AndroidDevice] = {}

    # ------------------------------------------------------------------
    # discovery
    # ------------------------------------------------------------------
    def discover(self, ready_only: bool = True) -> List[AdbDevice]:
        devs = self._adb.devices()
        return [d for d in devs if d.ready] if ready_only else devs

    @property
    def serials(self) -> List[str]:
        return [d.serial for d in self.discover()]

    def __len__(self) -> int:
        return len(self.discover())

    # ------------------------------------------------------------------
    # connections
    # ------------------------------------------------------------------
    def connect(self, serial: Optional[str] = None, reuse: bool = True) -> AndroidDevice:
        """Connect to ``serial`` (or the only device present)."""
        from .device import connect as _connect

        if serial is None:
            ready = self.serials
            if not ready:
                raise NoDeviceError()
            if len(ready) == 1:
                serial = ready[0]
            else:
                from .errors import MultipleDevicesError
                raise MultipleDevicesError(ready)

        if reuse and serial in self._pool:
            return self._pool[serial]

        dev = _connect(serial)
        self._pool[serial] = dev
        return dev

    get = connect

    def connect_wifi(self, host: str, port: int = 5555) -> AndroidDevice:
        """Wireless debugging: ``adb connect`` then attach uiautomator2."""
        target = connect_wifi(host, port, adb=self._adb.adb)
        return self.connect(target)

    def get_or_none(self, serial: str) -> Optional[AndroidDevice]:
        try:
            return self.connect(serial)
        except Exception as exc:
            log.warning("Could not connect to %s: %s", serial, exc)
            return None

    def all(self) -> List[AndroidDevice]:
        """Every ready device, connected."""
        out = []
        for serial in self.serials:
            dev = self.get_or_none(serial)
            if dev is not None:
                out.append(dev)
        return out

    def require(self) -> AndroidDevice:
        """Exactly one ready device, or an error."""
        devs = self.all()
        if not devs:
            raise NoDeviceError()
        return devs[0]

    # ------------------------------------------------------------------
    # fan-out
    # ------------------------------------------------------------------
    def broadcast(self, fn: Callable[[AndroidDevice], Any],
                  serials: Optional[Iterable[str]] = None) -> Dict[str, Any]:
        """Run ``fn`` on each device sequentially; collect results or errors."""
        targets = list(serials) if serials else self.serials
        results: Dict[str, Any] = {}
        for serial in targets:
            try:
                results[serial] = fn(self.connect(serial))
            except Exception as exc:
                log.exception("broadcast failed on %s", serial)
                results[serial] = {"error": f"{type(exc).__name__}: {exc}"}
        return results

    def parallel(self, fn: Callable[[AndroidDevice], Any],
                 serials: Optional[Iterable[str]] = None,
                 max_workers: int = 8) -> Dict[str, Any]:
        """Same as :meth:`broadcast` but devices run concurrently.

        Each device is touched from a single worker thread, which is safe: the
        contention you care about is on the phone, not in this process.
        """
        targets = list(serials) if serials else self.serials
        results: Dict[str, Any] = {}
        if not targets:
            return results

        def _run(serial: str):
            try:
                return serial, fn(self.connect(serial))
            except Exception as exc:
                log.exception("parallel failed on %s", serial)
                return serial, {"error": f"{type(exc).__name__}: {exc}"}

        with ThreadPoolExecutor(max_workers=min(max_workers, len(targets))) as pool:
            for serial, value in pool.map(_run, targets):
                results[serial] = value
        return results

    def summary(self) -> List[Dict[str, Any]]:
        """One summary dict per connected device -- ideal for an MCP listing."""
        out = []
        for serial in self.serials:
            dev = self.get_or_none(serial)
            out.append(dev.summary() if dev else {"serial": serial, "error": "unreachable"})
        return out

    def disconnect(self, serial: Optional[str] = None) -> None:
        if serial:
            self._pool.pop(serial, None)
        else:
            self._pool.clear()
