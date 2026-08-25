"""Tests for androidctl using an in-process fake uiautomator2 transport.

No phone, no adb server, no network: ``FakeU2`` implements exactly the surface
``AndroidDevice`` uses, so these tests execute the real wrapper code paths --
hierarchy parsing/compaction, tap/swipe coordinate maths, shell result mapping,
app control, and the multi-device fan-out.
"""

from __future__ import annotations

import os
import sys
import xml.etree.ElementTree as ET

import pytest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from androidctl import (  # noqa: E402
    AndroidDevice,
    DeviceManager,
    ElementNotFoundError,
    ShellResult,
    parse_hierarchy,
)
from androidctl.hierarchy import compact_hierarchy  # noqa: E402


# ---------------------------------------------------------------------------
# fixtures: a realistic UiAutomator dump
# ---------------------------------------------------------------------------
HIERARCHY_XML = """<?xml version='1.0' encoding='UTF-8' standalone='yes' ?>
<hierarchy rotation="0" index="0">
  <node index="0" text="" resource-id="" class="android.widget.FrameLayout"
        package="com.android.settings" content-desc="" checkable="false" checked="false"
        clickable="false" enabled="true" focusable="false" focused="false"
        scrollable="false" long-clickable="false" password="false" selected="false"
        bounds="[0,0][1080,2340]">
    <node index="0" text="Settings" resource-id="com.android.settings:id/header"
          class="android.widget.TextView" package="com.android.settings" content-desc=""
          checkable="false" checked="false" clickable="true" enabled="true" focusable="true"
          focused="false" scrollable="false" long-clickable="false" password="false"
          selected="false" bounds="[40,140][200,220]" />
    <node index="1" text="" resource-id="com.android.settings:id/wifi_toggle"
          class="android.widget.Switch" package="com.android.settings" content-desc="Wi-Fi toggle"
          checkable="true" checked="true" clickable="true" enabled="true" focusable="true"
          focused="false" scrollable="false" long-clickable="false" password="false"
          selected="false" bounds="[900,260][1040,340]" />
    <node index="2" text="Password" resource-id="com.android.settings:id/pw_field"
          class="android.widget.EditText" package="com.android.settings" content-desc=""
          checkable="false" checked="false" clickable="true" enabled="true" focusable="true"
          focused="false" scrollable="false" long-clickable="true" password="true"
          selected="false" bounds="[60,400][1020,500]" />
    <node index="3" text="" resource-id="" class="android.view.View"
          package="com.android.settings" content-desc="" checkable="false" checked="false"
          clickable="false" enabled="false" focusable="false" focused="false"
          scrollable="false" long-clickable="false" password="false" selected="false"
          bounds="[0,0][0,0]" />
    <node index="4" text="Notifications" resource-id=""
          class="android.widget.LinearLayout" package="com.android.settings" content-desc=""
          checkable="false" checked="false" clickable="false" enabled="true" focusable="false"
          focused="false" scrollable="true" long-clickable="false" password="false"
          selected="false" bounds="[0,520][1080,2200]" />
  </node>
</hierarchy>"""


class _ShellResp:
    """Mirrors ``uiautomator2.abstract.ShellResponse``."""

    def __init__(self, output: str, exit_code: int = 0):
        self.output = output
        self.exit_code = exit_code


class _FakeImage:
    """Stand-in for PIL.Image -- records saves."""

    def __init__(self, sink):
        self._sink = sink

    def save(self, path_or_buf, format=None):
        self._sink.append(path_or_buf)


class FakeU2:
    """Implements the subset of uiautomator2.Device that AndroidDevice calls."""

    def __init__(self, serial="FAKE0001", width=1080, height=2340):
        self.serial = serial
        self._w, self._h = width, height
        self.calls = []
        self.typed = []
        self.keys = []
        self._sink = []

    # introspection
    @property
    def device_info(self):
        return {"serial": self.serial, "brand": "Fake", "model": "Test-1",
                "version": "14", "sdk": 34, "battery": {"level": 88},
                "display": {"width": self._w, "height": self._h}}

    def window_size(self):
        return (self._w, self._h)

    # screen
    def screenshot(self, filename=None, format="pillow", display_id=None):
        self.calls.append(("screenshot", filename))
        return _FakeImage(self._sink)

    # hierarchy
    def dump_hierarchy(self, compressed=False, pretty=False, max_depth=None,
                       root_in_active=None):
        self.calls.append(("dump_hierarchy", compressed, pretty))
        return HIERARCHY_XML

    def app_current(self):
        return {"package": "com.android.settings",
                "activity": ".Settings", "pid": 4242}

    # input
    def click(self, x, y):
        self.calls.append(("click", x, y))

    def long_click(self, x, y, duration=0.5):
        self.calls.append(("long_click", x, y, duration))

    def swipe(self, fx, fy, tx, ty, duration=None, steps=None):
        self.calls.append(("swipe", fx, fy, tx, ty, duration))

    def send_keys(self, text, clear=False):
        self.typed.append((text, clear))

    def clear_text(self):
        self.calls.append(("clear_text",))

    def press(self, key, meta=None):
        self.keys.append(key)

    # shell
    def shell(self, cmdargs, timeout=60):
        self.calls.append(("shell", cmdargs))
        if "getprop ro.product.model" in str(cmdargs):
            return _ShellResp("Test-1\n", 0)
        if "failplease" in str(cmdargs):
            return _ShellResp("boom", 1)
        return _ShellResp("ok\n", 0)

    # apps
    def app_start(self, package_name, activity=None, wait=False, stop=False,
                  use_monkey=False):
        self.calls.append(("app_start", package_name, activity, stop))

    def app_stop(self, package_name):
        self.calls.append(("app_stop", package_name))

    def app_wait(self, package_name, timeout=20.0, front=False):
        self.calls.append(("app_wait", package_name))
        return 1

    def app_list(self, filter=None):
        return ["com.android.settings", "com.example.app"]

    def app_info(self, package_name):
        return {"packageName": package_name, "versionName": "1.0"}

    def app_install(self, data):
        self.calls.append(("app_install", data))

    def app_uninstall(self, package_name):
        return True

    def open_url(self, url):
        self.calls.append(("open_url", url))

    # files
    def push(self, src, dst, mode=420):
        self.calls.append(("push", src, dst))

    def pull(self, src, dst):
        self.calls.append(("pull", src, dst))

    def set_clipboard(self, text, label=None):
        self.calls.append(("set_clipboard", text, label))

    def last(self, name):
        for c in reversed(self.calls):
            if c[0] == name:
                return c
        return None


@pytest.fixture
def fake():
    return FakeU2()


@pytest.fixture
def dev(fake):
    return AndroidDevice(fake, serial=fake.serial)


# ---------------------------------------------------------------------------
# hierarchy parsing
# ---------------------------------------------------------------------------
def test_parse_hierarchy_counts_and_indexes():
    tree = parse_hierarchy(HIERARCHY_XML)
    # 1 root FrameLayout + 5 children
    assert len(tree.nodes) == 6
    assert sorted(tree.nodes) == [0, 1, 2, 3, 4, 5]
    assert tree.package == "com.android.settings"   # inferred from node[0]


def test_parse_hierarchy_bounds_and_center():
    tree = parse_hierarchy(HIERARCHY_XML)
    header = tree.nodes[1]
    assert header.text == "Settings"
    assert header.bounds == (40, 140, 200, 220)
    assert header.center == (120, 180)
    assert header.width == 160 and header.height == 80
    assert header.clickable is True


def test_parse_hierarchy_flags():
    tree = parse_hierarchy(HIERARCHY_XML)
    switch = tree.nodes[2]
    assert switch.short_id == "wifi_toggle"
    assert switch.short_class == "Switch"
    assert switch.checkable and switch.checked
    pw = tree.nodes[3]
    assert pw.password is True
    assert pw.label == "Password"          # falls back to text
    assert tree.nodes[2].label == "Wi-Fi toggle"   # content-desc when no text


def test_parse_hierarchy_parent_child_links():
    tree = parse_hierarchy(HIERARCHY_XML)
    assert tree.nodes[0].children == [1, 2, 3, 4, 5] or tree.nodes[0].children
    root = tree.nodes[0]
    assert 1 in root.children and 5 in root.children


def test_parse_hierarchy_rejects_empty():
    with pytest.raises(ValueError):
        parse_hierarchy("")
    with pytest.raises(ET.ParseError):
        parse_hierarchy("<not-xml")


def test_compact_hierarchy_hides_invisible_and_disabled():
    tree = parse_hierarchy(HIERARCHY_XML)
    text = compact_hierarchy(tree)
    assert "Settings" in text
    assert "wifi_toggle" in text
    # node 4 is 0x0 + disabled -> filtered out of the default view
    assert "[4]" not in text
    assert "nodes=6" in text


def test_compact_hierarchy_include_all_shows_everything():
    tree = parse_hierarchy(HIERARCHY_XML)
    assert "[4]" in compact_hierarchy(tree, include_all=True)


def test_compact_hierarchy_max_nodes_caps_output():
    tree = parse_hierarchy(HIERARCHY_XML)
    text = compact_hierarchy(tree, include_all=True, max_nodes=2)
    assert "(showing 2)" in text


def test_find_and_find_one():
    tree = parse_hierarchy(HIERARCHY_XML)
    assert len(tree.find(text="Settings")) == 1
    assert tree.find_one(resource_id="pw_field").password is True
    assert tree.find_one(text="does-not-exist") is None
    assert len(tree.find(clickable=True)) == 3
    assert tree.find_one(content_desc="wi-fi").node_id == 2


def test_interactive_filters_to_visible_actionable():
    tree = parse_hierarchy(HIERARCHY_XML)
    ids = {n.node_id for n in tree.interactive()}
    assert {1, 2, 3, 5}.issubset(ids)      # header, switch, edittext, scrollable list
    assert 4 not in ids


def test_get_unknown_id_raises_helpful_keyerror():
    tree = parse_hierarchy(HIERARCHY_XML)
    with pytest.raises(KeyError, match="No UI element with id 99"):
        tree.get(99)


# ---------------------------------------------------------------------------
# device: screen
# ---------------------------------------------------------------------------
def test_screenshot_returns_image_and_writes_file(tmp_path, dev, fake):
    img = dev.screenshot()
    assert isinstance(img, _FakeImage)
    out = tmp_path / "shots" / "a.png"
    dev.screenshot(str(out))
    assert fake.last("screenshot") is not None
    assert fake._sink[-1] == str(out)


def test_screenshot_b64_is_ascii_base64(dev, monkeypatch):
    # swap in a real minimal PNG so base64/bytes paths are exercised for real
    import base64
    import io
    from PIL import Image

    class RealImage:
        def save(self, buf, format=None):
            Image.new("RGB", (4, 4), "red").save(buf, format=format or "PNG")

    monkeypatch.setattr(dev._d, "screenshot", lambda *a, **k: RealImage())
    b64 = dev.screenshot_b64()
    assert b64.isascii()
    assert base64.b64decode(b64)[:8] == b"\x89PNG\r\n\x1a\n"


# ---------------------------------------------------------------------------
# device: input
# ---------------------------------------------------------------------------
def test_tap_maps_to_click(dev, fake):
    dev.tap(540, 1200)
    assert fake.last("click") == ("click", 540, 1200)


def test_click_alias_is_tap(dev, fake):
    dev.click(10, 20)
    assert fake.last("click") == ("click", 10, 20)


def test_tap_element_uses_node_center(dev, fake):
    node = dev.tap_element(1)              # header, bounds 40,140-200,220
    assert node.text == "Settings"
    assert fake.last("click") == ("click", 120, 180)


def test_tap_element_accepts_node_object(dev, fake):
    tree = dev.ui_tree()
    dev.tap_element(tree.nodes[2])
    assert fake.last("click") == ("click", 970, 300)


def test_tap_element_offset_applied(dev, fake):
    dev.tap_element(1, offset=(5, -5))
    assert fake.last("click") == ("click", 125, 175)


def test_tap_percent_uses_window_size(dev, fake):
    dev.tap_percent(0.5, 0.5)
    assert fake.last("click") == ("click", 540, 1170)


def test_swipe_direction_up_coordinates(dev, fake):
    dev.swipe_direction("up", scale=0.6)
    c = fake.last("swipe")
    # centre 540,1170 ; dy = 2340*0.6/2 = 702
    assert c == ("swipe", 540, 1872, 540, 468, 0.3)


def test_swipe_direction_down_is_inverse(dev, fake):
    dev.swipe_direction("down", scale=0.6)
    assert fake.last("swipe") == ("swipe", 540, 468, 540, 1872, 0.3)


def test_swipe_direction_left_right(dev, fake):
    dev.swipe_direction("left", scale=0.6)
    # dx = 1080*0.6/2 = 324
    assert fake.last("swipe") == ("swipe", 864, 1170, 216, 1170, 0.3)
    dev.swipe_direction("right", scale=0.6)
    assert fake.last("swipe") == ("swipe", 216, 1170, 864, 1170, 0.3)


def test_swipe_direction_rejects_bad_direction(dev):
    from androidctl.errors import ActionFailedError
    with pytest.raises(ActionFailedError, match="direction must be one of"):
        dev.swipe_direction("sideways")


def test_long_press_passes_duration(dev, fake):
    dev.long_press(100, 200, duration=1.5)
    assert fake.last("long_click") == ("long_click", 100, 200, 1.5)


def test_type_text_goes_through_send_keys(dev, fake):
    dev.type_text("hello world", clear=True)
    assert fake.typed == [("hello world", True)]


def test_type_text_falls_back_to_adb_broadcast(dev, fake, monkeypatch):
    def boom(text, clear=False):
        raise RuntimeError("no IME")
    monkeypatch.setattr(fake, "send_keys", boom)
    dev.type_text("hi there")
    shell_calls = [c for c in fake.calls if c[0] == "shell"]
    assert any("ADB_INPUT_TEXT" in str(c[1]) for c in shell_calls)


def test_press_and_shortcuts(dev, fake):
    dev.home(); dev.back(); dev.enter()
    assert fake.keys == ["home", "back", "enter"]


# ---------------------------------------------------------------------------
# device: shell
# ---------------------------------------------------------------------------
def test_shell_returns_structured_result(dev):
    res = dev.shell("getprop ro.product.model")
    assert isinstance(res, ShellResult)
    assert res.output == "Test-1\n"
    assert res.exit_code == 0 and res.ok is True
    assert str(res) == "Test-1\n"


def test_shell_propagates_nonzero_exit(dev):
    res = dev.shell("failplease")
    assert res.ok is False and res.exit_code == 1


def test_shell_accepts_list_argv(dev, fake):
    dev.shell(["getprop", "ro.product.model"])
    assert fake.last("shell") == ("shell", ["getprop", "ro.product.model"])


def test_shell_tolerates_plain_string_return(dev, fake, monkeypatch):
    monkeypatch.setattr(fake, "shell", lambda cmd, timeout=60: "just a string")
    res = dev.shell("anything")
    assert res.output == "just a string" and res.exit_code == 0


# ---------------------------------------------------------------------------
# device: apps
# ---------------------------------------------------------------------------
def test_launch_starts_and_waits(dev, fake):
    info = dev.launch("com.android.settings")
    assert fake.last("app_start")[1] == "com.android.settings"
    assert fake.last("app_wait") is not None
    assert info["package"] == "com.android.settings"


def test_launch_stop_first(dev, fake):
    dev.launch("com.android.settings", stop_first=True)
    assert fake.last("app_start")[3] is True


def test_stop_current_and_list(dev, fake):
    dev.stop("com.example.app")
    assert fake.last("app_stop") == ("app_stop", "com.example.app")
    assert dev.current_app()["activity"] == ".Settings"
    assert dev.list_apps() == ["com.android.settings", "com.example.app"]


def test_summary_shape(dev):
    s = dev.summary()
    assert s["serial"] == "FAKE0001"
    assert s["width"] == 1080 and s["height"] == 2340
    assert s["model"] == "Test-1" and s["android_version"] == "14"


def test_summary_survives_broken_device_info(dev, fake, monkeypatch):
    def boom():
        raise RuntimeError("server down")
    monkeypatch.setattr(type(fake), "device_info", property(lambda self: boom()))
    s = dev.summary()
    assert "error" in s and s["serial"] == "FAKE0001"
    assert "server down" in s["error"]


def test_summary_survives_broken_window_size(dev, fake, monkeypatch):
    def boom():
        raise RuntimeError("screen off")
    monkeypatch.setattr(fake, "window_size", boom)
    s = dev.summary()
    assert s["width"] == 0 and s["height"] == 0
    assert "screen off" in s["error"]


# ---------------------------------------------------------------------------
# device: waiting / screen_state
# ---------------------------------------------------------------------------
def test_wait_for_finds_existing_node(dev):
    node = dev.wait_for(text="Settings", timeout=1.0)
    assert node.text == "Settings"


def test_wait_for_times_out(dev):
    with pytest.raises(ElementNotFoundError):
        dev.wait_for(text="nope-not-here", timeout=0.3, interval=0.1)


def test_screen_state_contains_tree_and_image(dev, fake, monkeypatch):
    from PIL import Image

    class RealImage:
        def save(self, buf, format=None):
            Image.new("RGB", (2, 2), "blue").save(buf, format=format or "PNG")

    monkeypatch.setattr(fake, "screenshot", lambda *a, **k: RealImage())
    state = dev.screen_state()
    assert state["app"]["package"] == "com.android.settings"
    assert "Settings" in state["ui_tree"]
    assert state["screenshot_png_b64"].startswith("iVBORw0KGgo")


# ---------------------------------------------------------------------------
# multi-device
# ---------------------------------------------------------------------------
def test_manager_broadcast_and_parallel(monkeypatch):
    mgr = DeviceManager()
    fakes = {"A": FakeU2("A"), "B": FakeU2("B", width=720, height=1280)}
    monkeypatch.setattr(mgr._adb, "devices",
                        lambda: [_fake_adbdev("A"), _fake_adbdev("B")])
    monkeypatch.setattr("androidctl.device.connect",
                        lambda serial, **kw: AndroidDevice(fakes[serial], serial=serial))

    assert mgr.serials == ["A", "B"]
    assert len(mgr) == 2

    seq = mgr.broadcast(lambda d: d.shell("getprop ro.product.model").output.strip())
    assert seq == {"A": "Test-1", "B": "Test-1"}

    par = mgr.parallel(lambda d: d.window_size)
    assert par == {"A": (1080, 2340), "B": (720, 1280)}


def test_manager_caches_connections(monkeypatch):
    mgr = DeviceManager()
    calls = []

    def fake_connect(serial, **kw):
        calls.append(serial)
        return AndroidDevice(FakeU2(serial), serial=serial)

    monkeypatch.setattr(mgr._adb, "devices", lambda: [_fake_adbdev("A")])
    monkeypatch.setattr("androidctl.device.connect", fake_connect)

    first = mgr.connect("A")
    second = mgr.connect("A")
    assert first is second and calls == ["A"]
    mgr.disconnect("A")
    assert mgr.connect("A") is not first


def test_manager_captures_errors_instead_of_raising(monkeypatch):
    mgr = DeviceManager()
    monkeypatch.setattr(mgr._adb, "devices", lambda: [_fake_adbdev("A"), _fake_adbdev("B")])

    def connect(serial, **kw):
        if serial == "B":
            raise RuntimeError("offline")
        return AndroidDevice(FakeU2(serial), serial=serial)

    monkeypatch.setattr("androidctl.device.connect", connect)
    out = mgr.broadcast(lambda d: "ok")
    assert out["A"] == "ok"
    assert "error" in out["B"] and "offline" in out["B"]["error"]


def test_manager_summary_lists_unreachable(monkeypatch):
    mgr = DeviceManager()
    monkeypatch.setattr(mgr._adb, "devices", lambda: [_fake_adbdev("A")])

    def boom(serial, **kw):
        raise RuntimeError("nope")

    monkeypatch.setattr("androidctl.device.connect", boom)
    assert mgr.summary() == [{"serial": "A", "error": "unreachable"}]


def _fake_adbdev(serial):
    from androidctl.adb import AdbDevice
    return AdbDevice(serial=serial, state="device", model="Test-1")
