"""Tests for the adb layer: binary resolution and `adb devices -l` parsing."""

from __future__ import annotations

import os
import sys

import pytest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from androidctl import adb as adb_mod  # noqa: E402
from androidctl.adb import AdbDevice, AdbRunner, find_adb  # noqa: E402
from androidctl.errors import AdbNotFoundError  # noqa: E402


DEVICES_OUTPUT = """List of devices attached
R5CT30ABCD           device usb:1-2 product:a53xnaxx model:SM_A536B transport_id:3
192.168.1.50:5555    device product:redfin model:Pixel_5 transport_id:7
emulator-5554        offline transport_id:9
UNAUTHORIZED1        unauthorized transport_id:11
"""


class _StubRunner:
    """AdbRunner with a canned `adb devices -l` reply."""

    def __init__(self, text):
        self._text = text
        self.adb = "/fake/adb"

    def run(self, *args, serial=None, timeout=60):
        assert args[0] == "devices"
        return self._text


# ---------------------------------------------------------------------------
# parsing
# ---------------------------------------------------------------------------
def test_parses_usb_and_wifi_and_bad_states(monkeypatch):
    runner = _StubRunner(DEVICES_OUTPUT)
    devs = AdbRunner.devices(runner)          # unbound: skip __init__/real adb

    assert [d.serial for d in devs] == [
        "R5CT30ABCD", "192.168.1.50:5555", "emulator-5554", "UNAUTHORIZED1",
    ]
    assert [d.state for d in devs] == ["device", "device", "offline", "unauthorized"]
    assert [d.ready for d in devs] == [True, True, False, False]
    assert [d.is_usb for d in devs] == [True, False, True, True]


def test_parses_model_and_product_fields(monkeypatch):
    devs = AdbRunner.devices(_StubRunner(DEVICES_OUTPUT))
    phone = devs[0]
    assert phone.model == "SM_A536B"
    assert phone.product == "a53xnaxx"
    assert phone.transport_id == "3"


def test_ignores_daemon_noise_and_blanks():
    text = ("List of devices attached\n"
            "* daemon not running; starting now at tcp:5037\n"
            "* daemon started successfully\n"
            "\n"
            "ABC123               device transport_id:1\n")
    devs = AdbRunner.devices(_StubRunner(text))
    assert len(devs) == 1 and devs[0].serial == "ABC123"


def test_empty_device_list():
    assert AdbRunner.devices(_StubRunner("List of devices attached\n")) == []


def test_malformed_rows_are_skipped():
    text = "List of devices attached\n" + "garbagerow\n" + "OK1 device transport_id:2\n"
    devs = AdbRunner.devices(_StubRunner(text))
    assert [d.serial for d in devs] == ["OK1"]   # the malformed row is dropped
    assert devs[0].ready is True


# ---------------------------------------------------------------------------
# binary resolution
# ---------------------------------------------------------------------------
def test_find_adb_honours_ADB_PATH(monkeypatch, tmp_path):
    fake = tmp_path / "adb"
    fake.write_text("#!/bin/sh\n")
    fake.chmod(0o755)
    monkeypatch.setenv("ADB_PATH", str(fake))
    monkeypatch.setattr(adb_mod.shutil, "which", lambda _: None)
    assert find_adb() == str(fake)


def test_find_adb_falls_back_to_PATH(monkeypatch):
    monkeypatch.delenv("ADB_PATH", raising=False)
    monkeypatch.delenv("ANDROID_HOME", raising=False)
    monkeypatch.delenv("ANDROID_SDK_ROOT", raising=False)
    monkeypatch.setattr(adb_mod.shutil, "which", lambda name: "/usr/bin/adb")
    monkeypatch.setattr(adb_mod.os.path, "isfile", lambda p: p == "/usr/bin/adb")
    monkeypatch.setattr(adb_mod.os, "access", lambda p, m: True)
    assert find_adb() == "/usr/bin/adb"


def test_find_adb_uses_bundled_adbutils_binary(monkeypatch):
    monkeypatch.delenv("ADB_PATH", raising=False)
    monkeypatch.setattr(adb_mod.shutil, "which", lambda _: None)
    monkeypatch.setattr(adb_mod.os.path, "isfile", lambda p: "adbutils" in p)
    monkeypatch.setattr(adb_mod.os, "access", lambda p, m: True)
    assert "adbutils" in find_adb()


def test_find_adb_error_lists_candidates_and_is_not_blank(monkeypatch):
    """Regression: the candidate list used to render as an empty string."""
    monkeypatch.setenv("ADB_PATH", "/does/not/exist/adb")
    monkeypatch.setattr(adb_mod.shutil, "which", lambda _: None)
    monkeypatch.delenv("ANDROID_HOME", raising=False)
    monkeypatch.delenv("ANDROID_SDK_ROOT", raising=False)
    monkeypatch.setattr(adb_mod.os.path, "isfile", lambda p: False)
    with pytest.raises(AdbNotFoundError) as ei:
        find_adb()
    msg = str(ei.value)
    assert "/does/not/exist/adb" in msg
    assert "Looked at: ." not in msg          # the old broken rendering


def test_find_adb_error_when_no_candidates_at_all(monkeypatch):
    monkeypatch.delenv("ADB_PATH", raising=False)
    monkeypatch.delenv("ANDROID_HOME", raising=False)
    monkeypatch.delenv("ANDROID_SDK_ROOT", raising=False)
    monkeypatch.setattr(adb_mod.shutil, "which", lambda _: None)
    monkeypatch.setattr(adb_mod, "adbutils", None, raising=False)
    import builtins
    real_import = builtins.__import__

    def no_adbutils(name, *a, **k):
        if name == "adbutils":
            raise ImportError("nope")
        return real_import(name, *a, **k)

    monkeypatch.setattr(builtins, "__import__", no_adbutils)
    with pytest.raises(AdbNotFoundError, match="<nothing>"):
        find_adb()


def test_real_adb_binary_is_present_and_reports_a_version():
    """The environment we ship must actually have a working adb."""
    path = find_adb()
    assert os.path.isfile(path)
    out = adb_mod.adb_version(path)
    assert "Android Debug Bridge" in out


def test_connect_wifi_rejects_a_refused_host(monkeypatch):
    monkeypatch.setattr(AdbRunner, "run",
                        lambda self, *a, **k: "failed to connect to 10.0.0.9:5555")
    from androidctl.errors import DeviceOfflineError
    with pytest.raises(DeviceOfflineError):
        adb_mod.connect_wifi("10.0.0.9", adb="/fake/adb")
