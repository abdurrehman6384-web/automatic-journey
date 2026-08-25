#!/usr/bin/env python3
"""``androidctl`` -- command-line front end.

    androidctl devices
    androidctl ui                         # compact tree of the current screen
    androidctl shot screen.png
    androidctl tap 540 1200
    androidctl swipe up
    androidctl type "hello world"
    androidctl launch com.android.settings
    androidctl shell getprop ro.product.model
    androidctl connect 192.168.1.50 5555  # wireless ADB
    androidctl agent "Turn on Wi-Fi"      # needs an LLM key

Pass ``-s SERIAL`` to any subcommand to target one device when several are
attached, or set ``ANDROID_SERIAL``.

Install as a console script (optional):

    pip install -e .
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from typing import Any, List, Optional

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from androidctl import (  # noqa: E402
    AndroidCtlError,
    DeviceManager,
    connect_wifi,
    list_devices,
)

PROG = "androidctl"


# ---------------------------------------------------------------------------
# helpers
# ---------------------------------------------------------------------------
def _fail(message: str, code: int = 1) -> int:
    print(f"{PROG}: {message}", file=sys.stderr)
    return code


def _get_device(serial: Optional[str]):
    mgr = DeviceManager()
    return mgr.connect(serial or os.environ.get("ANDROID_SERIAL") or None)


def _emit(data: Any, as_json: bool) -> None:
    if as_json:
        print(json.dumps(data, indent=2, default=str))
    else:
        print(data)


# ---------------------------------------------------------------------------
# subcommands
# ---------------------------------------------------------------------------
def cmd_devices(args) -> int:
    try:
        devs = list_devices()
    except AndroidCtlError as exc:
        return _fail(str(exc))
    if not devs:
        print("no devices. Enable USB debugging, or `androidctl connect <ip> [port]`.")
        return 1
    if args.json:
        _emit([d.__dict__ for d in devs], True)
        return 0
    print(f"{'SERIAL':30s} {'STATE':12s} {'TRANSPORT':10s} MODEL")
    for d in devs:
        print(f"{d.serial:30s} {d.state:12s} "
              f"{'usb' if d.is_usb else 'wifi':10s} {d.model or ''}")
    return 0


def cmd_connect(args) -> int:
    try:
        target = connect_wifi(args.host, args.port)
    except AndroidCtlError as exc:
        return _fail(str(exc))
    print(f"connected to {target}")
    return 0


def cmd_disconnect(args) -> int:
    from androidctl import disconnect
    target = args.target or os.environ.get("ANDROID_SERIAL")
    if not target:
        return _fail("give a host:port or set ANDROID_SERIAL")
    print(disconnect(target))
    return 0


def cmd_info(args) -> int:
    try:
        d = _get_device(args.serial)
    except AndroidCtlError as exc:
        return _fail(str(exc))
    _emit(d.summary(), args.json or True)
    return 0


def cmd_ui(args) -> int:
    try:
        d = _get_device(args.serial)
    except AndroidCtlError as exc:
        return _fail(str(exc))
    if args.raw:
        print(d.ui_dump())
        return 0
    tree = d.ui_tree()
    if args.json:
        _emit({"package": tree.package, "activity": tree.activity,
               "nodes": [n.to_dict() for n in tree.nodes.values()]}, True)
    else:
        print(tree.to_text(include_all=args.all, max_nodes=args.max_nodes))
    return 0


def cmd_shot(args) -> int:
    try:
        d = _get_device(args.serial)
        d.screenshot(args.path)
    except AndroidCtlError as exc:
        return _fail(str(exc))
    print(os.path.abspath(args.path))
    return 0


def cmd_tap(args) -> int:
    try:
        d = _get_device(args.serial)
        if args.id is not None:
            node = d.tap_element(args.id)
            print(f"tapped [{args.id}] {node.label!r} at {node.center}")
        else:
            d.tap(args.x, args.y)
            print(f"tapped ({args.x}, {args.y})")
    except AndroidCtlError as exc:
        return _fail(str(exc))
    return 0


def cmd_swipe(args) -> int:
    try:
        d = _get_device(args.serial)
        if args.coords:
            d.swipe(*args.coords)
            print(f"swiped {args.coords}")
        else:
            d.swipe_direction(args.direction)
            print(f"swiped {args.direction}")
    except AndroidCtlError as exc:
        return _fail(str(exc))
    return 0


def cmd_type(args) -> int:
    try:
        _get_device(args.serial).type_text(args.text, clear=args.clear)
    except AndroidCtlError as exc:
        return _fail(str(exc))
    print("ok")
    return 0


def cmd_press(args) -> int:
    try:
        _get_device(args.serial).press(args.key)
    except AndroidCtlError as exc:
        return _fail(str(exc))
    print(f"pressed {args.key}")
    return 0


def cmd_shell(args) -> int:
    try:
        res = _get_device(args.serial).shell(" ".join(args.command), timeout=args.timeout)
    except AndroidCtlError as exc:
        return _fail(str(exc))
    sys.stdout.write(res.output)
    if not res.output.endswith("\n"):
        print()
    return res.exit_code


def cmd_launch(args) -> int:
    try:
        info = _get_device(args.serial).launch(args.package, stop_first=args.stop_first)
    except AndroidCtlError as exc:
        return _fail(str(exc))
    print(f"{info.get('package')} / {info.get('activity')}")
    return 0


def cmd_current(args) -> int:
    try:
        cur = _get_device(args.serial).current_app()
    except AndroidCtlError as exc:
        return _fail(str(exc))
    _emit(cur, args.json)
    return 0


def cmd_apps(args) -> int:
    try:
        apps = _get_device(args.serial).list_apps(third_party_only=not args.system)
    except AndroidCtlError as exc:
        return _fail(str(exc))
    for pkg in apps:
        print(pkg)
    return 0


def cmd_state(args) -> int:
    try:
        state = _get_device(args.serial).screen_state(max_nodes=args.max_nodes)
    except AndroidCtlError as exc:
        return _fail(str(exc))
    if args.no_image:
        state.pop("screenshot_png_b64", None)
    _emit(state, True)
    return 0


def cmd_agent(args) -> int:
    from androidctl.agent import DeviceAgent

    try:
        d = _get_device(args.serial)
    except AndroidCtlError as exc:
        return _fail(str(exc))

    llm = _resolve_llm(args.provider)
    if llm is None:
        return _fail("no LLM available. Set GROQ_API_KEY / OPENAI_API_KEY, "
                     "or pass --provider module:callable")

    agent = DeviceAgent(d, llm=llm, max_nodes=args.max_nodes)
    result = agent.run(args.goal, max_steps=args.max_steps)
    print(result.transcript())
    return 0 if result.success else 2


def _resolve_llm(spec: Optional[str]):
    """``module.path:callable`` or one of the built-in env-key providers."""
    if spec and ":" in spec:
        module, _, attr = spec.partition(":")
        import importlib
        try:
            return getattr(importlib.import_module(module), attr)
        except Exception as exc:
            print(f"{PROG}: could not load {spec}: {exc}", file=sys.stderr)
            return None

    groq = os.environ.get("GROQ_API_KEY")
    if groq:
        return _http_llm("https://api.groq.com/openai/v1/chat/completions",
                         groq, "llama-3.1-70b-versatile")
    openai = os.environ.get("OPENAI_API_KEY")
    if openai:
        return _http_llm("https://api.openai.com/v1/chat/completions",
                         openai, "gpt-4o-mini")
    return None


def _http_llm(url: str, key: str, model: str):
    import requests

    def call(prompt: str) -> str:
        r = requests.post(
            url,
            headers={"Authorization": f"Bearer {key}",
                     "Content-Type": "application/json"},
            json={"model": model,
                  "messages": [{"role": "user", "content": prompt}],
                  "temperature": 0.2},
            timeout=30,
        )
        r.raise_for_status()
        return r.json()["choices"][0]["message"]["content"]
    return call


# ---------------------------------------------------------------------------
# parser
# ---------------------------------------------------------------------------
def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(prog=PROG, description="Android device control over ADB")
    p.add_argument("-s", "--serial", help="device serial (or set ANDROID_SERIAL)")
    sub = p.add_subparsers(dest="command", required=True)

    def add(name, fn, help_text, **kwargs):
        sp = sub.add_parser(name, help=help_text, **kwargs)
        sp.set_defaults(func=fn)
        return sp

    sp = add("devices", cmd_devices, "list connected devices")
    sp.add_argument("--json", action="store_true")

    sp = add("connect", cmd_connect, "wireless ADB: adb connect host:port")
    sp.add_argument("host")
    sp.add_argument("port", nargs="?", type=int, default=5555)

    sp = add("disconnect", cmd_disconnect, "drop a wireless ADB connection")
    sp.add_argument("target", nargs="?")

    sp = add("info", cmd_info, "device model / version / screen / battery")
    sp.add_argument("--json", action="store_true")

    sp = add("ui", cmd_ui, "dump the UI tree")
    sp.add_argument("--raw", action="store_true", help="raw XML instead of compact")
    sp.add_argument("--all", action="store_true", help="include invisible/disabled nodes")
    sp.add_argument("--json", action="store_true")
    sp.add_argument("--max-nodes", type=int, default=400)

    sp = add("shot", cmd_shot, "save a screenshot")
    sp.add_argument("path", nargs="?", default="screenshot.png")

    sp = add("tap", cmd_tap, "tap the screen")
    sp.add_argument("x", nargs="?", type=int)
    sp.add_argument("y", nargs="?", type=int)
    sp.add_argument("--id", type=int, help="tap a UI element by [id] instead")

    sp = add("swipe", cmd_swipe, "swipe / scroll")
    sp.add_argument("direction", nargs="?", default="up",
                    choices=["up", "down", "left", "right"])
    sp.add_argument("--coords", nargs=4, type=int, metavar=("X1", "Y1", "X2", "Y2"))

    sp = add("type", cmd_type, "type into the focused field")
    sp.add_argument("text")
    sp.add_argument("--clear", action="store_true")

    sp = add("press", cmd_press, "press a key: home back enter recent volume_up ...")
    sp.add_argument("key")

    sp = add("shell", cmd_shell, "run an adb shell command")
    sp.add_argument("command", nargs="+")
    sp.add_argument("--timeout", type=int, default=60)

    sp = add("launch", cmd_launch, "open an app by package name")
    sp.add_argument("package")
    sp.add_argument("--stop-first", action="store_true")

    sp = add("current", cmd_current, "which app is in the foreground")
    sp.add_argument("--json", action="store_true")

    sp = add("apps", cmd_apps, "list installed apps")
    sp.add_argument("--system", action="store_true", help="include system apps")

    sp = add("state", cmd_state, "screenshot + UI tree + app as JSON")
    sp.add_argument("--max-nodes", type=int, default=250)
    sp.add_argument("--no-image", action="store_true")

    sp = add("agent", cmd_agent, "drive the phone from a natural-language goal")
    sp.add_argument("goal")
    sp.add_argument("--max-steps", type=int, default=10)
    sp.add_argument("--max-nodes", type=int, default=200)
    sp.add_argument("--provider", help="module.path:callable, else GROQ/OPENAI key")
    return p


def main(argv: Optional[List[str]] = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        return args.func(args)
    except KeyboardInterrupt:
        return _fail("interrupted", 130)
    except AndroidCtlError as exc:
        return _fail(str(exc))


if __name__ == "__main__":
    raise SystemExit(main())
