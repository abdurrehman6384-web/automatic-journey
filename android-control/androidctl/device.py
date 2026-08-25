"""High-level single-device control surface.

    from androidctl import connect
    d = connect()                 # or connect("SERIAL")
    d.screenshot("shot.png")
    print(d.ui_tree().to_text())
    d.tap(540, 1200)
    d.shell("dumpsys battery")

The wrapper is intentionally duck-typed over ``uiautomator2.Device``: it only
uses ``click / swipe / send_keys / screenshot / dump_hierarchy / shell /
app_* / press / window_size / device_info``. That keeps it unit-testable with a
stub transport and makes swapping the backend (u2 -> lamda -> raw adb) a
one-class change.
"""

from __future__ import annotations

import base64
import io
import os
import time
from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Tuple, Union

from .errors import ActionFailedError, ElementNotFoundError
from .hierarchy import UiNode, UiTree, parse_hierarchy

__all__ = ["AndroidDevice", "ShellResult", "connect"]

Coord = Union[int, float]


@dataclass
class ShellResult:
    """Result of :meth:`AndroidDevice.shell`."""
    output: str
    exit_code: int

    @property
    def ok(self) -> bool:
        return self.exit_code == 0

    def __str__(self) -> str:
        return self.output


class AndroidDevice:
    """One connected Android device."""

    def __init__(self, u2device: Any, serial: Optional[str] = None):
        self._d = u2device
        self.serial = serial or getattr(u2device, "serial", None) or "unknown"
        self._size_cache: Optional[Tuple[int, int]] = None

    def __repr__(self) -> str:
        return f"<AndroidDevice {self.serial}>"

    # ------------------------------------------------------------------
    # introspection
    # ------------------------------------------------------------------
    @property
    def info(self) -> Dict[str, Any]:
        """Raw ``device_info`` dict from the on-device server."""
        return dict(self._d.device_info)

    @property
    def window_size(self) -> Tuple[int, int]:
        if self._size_cache is None:
            w, h = self._d.window_size()
            self._size_cache = (int(w), int(h))
        return self._size_cache

    @property
    def display_on(self) -> bool:
        return self.shell("dumpsys power").output.count("mWakefulness=Awake") > 0

    def summary(self) -> Dict[str, Any]:
        """Small dict describing the device -- good for logs and MCP listings."""
        info = {}
        error = None
        try:
            info = self.info
        except Exception as exc:              # device_info needs the u2 server up
            error = f"{type(exc).__name__}: {exc}"
        w, h = 0, 0
        try:
            w, h = self.window_size
        except Exception as exc:
            error = error or f"{type(exc).__name__}: {exc}"
        out = {
            "serial": self.serial,
            "width": w,
            "height": h,
            "brand": info.get("brand"),
            "model": info.get("model"),
            "android_version": info.get("version"),
            "sdk": info.get("sdk"),
            "battery": info.get("battery"),
            "display": info.get("display"),
        }
        if error:
            # Surface it -- a silently all-None summary is worse than an error.
            out["error"] = error
        return out

    # ------------------------------------------------------------------
    # screen capture
    # ------------------------------------------------------------------
    def screenshot(self, path: Optional[str] = None):
        """Capture the screen.

        Returns a ``PIL.Image``. If ``path`` is given the PNG is also written
        there (parent directories are created).
        """
        img = self._d.screenshot()
        if path:
            parent = os.path.dirname(os.path.abspath(path))
            os.makedirs(parent, exist_ok=True)
            img.save(path)
        return img

    def screenshot_bytes(self, fmt: str = "PNG") -> bytes:
        buf = io.BytesIO()
        self.screenshot().save(buf, format=fmt)
        return buf.getvalue()

    def screenshot_b64(self, fmt: str = "PNG") -> str:
        """Base64 PNG -- what you hand a vision model."""
        return base64.b64encode(self.screenshot_bytes(fmt)).decode("ascii")

    # ------------------------------------------------------------------
    # UI hierarchy
    # ------------------------------------------------------------------
    def ui_tree(self, compressed: bool = False, pretty: bool = False) -> UiTree:
        """Dump + parse the accessibility hierarchy into a :class:`UiTree`."""
        xml = self._d.dump_hierarchy(compressed=compressed, pretty=pretty)
        pkg = act = ""
        try:
            cur = self._d.app_current() or {}
            pkg, act = cur.get("package", ""), cur.get("activity", "")
        except Exception:
            pass
        return parse_hierarchy(xml, package=pkg, activity=act)

    def ui_text(self, include_all: bool = False, max_nodes: int = 400) -> str:
        """Compact text tree for LLM consumption (cheap on tokens)."""
        return self.ui_tree().to_text(include_all=include_all, max_nodes=max_nodes)

    def ui_dump(self, compressed: bool = False) -> str:
        """The raw XML, when you need everything."""
        return self._d.dump_hierarchy(compressed=compressed)

    def screen_state(self, max_nodes: int = 250) -> Dict[str, Any]:
        """Screenshot + compact tree in one shot -- the standard agent step."""
        tree = self.ui_tree()
        return {
            "serial": self.serial,
            "app": {"package": tree.package, "activity": tree.activity},
            "window_size": self.window_size,
            "ui_tree": tree.to_text(max_nodes=max_nodes),
            "screenshot_png_b64": self.screenshot_b64(),
        }

    # ------------------------------------------------------------------
    # input
    # ------------------------------------------------------------------
    def tap(self, x: Coord, y: Coord) -> None:
        """Tap absolute pixel coordinates.

        ``uiautomator2`` names this ``click``; ``tap`` is kept because it is the
        verb everybody reaches for, and it is what the public API promises.
        """
        self._d.click(x, y)

    click = tap  # alias, so both spellings work

    def tap_element(self, node_id_or_node: Union[int, UiNode],
                    offset: Tuple[int, int] = (0, 0)) -> UiNode:
        """Tap the centre of a node from :meth:`ui_tree`."""
        node = node_id_or_node if isinstance(node_id_or_node, UiNode) \
            else self.ui_tree().get(int(node_id_or_node))
        cx, cy = node.center
        self.tap(cx + offset[0], cy + offset[1])
        return node

    def tap_percent(self, px: float, py: float) -> None:
        """Tap using 0.0-1.0 fractions of the screen (resolution independent)."""
        w, h = self.window_size
        self.tap(int(w * px), int(h * py))

    def long_press(self, x: Coord, y: Coord, duration: float = 0.8) -> None:
        self._d.long_click(x, y, duration=duration)

    def swipe(self, x1: Coord, y1: Coord, x2: Coord, y2: Coord,
              duration: float = 0.3) -> None:
        self._d.swipe(x1, y1, x2, y2, duration=duration)

    def swipe_direction(self, direction: str = "up", scale: float = 0.6,
                        duration: float = 0.3) -> None:
        """Swipe from screen centre. ``up`` scrolls content down, and so on."""
        w, h = self.window_size
        cx, cy = w // 2, h // 2
        dx = int(w * scale / 2)
        dy = int(h * scale / 2)
        table = {
            "up":    (cx, cy + dy, cx, cy - dy),
            "down":  (cx, cy - dy, cx, cy + dy),
            "left":  (cx + dx, cy, cx - dx, cy),
            "right": (cx - dx, cy, cx + dx, cy),
        }
        if direction not in table:
            raise ActionFailedError(f"direction must be one of {list(table)}, got {direction!r}")
        self.swipe(*table[direction], duration=duration)

    scroll = swipe_direction  # alias

    def type_text(self, text: str, clear: bool = False) -> None:
        """Type into the focused field.

        Falls back to the ADB broadcast IME path if the u2 fast-input IME is not
        enabled, so this keeps working on stock ROMs.
        """
        try:
            self._d.send_keys(text, clear=clear)
        except Exception as exc:
            if clear:
                self.clear_text()
            quoted = text.replace("\\", "\\\\").replace('"', '\\"')
            res = self.shell(f'am broadcast -a ADB_INPUT_TEXT --es msg "{quoted}"')
            if not res.ok:
                raise ActionFailedError(f"Could not type text: {exc} / {res.output}") from exc

    def clear_text(self) -> None:
        try:
            self._d.clear_text()
        except Exception:
            self.shell('am broadcast -a ADB_CLEAR_TEXT')

    def press(self, key: str) -> None:
        """``home``, ``back``, ``enter``, ``volume_up``, ``power``, ..."""
        self._d.press(key)

    def home(self) -> None:
        self.press("home")

    def back(self) -> None:
        self.press("back")

    def enter(self) -> None:
        self.press("enter")

    def wake(self) -> None:
        self.shell("input keyevent KEYCODE_WAKEUP")

    # ------------------------------------------------------------------
    # shell
    # ------------------------------------------------------------------
    def shell(self, cmd: Union[str, List[str]], timeout: int = 60) -> ShellResult:
        """Run an ``adb shell`` command and return output + exit code."""
        res = self._d.shell(cmd, timeout=timeout)
        output = getattr(res, "output", None)
        code = getattr(res, "exit_code", None)
        if output is None:                      # tolerate a plain-string return
            output, code = str(res), 0
        return ShellResult(output=output, exit_code=int(code or 0))

    # ------------------------------------------------------------------
    # apps
    # ------------------------------------------------------------------
    def launch(self, package: str, activity: Optional[str] = None,
               stop_first: bool = False, wait: bool = True,
               timeout: float = 15.0) -> Dict[str, Any]:
        """Start an app by package name."""
        self._d.app_start(package, activity=activity, wait=False, stop=stop_first)
        if wait:
            self.wait_for_app(package, timeout=timeout)
        return self.current_app()

    start_app = launch

    def stop(self, package: str) -> None:
        self._d.app_stop(package)

    def current_app(self) -> Dict[str, Any]:
        return dict(self._d.app_current() or {})

    def list_apps(self, third_party_only: bool = True) -> List[str]:
        return list(self._d.app_list(filter="-3" if third_party_only else None))

    def app_info(self, package: str) -> Dict[str, Any]:
        return dict(self._d.app_info(package))

    def install(self, apk_path: str) -> None:
        self._d.app_install(apk_path)

    def uninstall(self, package: str) -> bool:
        return bool(self._d.app_uninstall(package))

    def open_url(self, url: str) -> None:
        self._d.open_url(url)

    # ------------------------------------------------------------------
    # waiting
    # ------------------------------------------------------------------
    def wait_for_app(self, package: str, timeout: float = 15.0) -> bool:
        try:
            return bool(self._d.app_wait(package, timeout=timeout, front=True))
        except Exception:
            deadline = time.time() + timeout
            while time.time() < deadline:
                if self.current_app().get("package") == package:
                    return True
                time.sleep(0.5)
            return False

    def wait_for(self, *, text: Optional[str] = None, resource_id: Optional[str] = None,
                 content_desc: Optional[str] = None, timeout: float = 10.0,
                 interval: float = 0.5) -> Optional[UiNode]:
        """Poll the hierarchy until something matches, then return the node."""
        deadline = time.time() + timeout
        while time.time() < deadline:
            node = self.ui_tree().find_one(
                text=text, resource_id=resource_id, content_desc=content_desc
            )
            if node is not None:
                return node
            time.sleep(interval)
        raise ElementNotFoundError(
            f"text={text!r} resource_id={resource_id!r} content_desc={content_desc!r} "
            f"after {timeout}s"
        )

    def wait_idle(self, seconds: float = 1.0) -> None:
        time.sleep(seconds)

    # ------------------------------------------------------------------
    # files
    # ------------------------------------------------------------------
    def push(self, local: str, remote: str) -> None:
        self._d.push(local, remote)

    def pull(self, remote: str, local: str) -> None:
        parent = os.path.dirname(os.path.abspath(local))
        os.makedirs(parent, exist_ok=True)
        self._d.pull(remote, local)

    def set_clipboard(self, text: str, label: str = "androidctl") -> None:
        self._d.set_clipboard(text, label)

    @property
    def raw(self) -> Any:
        """Escape hatch to the underlying ``uiautomator2.Device``."""
        return self._d


def connect(serial: Optional[str] = None, **kwargs) -> AndroidDevice:
    """Connect to a device and return an :class:`AndroidDevice`.

    ``serial`` may be omitted when exactly one device is attached; with several
    attached you must name one (see :class:`androidctl.DeviceManager`).
    """
    import uiautomator2 as u2          # deferred: import is heavy
    from .errors import MultipleDevicesError, NoDeviceError
    from .adb import list_devices

    if serial is None:
        ready = [d.serial for d in list_devices() if d.ready]
        if not ready:
            raise NoDeviceError()
        if len(ready) > 1:
            raise MultipleDevicesError(ready)
        serial = ready[0]

    return AndroidDevice(u2.connect(serial, **kwargs), serial=serial)
