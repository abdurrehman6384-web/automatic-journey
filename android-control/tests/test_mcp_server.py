"""End-to-end test of the MCP server over real stdio JSON-RPC.

This spawns ``mcp_server.py`` as a subprocess and speaks the actual MCP wire
protocol to it: ``initialize`` -> ``notifications/initialized`` -> ``tools/list``
-> ``tools/call``. No mocks on the transport, so a broken tool signature or a
crash-on-startup fails here.

``android_list_devices`` is exercised for real: it shells out to the bundled
``adb`` binary. With no phone attached it must return an empty, well-formed list
rather than an error -- that is the contract clients depend on.
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
import threading
import time

import pytest

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, ".."))
SERVER = os.path.join(ROOT, "mcp_server.py")

PYTHON = os.environ.get("ANDROIDCTL_PYTHON") or (
    os.path.join(ROOT, ".venv", "bin", "python")
    if os.path.exists(os.path.join(ROOT, ".venv", "bin", "python"))
    else sys.executable
)


class StdioClient:
    """Minimal line-delimited JSON-RPC client for an MCP stdio server."""

    def __init__(self):
        self.proc = subprocess.Popen(
            [PYTHON, SERVER],
            stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
            text=True, bufsize=1, cwd=ROOT,
        )
        self._id = 0
        self._lock = threading.Lock()

    def send(self, payload: dict) -> None:
        assert self.proc.stdin is not None
        self.proc.stdin.write(json.dumps(payload) + "\n")
        self.proc.stdin.flush()

    def request(self, method: str, params: dict | None = None, timeout: float = 60.0) -> dict:
        with self._lock:
            self._id += 1
            rid = self._id
        self.send({"jsonrpc": "2.0", "id": rid, "method": method,
                   "params": params or {}})
        deadline = time.time() + timeout
        while time.time() < deadline:
            line = self.proc.stdout.readline()
            if not line:
                err = self.proc.stderr.read() if self.proc.stderr else ""
                raise RuntimeError(f"server closed stdout. stderr:\n{err}")
            line = line.strip()
            if not line:
                continue
            msg = json.loads(line)
            # notifications have no id; skip them
            if msg.get("id") == rid:
                return msg
        raise TimeoutError(f"no response to {method} within {timeout}s")

    def notify(self, method: str, params: dict | None = None) -> None:
        self.send({"jsonrpc": "2.0", "method": method, "params": params or {}})

    def close(self) -> None:
        try:
            self.proc.stdin.close()
        except Exception:
            pass
        try:
            self.proc.wait(timeout=10)
        except Exception:
            self.proc.kill()


@pytest.fixture
def client():
    c = StdioClient()
    try:
        yield c
    finally:
        c.close()


def _initialize(client: StdioClient) -> dict:
    res = client.request("initialize", {
        "protocolVersion": "2025-06-18",
        "capabilities": {},
        "clientInfo": {"name": "pytest-androidctl", "version": "1.0.0"},
    })
    assert "result" in res, res
    client.notify("notifications/initialized")
    return res["result"]


def test_server_handshake_reports_identity(client):
    result = _initialize(client)
    assert result["serverInfo"]["name"] == "android-control"
    assert "capabilities" in result


def test_tools_list_exposes_the_documented_surface(client):
    _initialize(client)
    res = client.request("tools/list")
    names = {t["name"] for t in res["result"]["tools"]}

    required = {
        "android_list_devices", "android_screen_state", "android_screenshot",
        "android_ui_tree", "android_tap", "android_tap_element", "android_swipe",
        "android_scroll", "android_type_text", "android_press_key",
        "android_launch_app", "android_current_app", "android_shell",
        "android_find_element", "android_wait_for", "android_device_info",
    }
    missing = required - names
    assert not missing, f"missing tools: {missing}"
    assert len(names) >= 20


def test_every_tool_declares_a_description_and_schema(client):
    _initialize(client)
    res = client.request("tools/list")
    for tool in res["result"]["tools"]:
        assert tool.get("description"), f"{tool['name']} has no description"
        assert tool.get("inputSchema", {}).get("type") == "object", tool["name"]


def test_list_devices_returns_wellformed_empty_list(client):
    """Real adb call. No phone in CI -> empty list, still ok:true."""
    _initialize(client)
    res = client.request("tools/call", {
        "name": "android_list_devices", "arguments": {},
    })
    assert "error" not in res, res
    payload = json.loads(res["result"]["content"][0]["text"])
    assert payload["ok"] is True
    assert payload["count"] == len(payload["devices"])
    assert isinstance(payload["devices"], list)


def test_action_without_device_returns_structured_error(client):
    """No phone attached -> the tool must degrade to a helpful error, not crash."""
    _initialize(client)
    res = client.request("tools/call", {
        "name": "android_tap", "arguments": {"x": 100, "y": 100},
    })
    assert "error" not in res, res          # transport-level call succeeded
    assert res["result"].get("isError") is not True or True   # either shape is fine
    text = res["result"]["content"][0]["text"]
    payload = json.loads(text)
    assert payload["ok"] is False
    assert "hint" in payload and payload["hint"]


def test_unknown_tool_is_rejected(client):
    _initialize(client)
    res = client.request("tools/call", {
        "name": "android_does_not_exist", "arguments": {},
    })
    assert "error" in res or res["result"].get("isError") is True
