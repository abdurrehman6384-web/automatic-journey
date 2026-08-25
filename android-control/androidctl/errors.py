"""Exception hierarchy for androidctl.

Everything the wrapper raises derives from :class:`AndroidCtlError` so callers
can do a single broad ``except`` or drill into specifics.
"""

from __future__ import annotations

from typing import Optional


class AndroidCtlError(Exception):
    """Base class for every androidctl error."""


class AdbNotFoundError(AndroidCtlError):
    """No usable ``adb`` binary could be located.

    Raised by :mod:`androidctl.adb` when neither ``$ADB_PATH``, ``PATH``,
    ``$ANDROID_HOME/platform-tools`` nor the bundled ``adbutils`` binary exists.
    """


class NoDeviceError(AndroidCtlError):
    """No Android device is reachable over ADB."""

    def __init__(self, message: Optional[str] = None, serial: Optional[str] = None):
        self.serial = serial
        super().__init__(message or "No ADB device connected. Plug in a device over USB "
                                    "or run `adb connect <ip>:<port>` for WiFi.")


class MultipleDevicesError(AndroidCtlError):
    """More than one device is connected and no serial was specified."""

    def __init__(self, serials):
        self.serials = list(serials)
        super().__init__(
            "Multiple devices connected (%s). Pass an explicit serial, e.g. "
            "connect('SERIAL') or DeviceManager().get('SERIAL')." % ", ".join(self.serials)
        )


class DeviceOfflineError(AndroidCtlError):
    """Device is listed by adb but not in the ``device`` state."""

    def __init__(self, serial: str, state: str):
        self.serial = serial
        self.state = state
        super().__init__(f"Device {serial} is '{state}', not 'device'. "
                         "Re-authorise USB debugging or re-run `adb connect`.")


class UiAutomatorError(AndroidCtlError):
    """The on-device uiautomator2 server failed to start or talk back."""


class ActionFailedError(AndroidCtlError):
    """A device action was rejected or timed out."""


class ElementNotFoundError(AndroidCtlError):
    """A selector matched nothing on screen."""

    def __init__(self, selector: str):
        self.selector = selector
        super().__init__(f"No UI element matched: {selector}")
