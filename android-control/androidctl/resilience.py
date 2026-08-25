"""Reconnect-and-retry wrapper.

The uiautomator2 server on the phone dies for ordinary reasons: the screen
locks, the app is swiped away, the phone reboots, WiFi ADB power-saves. A long
agent run *will* hit this, so recovery has to be structural rather than a
try/except scattered through the caller.

    from androidctl.resilience import resilient

    d = resilient(mgr, "R5CT30ABCD")
    d.tap(540, 1200)          # transparently reconnects + retries on a dead session

Only the errors that a reconnect can actually fix are retried. A genuine
programming error (``TypeError``, ``ElementNotFoundError``) fails immediately --
silently retrying those just hides bugs.
"""

from __future__ import annotations

import functools
import logging
import time
from typing import Any, Callable, Iterable, Optional, Tuple, Type

log = logging.getLogger("androidctl.resilience")

__all__ = ["RETRYABLE", "retryable_errors", "resilient", "ResilientDevice",
           "with_reconnect"]


def retryable_errors() -> Tuple[Type[BaseException], ...]:
    """Session-level failures worth one reconnect.

    Resolved dynamically: the exact exception set differs between uiautomator2
    versions, and adbutils/lamda add their own. Anything unavailable is skipped
    rather than guessed at.
    """
    names = [
        ("uiautomator2", "SessionBrokenError"),
        ("uiautomator2", "UiAutomationError"),
        ("uiautomator2", "UiAutomationNotConnectedError"),
        ("uiautomator2", "LaunchUiAutomationError"),
        ("uiautomator2", "RPCError"),
        ("uiautomator2", "HTTPError"),
        ("uiautomator2", "HTTPTimeoutError"),
        ("uiautomator2", "HierarchyEmptyError"),
        ("uiautomator2", "DeviceError"),
        ("adbutils", "AdbError"),
        ("adbutils", "AdbTimeout"),
        ("lamda.exceptions", "UnHandledException"),
    ]
    found = []
    for module, attr in names:
        try:
            mod = __import__(module, fromlist=[attr])
            exc = getattr(mod, attr, None)
            if isinstance(exc, type) and issubclass(exc, BaseException):
                found.append(exc)
        except Exception:
            continue

    # Always include the transport basics, whatever else resolved.
    found += [ConnectionError, TimeoutError, OSError]

    # de-dup, keep it a tuple
    unique: list = []
    for exc in found:
        if exc not in unique:
            unique.append(exc)
    return tuple(unique)


#: Snapshot taken at import time; call :func:`retryable_errors` for a fresh one.
RETRYABLE: Tuple[Type[BaseException], ...] = retryable_errors()


def with_reconnect(reconnect: Callable[[], Any],
                   attempts: int = 3,
                   delay: float = 1.0,
                   backoff: float = 2.0,
                   retry_on: Optional[Iterable[Type[BaseException]]] = None) -> Callable:
    """Decorator: on a retryable failure, ``reconnect()`` and try again.

    ``reconnect`` receives no arguments and must return the fresh object the
    wrapped function should be re-bound to (via ``self._device``).
    """
    errors = tuple(retry_on) if retry_on else RETRYABLE

    def decorator(fn: Callable) -> Callable:
        @functools.wraps(fn)
        def wrapper(self, *args, **kwargs):
            wait = delay
            last: Optional[BaseException] = None
            for attempt in range(1, attempts + 1):
                try:
                    return fn(self, *args, **kwargs)
                except errors as exc:
                    last = exc
                    if attempt == attempts:
                        break
                    log.warning("%s failed (%s: %s) -- reconnecting, attempt %d/%d",
                                fn.__name__, type(exc).__name__, exc, attempt, attempts)
                    try:
                        reconnect_target = reconnect()
                        if reconnect_target is not None:
                            self._device = reconnect_target
                    except Exception as reconn_exc:
                        log.error("reconnect failed: %s", reconn_exc)
                    time.sleep(wait)
                    wait *= backoff
            assert last is not None
            raise last
        return wrapper
    return decorator


class ResilientDevice:
    """Wraps a ``DeviceManager`` + serial, reconnecting when the session dies.

    Attribute access is forwarded to the live device, so it is a drop-in for
    :class:`androidctl.AndroidDevice`. Each forwarded call is retried.
    """

    #: Methods that are safe to retry. Read-only or idempotent-by-intent; a
    #: blind retry of ``tap`` could double-fire, so taps are retried only when
    #: the session was demonstrably dead (which is what the error means).
    _FORWARDED_RETRYABLE = True

    def __init__(self, manager: Any, serial: Optional[str] = None,
                 attempts: int = 3, delay: float = 1.0, backoff: float = 2.0,
                 retry_on: Optional[Iterable[Type[BaseException]]] = None):
        self._manager = manager
        self._serial = serial
        self._device = None
        self._attempts = attempts
        self._delay = delay
        self._backoff = backoff
        self._errors = tuple(retry_on) if retry_on else RETRYABLE
        self.reconnect_count = 0

    # -- connection -----------------------------------------------------
    def _reconnect(self):
        self._manager.disconnect(self._serial)
        dev = self._manager.connect(self._serial)
        self._serial = dev.serial
        self.reconnect_count += 1
        log.info("reconnected to %s (total reconnects: %d)",
                 self._serial, self.reconnect_count)
        return dev

    @property
    def device(self):
        if self._device is None:
            self._device = self._manager.connect(self._serial)
            self._serial = self._device.serial
        return self._device

    @property
    def serial(self) -> Optional[str]:
        return self._serial

    def reset(self) -> None:
        self._device = None

    # -- proxying -------------------------------------------------------
    def __getattr__(self, name: str) -> Any:
        attr = getattr(self.device, name)
        if not callable(attr):
            return attr

        @functools.wraps(attr)
        def call(*args, **kwargs):
            wait = self._delay
            last: Optional[BaseException] = None
            for attempt in range(1, self._attempts + 1):
                try:
                    return getattr(self.device, name)(*args, **kwargs)
                except self._errors as exc:
                    last = exc
                    if attempt == self._attempts:
                        break
                    log.warning("%s failed (%s) -- reconnect %d/%d",
                                name, type(exc).__name__, attempt, self._attempts)
                    try:
                        self._reconnect()
                    except Exception as reconn_exc:
                        log.error("reconnect failed: %s", reconn_exc)
                    time.sleep(wait)
                    wait *= self._backoff
            assert last is not None
            raise last
        return call

    def __repr__(self) -> str:
        return (f"<ResilientDevice {self._serial or 'auto'} "
                f"reconnects={self.reconnect_count}>")


def resilient(manager: Any, serial: Optional[str] = None, **kwargs) -> ResilientDevice:
    """Convenience constructor for :class:`ResilientDevice`."""
    return ResilientDevice(manager, serial, **kwargs)
