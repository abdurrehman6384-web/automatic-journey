"""androidctl -- deep Android device control for Python.

    from androidctl import connect, DeviceManager

    d = connect()                      # only device attached
    d = connect("R5CT30XXXXX")         # a specific one

    d.screenshot("screen.png")
    print(d.ui_text())                 # compact, LLM-friendly UI tree
    d.tap(540, 1200)
    d.swipe_direction("up")
    d.type_text("hello")
    d.launch("com.android.settings")
    print(d.shell("getprop ro.product.model").output)

    mgr = DeviceManager()              # many phones at once
    print(mgr.parallel(lambda dev: dev.current_app()))

Built on ``uiautomator2`` (no root required). See ``README.md`` for USB / WiFi
ADB setup and the MCP server.
"""

from __future__ import annotations

from .adb import (
    AdbDevice,
    adb_version,
    AdbRunner,
    connect_wifi,
    disconnect,
    enable_tcpip,
    find_adb,
    list_devices,
    wait_for_device,
)
from .device import AndroidDevice, ShellResult, connect
from .errors import (
    ActionFailedError,
    AdbNotFoundError,
    AndroidCtlError,
    DeviceOfflineError,
    ElementNotFoundError,
    MultipleDevicesError,
    NoDeviceError,
    UiAutomatorError,
)
from .hierarchy import UiNode, UiTree, compact_hierarchy, parse_hierarchy
from .manager import DeviceManager
from .agent import AgentResult, DeviceAgent, Step
from .resilience import ResilientDevice, resilient

__version__ = "1.0.0"

__all__ = [
    "__version__",
    # device
    "AndroidDevice", "ShellResult", "connect",
    # multi-device
    "DeviceManager", "ResilientDevice", "resilient",
    # agent
    "DeviceAgent", "AgentResult", "Step",
    # adb
    "AdbDevice", "AdbRunner", "find_adb", "adb_version", "list_devices", "connect_wifi",
    "disconnect", "enable_tcpip", "wait_for_device",
    # hierarchy
    "UiNode", "UiTree", "parse_hierarchy", "compact_hierarchy",
    # errors
    "AndroidCtlError", "AdbNotFoundError", "NoDeviceError", "MultipleDevicesError",
    "DeviceOfflineError", "UiAutomatorError", "ActionFailedError", "ElementNotFoundError",
]
