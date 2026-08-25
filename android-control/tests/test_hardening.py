"""Tests for the hardening layer: reconnect/retry, the agent loop, the CLI."""

from __future__ import annotations

import os
import sys

import pytest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from androidctl import AndroidDevice, DeviceManager  # noqa: E402
from androidctl.agent import AgentActionError, DeviceAgent  # noqa: E402
from androidctl.cli import build_parser, main as cli_main  # noqa: E402
from androidctl.resilience import RETRYABLE, ResilientDevice  # noqa: E402
from test_androidctl import FakeU2  # noqa: E402


# ===========================================================================
# resilience
# ===========================================================================
class FlakyU2(FakeU2):
    """Fails the first ``fail_times`` hierarchy dumps, then behaves normally."""

    def __init__(self, serial="FLAKY", fail_times=1, exc=None):
        super().__init__(serial)
        self.fail_times = fail_times
        self.exc = exc or ConnectionError("session broken")
        self.dump_attempts = 0

    def dump_hierarchy(self, compressed=False, pretty=False, max_depth=None,
                       root_in_active=None):
        self.dump_attempts += 1
        if self.dump_attempts <= self.fail_times:
            raise self.exc
        return super().dump_hierarchy(compressed, pretty, max_depth, root_in_active)


def _manager_with(monkeypatch, factory):
    """A DeviceManager whose connect() hands back freshly built fakes."""
    from androidctl.adb import AdbDevice
    mgr = DeviceManager()
    monkeypatch.setattr(mgr._adb, "devices",
                        lambda: [AdbDevice(serial="FLAKY", state="device")])
    monkeypatch.setattr("androidctl.device.connect",
                        lambda serial, **kw: factory(serial))
    return mgr


def test_retryable_includes_the_session_errors():
    names = {e.__name__ for e in RETRYABLE}
    assert {"ConnectionError", "TimeoutError", "OSError"}.issubset(names)
    assert "SessionBrokenError" in names          # u2 is installed in this venv
    assert "HTTPError" in names


def test_resilient_reconnects_and_succeeds(monkeypatch):
    mgr = _manager_with(monkeypatch, lambda s: AndroidDevice(FlakyU2(s), serial=s))
    d = ResilientDevice(mgr, "FLAKY", delay=0.0)

    out = d.ui_dump()                            # fails once, reconnects, retries
    assert "<hierarchy" in out
    assert d.reconnect_count == 1


def test_resilient_gives_up_after_attempts(monkeypatch):
    mgr = _manager_with(monkeypatch,
                        lambda s: AndroidDevice(FlakyU2(s, fail_times=99), serial=s))
    d = ResilientDevice(mgr, "FLAKY", attempts=3, delay=0.0)

    with pytest.raises(ConnectionError):
        d.ui_dump()
    assert d.reconnect_count == 2                # attempts-1 reconnects


def test_resilient_does_not_retry_unrelated_errors(monkeypatch):
    class AlwaysValueError(FakeU2):
        def shell(self, cmdargs, timeout=60):
            raise ValueError("programmer mistake")

    mgr = _manager_with(monkeypatch, lambda s: AndroidDevice(AlwaysValueError(s), serial=s))
    d = ResilientDevice(mgr, "FLAKY", delay=0.0)

    with pytest.raises(ValueError):
        d.shell("anything")
    assert d.reconnect_count == 0                # no pointless reconnect


def test_resilient_forwards_attributes_and_properties(monkeypatch):
    mgr = _manager_with(monkeypatch, lambda s: AndroidDevice(FakeU2(s), serial=s))
    d = ResilientDevice(mgr, "FLAKY", delay=0.0)

    assert d.shell("getprop ro.product.model").output == "Test-1\n"
    assert d.window_size == (1080, 2340)         # property, not callable
    d.reset()
    assert d._device is None


def test_resilient_repr(monkeypatch):
    mgr = _manager_with(monkeypatch, lambda s: AndroidDevice(FakeU2(s), serial=s))
    d = ResilientDevice(mgr, "FLAKY", delay=0.0)
    _ = d.device                                  # force connect
    assert "FLAKY" in repr(d) and "reconnects=0" in repr(d)


# ===========================================================================
# agent: action parsing
# ===========================================================================
@pytest.mark.parametrize("reply,expected", [
    ("tap 12", ("tap", "12")),
    ("TAP 12", ("tap", "12")),
    ("tap: 12", ("tap", "12")),
    ("swipe up", ("swipe", "up")),
    ("type hello world", ("type", "hello world")),
    ("press home", ("press", "home")),
    ("launch com.android.settings", ("launch", "com.android.settings")),
    ("done turned on Wi-Fi", ("done", "turned on Wi-Fi")),
    ("fail could not find the toggle", ("fail", "could not find the toggle")),
    ("wait", ("wait", "")),
    ("tap_xy 540 1200", ("tap_xy", "540 1200")),
    ("- tap 3", ("tap", "3")),
    ("```\ntap 7\n```", ("tap", "7")),
    ("tap 5\nand then also swipe up", ("tap", "5")),      # one action only
])
def test_parse_action_accepts_normal_forms(reply, expected):
    assert DeviceAgent.parse_action(reply) == expected


@pytest.mark.parametrize("reply", [
    '{"action": "tap", "id": 3}',
    '{"action": "tap", "args": "3"}',
    '{"action": "swipe", "args": "up"}',
    '{"action": "tap_xy", "x": 100, "y": 200}',
    '{"action": "type", "value": "hi"}',
    '{"verb": "launch", "args": ["com.x"]}',
])
def test_parse_action_accepts_json(reply):
    verb, args = DeviceAgent.parse_action(reply)
    assert verb in {"tap", "swipe", "tap_xy", "type", "launch"}
    assert args


@pytest.mark.parametrize("reply", ["", "   ", "dance around", "please tap the button"])
def test_parse_action_rejects_garbage(reply):
    with pytest.raises(AgentActionError):
        DeviceAgent.parse_action(reply)


# ===========================================================================
# agent: the loop
# ===========================================================================
class ScriptedLLM:
    """Returns canned replies in order, recording the prompts it was given."""

    def __init__(self, *replies):
        self.replies = list(replies)
        self.prompts = []

    def __call__(self, prompt):
        self.prompts.append(prompt)
        return self.replies.pop(0) if self.replies else "done finished"


@pytest.fixture
def agent_device():
    fake = FakeU2("AGENT1")
    from PIL import Image
    fake.screenshot = lambda *a, **k: Image.new("RGB", (8, 8), "black")
    return AndroidDevice(fake, serial="AGENT1")


def test_agent_reaches_done(agent_device):
    llm = ScriptedLLM("tap 1", "done Wi-Fi is on")
    result = DeviceAgent(agent_device, llm=llm, sleep_between=0).run("Turn on Wi-Fi")

    assert result.success is True
    assert result.summary == "Wi-Fi is on"
    assert result.step_count == 2
    assert result.steps[0].action == "tap"
    assert "tapped [1]" in result.steps[0].result


def test_agent_prompt_contains_goal_and_tree(agent_device):
    llm = ScriptedLLM("done ok")
    DeviceAgent(agent_device, llm=llm, sleep_between=0).run("Do the thing")

    prompt = llm.prompts[0]
    assert "Do the thing" in prompt
    assert "Settings" in prompt                  # from the UI tree
    assert "tap <id>" in prompt                  # the action contract
    assert "com.android.settings" in prompt


def test_agent_carries_bounded_history(agent_device):
    llm = ScriptedLLM("wait", "wait", "wait", "done")
    result = DeviceAgent(agent_device, llm=llm, sleep_between=0).run("x")
    assert result.success
    # history is capped at 6 lines
    for p in llm.prompts:
        assert p.count("screen=com.android.settings") <= 6


def test_agent_handles_fail(agent_device):
    llm = ScriptedLLM("fail the toggle is missing")
    result = DeviceAgent(agent_device, llm=llm, sleep_between=0).run("x")
    assert result.success is False
    assert "toggle is missing" in result.summary


def test_agent_stops_at_max_steps(agent_device):
    llm = ScriptedLLM(*(["wait"] * 10))
    result = DeviceAgent(agent_device, llm=llm, sleep_between=0).run("x", max_steps=3)
    assert result.success is False
    assert result.step_count == 3
    assert "max_steps=3" in result.summary


def test_agent_survives_a_bad_action_and_continues(agent_device):
    llm = ScriptedLLM("tap not-a-number", "tap 1", "done ok")
    result = DeviceAgent(agent_device, llm=llm, sleep_between=0).run("x")

    assert result.success is True
    assert result.steps[0].error and "numeric element id" in result.steps[0].error
    assert "tapped [1]" in result.steps[1].result


def test_agent_survives_an_unparseable_reply(agent_device):
    llm = ScriptedLLM("I think we should tap the button", "done ok")
    result = DeviceAgent(agent_device, llm=llm, sleep_between=0).run("x")
    assert result.success is True
    assert "unknown action" in result.steps[0].error


def test_agent_swipe_type_press_launch_execute(agent_device):
    llm = ScriptedLLM("swipe up", "type hello", "press home",
                      "launch com.android.settings", "done")
    result = DeviceAgent(agent_device, llm=llm, sleep_between=0).run("x")

    assert result.success
    results = [s.result for s in result.steps]
    assert results[0] == "swiped up"
    assert results[1] == "typed 5 chars"
    assert results[2] == "pressed home"
    assert "launched" in results[3]


def test_agent_tap_xy(agent_device):
    llm = ScriptedLLM("tap_xy 100 200", "done")
    result = DeviceAgent(agent_device, llm=llm, sleep_between=0).run("x")
    assert result.steps[0].result == "tapped (100, 200)"


def test_agent_on_step_callback_fires(agent_device):
    seen = []
    llm = ScriptedLLM("tap 1", "done")
    DeviceAgent(agent_device, llm=llm, on_step=seen.append,
                sleep_between=0).run("x")
    assert len(seen) == 2 and seen[0].index == 1


def test_agent_transcript_is_readable(agent_device):
    llm = ScriptedLLM("tap 1", "done all good")
    result = DeviceAgent(agent_device, llm=llm, sleep_between=0).run("Goal here")
    text = result.transcript()
    assert "GOAL: Goal here" in text
    assert "OUTCOME: success" in text
    assert "tap 1" in text


# ===========================================================================
# CLI
# ===========================================================================
def test_parser_builds_and_every_subcommand_has_a_func():
    parser = build_parser()
    # walk the subparsers action to collect the registered commands
    subs = [a for a in parser._actions if hasattr(a, "choices") and a.dest == "command"]
    assert subs, "no subparsers registered"
    choices = subs[0].choices
    assert {"devices", "ui", "shot", "tap", "swipe", "type", "shell",
            "launch", "apps", "connect", "state", "agent"}.issubset(set(choices))
    for name, sp in choices.items():
        assert callable(sp._defaults.get("func")), f"{name} has no handler"


def test_cli_devices_reports_no_devices_cleanly(monkeypatch, capsys):
    monkeypatch.setattr("androidctl.cli.list_devices", lambda: [])
    code = cli_main(["devices"])
    assert code == 1
    assert "no devices" in capsys.readouterr().out


def test_cli_devices_prints_a_table(monkeypatch, capsys):
    from androidctl.adb import AdbDevice
    monkeypatch.setattr("androidctl.cli.list_devices", lambda: [
        AdbDevice(serial="R5CT30ABCD", state="device", model="SM_A536B"),
        AdbDevice(serial="192.168.1.50:5555", state="device", model="Pixel_5"),
    ])
    assert cli_main(["devices"]) == 0
    out = capsys.readouterr().out
    assert "R5CT30ABCD" in out and "usb" in out
    assert "192.168.1.50:5555" in out and "wifi" in out


def test_cli_ui_runs_against_a_fake(monkeypatch, capsys):
    fake = FakeU2("CLI1")
    monkeypatch.setattr("androidctl.cli._get_device",
                        lambda s: AndroidDevice(fake, serial="CLI1"))
    assert cli_main(["ui", "--max-nodes", "10"]) == 0
    out = capsys.readouterr().out
    assert "Settings" in out and "[1]" in out


def test_cli_tap_by_coordinates(monkeypatch, capsys):
    fake = FakeU2("CLI1")
    monkeypatch.setattr("androidctl.cli._get_device",
                        lambda s: AndroidDevice(fake, serial="CLI1"))
    assert cli_main(["tap", "540", "1200"]) == 0
    assert fake.last("click") == ("click", 540, 1200)
    assert "tapped (540, 1200)" in capsys.readouterr().out


def test_cli_shell_propagates_exit_code(monkeypatch, capsys):
    fake = FakeU2("CLI1")
    monkeypatch.setattr("androidctl.cli._get_device",
                        lambda s: AndroidDevice(fake, serial="CLI1"))
    assert cli_main(["shell", "getprop", "ro.product.model"]) == 0
    assert "Test-1" in capsys.readouterr().out

    assert cli_main(["shell", "failplease"]) == 1


def test_cli_handles_no_device_without_a_traceback(monkeypatch, capsys):
    from androidctl.errors import NoDeviceError

    def boom(serial):
        raise NoDeviceError()

    monkeypatch.setattr("androidctl.cli._get_device", boom)
    code = cli_main(["ui"])
    assert code == 1
    assert "androidctl:" in capsys.readouterr().err
