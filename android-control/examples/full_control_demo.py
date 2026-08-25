#!/usr/bin/env python3
"""Full-control demonstration.

Shows every capability you asked for against a real phone:

    screenshots · UI tree · tap / swipe / type · app launch · shell · multi-device

Usage
-----
    # from the android-control/ directory, with the venv active:
    python examples/full_control_demo.py                 # auto-pick the only device
    python examples/full_control_demo.py SERIAL          # a specific one
    python examples/full_control_demo.py --dry-run       # no phone needed: fake transport

``--dry-run`` runs the exact same code path against an in-process fake device,
so you can see the whole flow (and CI can assert on it) without hardware.
"""

from __future__ import annotations

import argparse
import json
import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

OUT_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "output")


# ---------------------------------------------------------------------------
# optional fake transport for --dry-run
# ---------------------------------------------------------------------------
def _fake_device(serial: str):
    """Real AndroidDevice, fake transport -- exercises the genuine code path."""
    from PIL import Image

    from androidctl import AndroidDevice
    sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "tests"))
    from test_androidctl import FakeU2      # reuse the test double

    fake = FakeU2(serial)
    # Give it a real PIL image so screenshot()/save()/b64 paths run for real.
    fake.screenshot = lambda *a, **k: Image.new("RGB", (1080, 2340), "#101820")
    return AndroidDevice(fake, serial=serial)


def section(title: str) -> None:
    print("\n" + "=" * 72)
    print(f"  {title}")
    print("=" * 72)


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("serial", nargs="?", default=None,
                    help="device serial (omit to auto-detect a single device)")
    ap.add_argument("--dry-run", action="store_true",
                    help="run against a fake device (no phone / no adb needed)")
    ap.add_argument("--no-launch", action="store_true",
                    help="skip the app-launch section")
    args = ap.parse_args()

    os.makedirs(OUT_DIR, exist_ok=True)

    # ------------------------------------------------------------------
    # 1. DISCOVERY -- what is plugged in?
    # ------------------------------------------------------------------
    section("1. Device discovery (adb)")
    from androidctl import find_adb, adb_version, list_devices
    print("adb binary :", find_adb())
    print("adb version:", adb_version().splitlines()[0])

    if args.dry_run:
        print("\n[dry-run] using the in-process fake transport")
        devices = [_fake_device("FAKE0001")]
    else:
        found = list_devices()
        if not found:
            print("\nNo devices found.\n"
                  "  USB : plug in, enable Developer Options > USB debugging,\n"
                  "        accept the RSA prompt, then re-run.\n"
                  "  WiFi: adb tcpip 5555 && adb connect <phone-ip>:5555\n"
                  "See README.md for the full walkthrough.")
            return 1
        print(f"\n{len(found)} device(s):")
        for d in found:
            print(f"  {d.serial:28s} state={d.state:12s} model={d.model} "
                  f"transport={'usb' if d.is_usb else 'wifi'}")

        from androidctl import connect
        devices = [connect(args.serial)]

    # ------------------------------------------------------------------
    # per-device demo
    # ------------------------------------------------------------------
    for dev in devices:
        section(f"2. Device info  [{dev.serial}]")
        print(json.dumps(dev.summary(), indent=2, default=str))

        # ---------------- screenshots ----------------
        section("3. Screenshot")
        shot = os.path.join(OUT_DIR, f"{dev.serial}_screen.png")
        img = dev.screenshot(shot)
        print(f"saved {shot}  ({img.size[0]}x{img.size[1]} px)")
        print(f"base64 length for a vision model: {len(dev.screenshot_b64())} chars")

        # ---------------- UI tree ----------------
        section("4. UI tree (compact, LLM-friendly)")
        tree = dev.ui_tree()
        print(f"package={tree.package}  activity={tree.activity}  nodes={len(tree.nodes)}")
        print("-" * 72)
        print(tree.to_text(max_nodes=25))
        print("-" * 72)
        print(f"raw XML would be {len(dev.ui_dump())} bytes; "
              f"compact form is {len(tree.to_text())} bytes")

        interactive = tree.interactive()
        print(f"\n{len(interactive)} interactive elements. First 5:")
        for n in interactive[:5]:
            print(f"  [{n.node_id}] {n.short_class:14s} {n.label!r:24s} center={n.center}")

        # ---------------- tap / swipe / type ----------------
        section("5. Input: tap / swipe / type")
        w, h = dev.window_size
        print(f"screen is {w}x{h}")

        print(f"tap centre            -> ({w//2}, {h//2})")
        dev.tap(w // 2, h // 2)

        print("tap by percent (0.5, 0.9)  -- resolution independent")
        dev.tap_percent(0.5, 0.9)

        if interactive:
            target = interactive[0]
            print(f"tap element [{target.node_id}] {target.label!r} at {target.center}")
            dev.tap_element(target.node_id)

        print("swipe up (scroll down the list)")
        dev.swipe_direction("up")
        dev.wait_idle(0.5)

        print("long-press centre for 0.8s")
        dev.long_press(w // 2, h // 2, duration=0.8)

        print("type text into the focused field")
        dev.type_text("hello from androidctl", clear=True)

        print("press home")
        dev.home()
        dev.wait_idle(0.5)

        # ---------------- shell ----------------
        section("6. Shell (non-root)")
        for cmd in ("getprop ro.product.model",
                    "getprop ro.build.version.release",
                    "dumpsys battery | head -5",
                    "pm list packages -3 | head -5"):
            res = dev.shell(cmd)
            first = res.output.strip().splitlines()[0] if res.output.strip() else ""
            print(f"  $ {cmd}\n    -> exit={res.exit_code} ok={res.ok} | {first[:70]}")

        # ---------------- app launch ----------------
        if not args.no_launch:
            section("7. App launch")
            print("launching com.android.settings ...")
            info = dev.launch("com.android.settings", stop_first=True)
            print(f"  foreground now: {info.get('package')} / {info.get('activity')}")
            dev.wait_idle(1.0)
            dev.screenshot(os.path.join(OUT_DIR, f"{dev.serial}_settings.png"))
            print("  saved a screenshot of the launched app")

            print("opening a deep link ...")
            dev.open_url("https://example.com")
            dev.wait_idle(1.0)

            print("installed third-party apps:")
            for pkg in dev.list_apps()[:8]:
                print(f"    {pkg}")

            print("back to home")
            dev.home()

        # ---------------- full agent step ----------------
        section("8. One-shot 'agent step' (what an LLM loop would call)")
        state = dev.screen_state(max_nodes=12)
        print(f"app          : {state['app']}")
        print(f"window_size  : {state['window_size']}")
        print(f"ui_tree      : {len(state['ui_tree'])} chars")
        print(f"screenshot   : {len(state['screenshot_png_b64'])} chars of base64 PNG")
        print("\nfirst lines of the tree handed to the model:")
        print("\n".join("    " + ln for ln in state["ui_tree"].splitlines()[:6]))

    # ------------------------------------------------------------------
    # 9. multi-device
    # ------------------------------------------------------------------
    section("9. Multi-device (parallel fan-out)")
    if args.dry_run:
        print("[dry-run] skipped -- attach 2+ devices to exercise this for real")
    else:
        from androidctl import DeviceManager
        mgr = DeviceManager()
        print(f"{len(mgr)} device(s) ready: {mgr.serials}")
        results = mgr.parallel(lambda d: {
            "model": d.shell("getprop ro.product.model").output.strip(),
            "android": d.shell("getprop ro.build.version.release").output.strip(),
            "app": d.current_app().get("package"),
        })
        for serial, data in results.items():
            print(f"  {serial:28s} -> {data}")

    section("Done")
    print(f"artifacts in {OUT_DIR}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
