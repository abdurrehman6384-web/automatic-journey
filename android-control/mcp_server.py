#!/usr/bin/env python3
"""MCP server exposing full Android device control to Claude / Cursor / etc.

Run it:

    python mcp_server.py                 # stdio transport (default)
    python mcp_server.py --list          # smoke-test: print tools and exit

Client config (Claude Desktop / Cursor) lives in ``examples/mcp_config.json``.

Tools are grouped by verb so an agent can plan: ``android_screen_state`` returns
the screenshot + a compact indexed UI tree in one call, which is the standard
"look, then act" step. Every tool takes an optional ``serial`` so a single
server can drive several phones at once.
"""

from __future__ import annotations

import argparse
import json
import logging
import os
import sys
from typing import Any, Dict, List, Optional

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from mcp.server.mcpserver import Image, MCPServer  # noqa: E402

from androidctl import DeviceManager  # noqa: E402
from androidctl.device import AndroidDevice  # noqa: E402
from androidctl.errors import AndroidCtlError  # noqa: E402

log = logging.getLogger("androidctl.mcp")

mcp = MCPServer(
    name="android-control",
    title="Android Device Control",
    version="1.0.0",
    instructions=(
        "Controls real Android devices over ADB (no root required).\n"
        "Typical loop: android_screen_state -> read the indexed UI tree -> "
        "android_tap_element / android_swipe / android_type_text -> repeat.\n"
        "Call android_list_devices first. Pass `serial` to every tool when more "
        "than one device is connected.\n"
        "Prefer android_tap_element(node_id) over raw coordinates: ids come from "
        "the UI tree and are exact."
    ),
)

_manager = DeviceManager()


# ---------------------------------------------------------------------------
# helpers
# ---------------------------------------------------------------------------
def _device(serial: Optional[str]) -> AndroidDevice:
    return _manager.connect(serial)


def _err(exc: Exception) -> Dict[str, Any]:
    """Uniform error shape so the model can recover instead of guessing."""
    return {
        "ok": False,
        "error": f"{type(exc).__name__}: {exc}",
        "hint": _hint_for(exc),
    }


def _hint_for(exc: Exception) -> str:
    name = type(exc).__name__
    hints = {
        "NoDeviceError": "Run `adb devices`. Enable USB debugging, or `adb connect <ip>:5555` for WiFi.",
        "MultipleDevicesError": "More than one phone is attached -- pass `serial` explicitly.",
        "DeviceOfflineError": "Accept the RSA fingerprint prompt on the phone, then retry.",
        "AdbNotFoundError": "adb not found: set ADB_PATH or `pip install adbutils`.",
        "ElementNotFoundError": "Nothing matched. Re-read the screen with android_screen_state first.",
        "UiObjectNotFoundError": "Element vanished (screen changed). Re-read with android_screen_state.",
    }
    return hints.get(name, "Retry once; if it persists, re-read the screen state.")


# ---------------------------------------------------------------------------
# discovery
# ---------------------------------------------------------------------------
@mcp.tool(description="List every Android device adb can see, with state and model.")
def android_list_devices() -> Dict[str, Any]:
    try:
        devs = _manager.discover(ready_only=False)
        return {
            "ok": True,
            "count": len(devs),
            "devices": [
                {
                    "serial": d.serial,
                    "state": d.state,
                    "model": d.model,
                    "product": d.product,
                    "transport": "usb" if d.is_usb else "wifi",
                    "ready": d.ready,
                }
                for d in devs
            ],
        }
    except Exception as exc:
        return _err(exc)


@mcp.tool(description="Connected-device details: model, Android version, screen size, battery.")
def android_device_info(serial: Optional[str] = None) -> Dict[str, Any]:
    try:
        return {"ok": True, "devices": _manager.summary() if serial is None
                else [_device(serial).summary()]}
    except Exception as exc:
        return _err(exc)


@mcp.tool(description="Wireless debugging: `adb connect host:port`, then attach. Returns the serial to reuse.")
def android_connect_wifi(host: str, port: int = 5555) -> Dict[str, Any]:
    try:
        dev = _manager.connect_wifi(host, port)
        return {"ok": True, "serial": dev.serial}
    except Exception as exc:
        return _err(exc)


# ---------------------------------------------------------------------------
# perception
# ---------------------------------------------------------------------------
@mcp.tool(description=(
    "The standard look step: screenshot + compact indexed UI tree + current app. "
    "Use the [id] values with android_tap_element."))
def android_screen_state(serial: Optional[str] = None, max_nodes: int = 250) -> Dict[str, Any]:
    try:
        d = _device(serial)
        state = d.screen_state(max_nodes=max_nodes)
        return {"ok": True, **state}
    except Exception as exc:
        return _err(exc)


@mcp.tool(description="Screenshot as a PNG image.")
def android_screenshot(serial: Optional[str] = None) -> Any:
    d = _device(serial)
    return Image(data=d.screenshot_bytes(), format="png")


@mcp.tool(description="Save a screenshot to a local file. Returns the absolute path.")
def android_screenshot_to_file(path: str, serial: Optional[str] = None) -> Dict[str, Any]:
    try:
        _device(serial).screenshot(path)
        return {"ok": True, "path": os.path.abspath(path)}
    except Exception as exc:
        return _err(exc)


@mcp.tool(description="Compact, LLM-friendly UI tree with [id] indexes and tap centres.")
def android_ui_tree(serial: Optional[str] = None, include_all: bool = False,
                    max_nodes: int = 400) -> Dict[str, Any]:
    try:
        tree = _device(serial).ui_tree()
        return {
            "ok": True,
            "package": tree.package,
            "activity": tree.activity,
            "node_count": len(tree.nodes),
            "tree": tree.to_text(include_all=include_all, max_nodes=max_nodes),
        }
    except Exception as exc:
        return _err(exc)


@mcp.tool(description="Search the current screen for elements by text / resource-id / content-desc.")
def android_find_element(serial: Optional[str] = None, text: Optional[str] = None,
                         resource_id: Optional[str] = None,
                         content_desc: Optional[str] = None,
                         clickable_only: bool = False) -> Dict[str, Any]:
    try:
        tree = _device(serial).ui_tree()
        hits = tree.find(text=text, resource_id=resource_id, content_desc=content_desc,
                         clickable=True if clickable_only else None)
        return {
            "ok": True,
            "count": len(hits),
            "elements": [
                {"id": n.node_id, "class": n.short_class, "label": n.label,
                 "resource_id": n.short_id, "center": list(n.center),
                 "clickable": n.clickable, "enabled": n.enabled}
                for n in hits[:50]
            ],
        }
    except Exception as exc:
        return _err(exc)


@mcp.tool(description="Current foreground app: package, activity, pid.")
def android_current_app(serial: Optional[str] = None) -> Dict[str, Any]:
    try:
        return {"ok": True, **_device(serial).current_app()}
    except Exception as exc:
        return _err(exc)


# ---------------------------------------------------------------------------
# actions
# ---------------------------------------------------------------------------
@mcp.tool(description="Tap absolute pixel coordinates.")
def android_tap(x: int, y: int, serial: Optional[str] = None) -> Dict[str, Any]:
    try:
        _device(serial).tap(x, y)
        return {"ok": True, "action": "tap", "x": x, "y": y}
    except Exception as exc:
        return _err(exc)


@mcp.tool(description="Tap the centre of a UI element by the [id] from android_ui_tree / android_screen_state.")
def android_tap_element(node_id: int, serial: Optional[str] = None) -> Dict[str, Any]:
    try:
        node = _device(serial).tap_element(node_id)
        return {"ok": True, "action": "tap_element", "node_id": node_id,
                "label": node.label, "center": list(node.center)}
    except Exception as exc:
        return _err(exc)


@mcp.tool(description="Tap a text label or resource-id on screen. Waits up to `timeout` seconds.")
def android_tap_text(text: Optional[str] = None, resource_id: Optional[str] = None,
                     serial: Optional[str] = None, timeout: float = 5.0) -> Dict[str, Any]:
    try:
        d = _device(serial)
        node = d.wait_for(text=text, resource_id=resource_id, timeout=timeout)
        d.tap(*node.center)
        return {"ok": True, "action": "tap_text", "label": node.label,
                "center": list(node.center)}
    except Exception as exc:
        return _err(exc)


@mcp.tool(description="Long-press at coordinates.")
def android_long_press(x: int, y: int, duration: float = 0.8,
                       serial: Optional[str] = None) -> Dict[str, Any]:
    try:
        _device(serial).long_press(x, y, duration)
        return {"ok": True, "action": "long_press", "x": x, "y": y}
    except Exception as exc:
        return _err(exc)


@mcp.tool(description="Swipe between two points.")
def android_swipe(x1: int, y1: int, x2: int, y2: int, duration: float = 0.3,
                  serial: Optional[str] = None) -> Dict[str, Any]:
    try:
        _device(serial).swipe(x1, y1, x2, y2, duration)
        return {"ok": True, "action": "swipe", "from": [x1, y1], "to": [x2, y2]}
    except Exception as exc:
        return _err(exc)


@mcp.tool(description="Swipe/scroll from screen centre: up, down, left or right.")
def android_scroll(direction: str = "up", serial: Optional[str] = None,
                   scale: float = 0.6) -> Dict[str, Any]:
    try:
        _device(serial).swipe_direction(direction, scale=scale)
        return {"ok": True, "action": "scroll", "direction": direction}
    except Exception as exc:
        return _err(exc)


@mcp.tool(description="Type text into the focused field. Set clear=true to replace existing text.")
def android_type_text(text: str, clear: bool = False,
                      serial: Optional[str] = None) -> Dict[str, Any]:
    try:
        _device(serial).type_text(text, clear=clear)
        return {"ok": True, "action": "type_text", "length": len(text)}
    except Exception as exc:
        return _err(exc)


@mcp.tool(description="Press a hardware/system key: home, back, enter, recent, volume_up, volume_down, power.")
def android_press_key(key: str, serial: Optional[str] = None) -> Dict[str, Any]:
    try:
        _device(serial).press(key)
        return {"ok": True, "action": "press_key", "key": key}
    except Exception as exc:
        return _err(exc)


@mcp.tool(description="Wait until an element appears, then return it. Raises on timeout.")
def android_wait_for(text: Optional[str] = None, resource_id: Optional[str] = None,
                     content_desc: Optional[str] = None, timeout: float = 10.0,
                     serial: Optional[str] = None) -> Dict[str, Any]:
    try:
        node = _device(serial).wait_for(text=text, resource_id=resource_id,
                                        content_desc=content_desc, timeout=timeout)
        return {"ok": True, "id": node.node_id, "label": node.label,
                "center": list(node.center)}
    except Exception as exc:
        return _err(exc)


# ---------------------------------------------------------------------------
# apps + shell
# ---------------------------------------------------------------------------
@mcp.tool(description="Launch an app by package name (e.g. com.android.settings). Waits for foreground.")
def android_launch_app(package: str, activity: Optional[str] = None,
                       stop_first: bool = False, serial: Optional[str] = None) -> Dict[str, Any]:
    try:
        return {"ok": True, **_device(serial).launch(package, activity=activity,
                                                     stop_first=stop_first)}
    except Exception as exc:
        return _err(exc)


@mcp.tool(description="Force-stop an app.")
def android_stop_app(package: str, serial: Optional[str] = None) -> Dict[str, Any]:
    try:
        _device(serial).stop(package)
        return {"ok": True, "stopped": package}
    except Exception as exc:
        return _err(exc)


@mcp.tool(description="Installed apps. third_party_only=false also lists system apps.")
def android_list_apps(third_party_only: bool = True,
                      serial: Optional[str] = None) -> Dict[str, Any]:
    try:
        apps = _device(serial).list_apps(third_party_only=third_party_only)
        return {"ok": True, "count": len(apps), "packages": apps}
    except Exception as exc:
        return _err(exc)


@mcp.tool(description="Open a URL / deep link in the default handler.")
def android_open_url(url: str, serial: Optional[str] = None) -> Dict[str, Any]:
    try:
        _device(serial).open_url(url)
        return {"ok": True, "url": url}
    except Exception as exc:
        return _err(exc)


@mcp.tool(description=(
    "Run an `adb shell` command. Non-root: useful for getprop, dumpsys, pm list, "
    "am start, input keyevent, screencap. Returns stdout and exit_code."))
def android_shell(command: str, timeout: int = 60,
                  serial: Optional[str] = None) -> Dict[str, Any]:
    try:
        res = _device(serial).shell(command, timeout=timeout)
        return {"ok": res.ok, "exit_code": res.exit_code, "output": res.output[:20000]}
    except Exception as exc:
        return _err(exc)


@mcp.tool(description="Screen on/off + lock state, via dumpsys.")
def android_wake(serial: Optional[str] = None) -> Dict[str, Any]:
    try:
        d = _device(serial)
        d.wake()
        return {"ok": True, "display_on": d.display_on}
    except Exception as exc:
        return _err(exc)


# ---------------------------------------------------------------------------
# entry point
# ---------------------------------------------------------------------------
def main() -> int:
    parser = argparse.ArgumentParser(description="androidctl MCP server")
    parser.add_argument("--list", action="store_true",
                        help="print registered tools and exit (smoke test)")
    parser.add_argument("--transport", default="stdio",
                        choices=["stdio", "sse", "streamable-http"])
    parser.add_argument("--verbose", action="store_true")
    args = parser.parse_args()

    logging.basicConfig(
        level=logging.DEBUG if args.verbose else logging.WARNING,
        # stdout is the MCP wire -- logs must never touch it
        stream=sys.stderr,
    )

    if args.list:
        tools = mcp._tool_manager.list_tools() if hasattr(mcp, "_tool_manager") else []
        print(json.dumps({"server": "android-control",
                          "tool_count": len(tools),
                          "tools": sorted(t.name for t in tools)}, indent=2))
        return 0

    mcp.run(args.transport)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
