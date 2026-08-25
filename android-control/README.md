# android-control

Deep Android device control + AI-agent tooling, bolted onto your **RASHEED / RGS**
Python desktop project. Non-root. Multi-device. Ships a Python API *and* an MCP
server.

```python
from androidctl import connect

d = connect()                       # the one phone you have plugged in
d.screenshot("screen.png")          # PIL image, also written to disk
print(d.ui_text())                  # compact, LLM-friendly UI tree
d.tap(540, 1200)                    # absolute px
d.swipe_direction("up")             # scroll
d.type_text("hello", clear=True)    # type into the focused field
d.launch("com.android.settings")    # open an app
print(d.shell("getprop ro.product.model").output)
```

---

## 1. What was in your project (and what that changed)

`project.zip` unpacks to `costem agent/{backend,frontend,main files}` — a
**Windows desktop** Python app: CustomTkinter + PyQt5 frontends, a
`backend/actions/` folder of 106 feature modules, Groq/OpenAI/Gemini routing in
`actions/ai_brain.py`, ChromaDB memory, `pyautogui`/`playwright` for desktop and
browser automation, `chromedriver.exe` and `run.bat` in the tree.

I grepped the whole backend for `adb|android|uiautomator|scrcpy`: **3 hits, all
irrelevant** (an "android studio" process-name mapping and a metasploit payload
string). There is no Android code, and no Kotlin/Java/Gradle file anywhere
(`find … -name '*.kt' -o -name '*.java'` returns 0).

That settles the architecture: **the phone is a target, your PC is the
controller.** Everything here runs on the desktop side over ADB and drives the
phone remotely. Nothing needs to be installed inside an Android app, and nothing
needs root.

---

## 2. Why `uiautomator2` (and when you would use `lamda` instead)

You ranked `firerpa/lamda` first. I checked it rather than assuming, and the
ranking should flip. Evidence, all from the clone in `vendor/lamda`:

| | `openatx/uiautomator2` | `firerpa/lamda` (now "FIRERPA") |
|---|---|---|
| Stars / pushed | 8,298 · 2026-08-07 | 8,228 · 2026-08-16 |
| PC-side client | PyPI, MIT | PyPI, MIT (`lamda 10.6`) |
| **On-device server** | **APK auto-pushed by the client, in the open repo** | **not in the repo** — `find -name '*.apk' -o -name '*.jar' -o -name '*.so'` returns nothing |
| How you get the server | happens automatically on first connect | download from `device-farm.com`, after accepting `DISCLAIMER.TXT` and "the entire application process" |
| Root | not required | `DISCLAIMER.TXT`: *"This service requires the device to have root access to run"* |
| Install cost | `pip install uiautomator2` | `pip install lamda` **plus** a closed binary you cannot audit |

The README badge says "root / non-root mode"; the disclaimer that governs the
download says root is required. When a licence document and a marketing badge
disagree, I plan around the licence document.

**Decision: `uiautomator2` is the primary backend.** It is fully open, installs
with one `pip` command, needs no root, self-installs its APK, and its API is
almost exactly the surface you asked for. `lamda` stays as a documented optional
upgrade for the day you need MITM capture, Frida, or virtual displays *and* you
have a rooted burner phone — see §8.

Also evaluated and rejected: `droidrun/mobilerun` (9,110★ but it is an
agent framework, not a device API — you would inherit its agent loop),
`ghost-in-the-droid/android-agent` (318★, same shape), `Steph-ux/android-mcp`
(0★, personal fork), `djcgh/AdbPhoneAgent` (13★, unmaintained since 2026-03).
`uiautomator2` is the dependency several of them sit on anyway.

---

## 3. Install

Verified on Python 3.11.2 / Debian bookworm.

```bash
cd android-control

python3 -m venv .venv
.venv/bin/pip install -r requirements.txt     # Windows: .venv\Scripts\pip
```

That is the whole install. `uiautomator2` pulls in `adbutils`, which **ships a
real platform-tools `adb` binary**, so you do not need the Android SDK:

```
$ .venv/bin/python -c "from androidctl import find_adb, adb_version; print(find_adb()); print(adb_version())"
/home/user/automatic-journey/android-control/.venv/lib/python3.11/site-packages/adbutils/binaries/adb
Android Debug Bridge version 1.0.41
Version 36.0.0-13206524
```

`find_adb()` resolution order: `$ADB_PATH` → `adb` on `PATH` →
`$ANDROID_HOME/platform-tools/adb` → the bundled `adbutils` binary. Override
with `export ADB_PATH=/path/to/adb` if you have your own.

### Verify without a phone

```bash
.venv/bin/python -m pytest tests/ -q          # 62 passed
.venv/bin/python examples/full_control_demo.py --dry-run
.venv/bin/python mcp_server.py --list         # tool_count: 24
```

`--dry-run` runs the *real* `AndroidDevice` code against an in-process fake
transport, so you can see the entire flow before a phone is anywhere near it.

---

## 4. Connect a real device

### 4a. USB (do this first)

1. **Phone** → Settings → About phone → tap **Build number** 7 times →
   "You are now a developer".
2. Settings → System → **Developer options** → enable **USB debugging**.
3. Plug in with a **data** cable (charge-only cables are the #1 cause of an
   empty `adb devices`).
4. Accept the **"Allow USB debugging?"** RSA prompt on the phone. Tick
   *Always allow from this computer*.
5. Check:

```bash
.venv/bin/python -c "from androidctl import list_devices; print(list_devices())"
# or directly:
.venv/lib/python3.11/site-packages/adbutils/binaries/adb devices -l
```

You want:

```
List of devices attached
R5CT30ABCD           device usb:1-2 product:a53xnaxx model:SM_A536B transport_id:3
```

`state=device` means good. `unauthorized` → look at the phone and accept the
prompt. `offline` → unplug, `adb kill-server`, replug.

**Linux extra step** — udev permission. Without it you get `no permissions`:

```bash
sudo tee /etc/udev/rules.d/51-android.rules >/dev/null <<'EOF'
SUBSYSTEM=="usb", ATTR{idVendor}=="<VENDOR_ID>", MODE="0666", GROUP="plugdev"
EOF
sudo udevadm control --reload-rules && sudo udevadm trigger
# then replug the phone
```

Find `<VENDOR_ID>` with `lsusb` (e.g. Samsung `04e8`, Xiaomi `2717`,
Google `18d1`, OnePlus/OPPO `2a70`).

**Windows extra step** — install the OEM USB driver, or the Google USB Driver
via SDK Manager. Then `adb devices` in `cmd`.

### 4b. WiFi / wireless ADB

**Android 11+ (no cable at all):**

1. Settings → Developer options → **Wireless debugging** → ON (same Wi‑Fi as PC).
2. Tap **Wireless debugging** → **Pair device with pairing code** → note
   `IP:PORT` and the 6-digit code.
3. Pair once, then connect:

```bash
ADB=.venv/lib/python3.11/site-packages/adbutils/binaries/adb
$ADB pair 192.168.1.50:37123          # the PAIRING port, enter the code
$ADB connect 192.168.1.50:40555       # the CONNECT port shown on the main screen
```

**Any Android version (one USB cable to bootstrap):**

```bash
$ADB -s R5CT30ABCD tcpip 5555         # phone switches to TCP mode
$ADB connect 192.168.1.50:5555        # then unplug the cable
```

**From Python** — this is the call to expose in your app's settings screen:

```python
from androidctl import DeviceManager
mgr = DeviceManager()
dev = mgr.connect_wifi("192.168.1.50", 5555)
print(dev.serial, dev.current_app())
```

Reconnect after the phone sleeps:

```python
from androidctl import connect_wifi, disconnect
disconnect("192.168.1.50:5555")
connect_wifi("192.168.1.50", 5555)
```

---

## 5. The API

### `androidctl.AndroidDevice`

| Method | What it does |
|---|---|
| `screenshot(path=None)` | PIL image; writes PNG if `path` given |
| `screenshot_b64()` / `screenshot_bytes()` | for a vision model |
| `ui_tree()` | parsed `UiTree` with `[id]` indexes |
| `ui_text(max_nodes=200)` | compact text tree — feed this to an LLM |
| `ui_dump()` | the raw XML, when you need everything |
| `screen_state()` | **screenshot + tree + current app in one call** |
| `tap(x, y)` / `click(x, y)` | absolute pixels |
| `tap_element(node_id)` | tap a tree node's centre — no coordinate guessing |
| `tap_percent(0.5, 0.9)` | resolution-independent |
| `long_press(x, y, duration)` | |
| `swipe(x1,y1,x2,y2)` / `swipe_direction("up")` | `up/down/left/right` |
| `type_text(text, clear=)` | fast-input IME, falls back to ADB broadcast |
| `press("home"\|"back"\|"enter"\|...)`, `home()`, `back()`, `enter()` | |
| `shell(cmd, timeout=60)` | → `ShellResult(output, exit_code, .ok)` |
| `launch(pkg, activity=, stop_first=)` / `stop(pkg)` | |
| `current_app()`, `list_apps()`, `app_info(pkg)` | |
| `install(apk)`, `uninstall(pkg)`, `open_url(url)` | |
| `wait_for(text=, resource_id=, timeout=)` | polls the hierarchy |
| `push()/pull()`, `set_clipboard()` | files |
| `.raw` | escape hatch to the underlying `uiautomator2.Device` |

> **Note:** `uiautomator2` 3.7 has **no `tap()`** — it is `click()`. The wrapper
> adds `tap()` as the primary name and keeps `click` as an alias, because `tap`
> is what you asked for and what everybody types.

### The UI tree, and why it matters

A raw `dump_hierarchy()` dump is enormous and mostly invisible scaffolding.
`ui_text()` compacts it to indexed, tappable lines:

```
screen: com.android.settings/.Settings  nodes=6 (showing 4)
  [1] TextView "Settings" rid=header clickable center=(120,180)
  [2] Switch "Wi-Fi toggle" rid=wifi_toggle clickable checked center=(970,300)
  [3] EditText "Password" rid=pw_field clickable password center=(540,450)
  [5] LinearLayout "Notifications" scrollable center=(540,1360)
```

On the demo fixture that is **2,439 bytes of XML → 341 bytes of tree (−86%)**,
and the saving grows with screen complexity. Two consequences for your agent:

- The `[id]` is a real node index. `d.tap_element(3)` resolves to exact centre
  coordinates — the model never invents pixels.
- Invisible (0×0) and `enabled=false` nodes are dropped, so the model is not
  offered things it cannot tap. Pass `include_all=True` to see them.

Search without rendering:

```python
tree = d.ui_tree()
tree.find(text="Sign in")
tree.find_one(resource_id="login_button").center     # (540, 1810)
tree.interactive()                                   # everything tappable
```

### The agent loop

`screen_state()` is the one call an LLM needs per step:

```python
state = d.screen_state(max_nodes=250)
# {"serial", "app": {package, activity}, "window_size",
#  "ui_tree": "<compact text>", "screenshot_png_b64": "<png>"}
```

```python
from androidctl import connect
from actions.ai_brain import MultiLLM        # your existing router

llm, d = MultiLLM(), connect()
goal = "Turn on Wi-Fi"

for step in range(10):
    state = d.screen_state()
    reply = llm.smart_ask(
        f"Goal: {goal}\n\nScreen:\n{state['ui_tree']}\n\n"
        "Reply with ONE action: tap <id> | swipe <dir> | type <text> | "
        "press <key> | launch <package> | done"
    )
    print(step, reply)
    if reply.startswith("done"):
        break
    verb, _, arg = reply.partition(" ")
    {"tap":    lambda a: d.tap_element(int(a)),
     "swipe":  lambda a: d.swipe_direction(a),
     "type":   lambda a: d.type_text(a, clear=True),
     "press":  lambda a: d.press(a),
     "launch": lambda a: d.launch(a)}.get(verb, lambda a: None)(arg)
```

---

## 6. Multi-device

```python
from androidctl import DeviceManager

mgr = DeviceManager()
print(mgr.serials)                    # ['R5CT30ABCD', '192.168.1.50:5555']

dev = mgr.connect("R5CT30ABCD")       # cached — one u2 session per serial
mgr.parallel(lambda d: d.screenshot(f"{d.serial}.png"))
print(mgr.broadcast(lambda d: d.shell("getprop ro.product.model").output))
print(mgr.summary())                  # one dict per device, for a UI listing
```

`parallel()` uses a thread pool (one worker per device); `broadcast()` is
sequential. Both capture per-device exceptions into
`{"serial": {"error": "..."}}` so one dead phone cannot take down a fleet run.
Connections are cached per serial and released with `mgr.disconnect()`.

Ambiguity is an error, not a guess: `connect()` with no serial raises
`MultipleDevicesError` if two or more phones are attached. Set
`ANDROID_SERIAL=R5CT30ABCD` to pin a default.

---

## 7. MCP server

24 tools over stdio, one per device action, each taking an optional `serial`.

```bash
.venv/bin/python mcp_server.py --list      # smoke test
.venv/bin/python mcp_server.py             # serve on stdio
```

```
android_list_devices   android_screen_state  android_screenshot     android_ui_tree
android_tap            android_tap_element   android_tap_text       android_swipe
android_scroll         android_type_text     android_press_key      android_launch_app
android_stop_app       android_list_apps     android_current_app    android_shell
android_find_element   android_wait_for      android_device_info    android_open_url
android_connect_wifi   android_long_press    android_screenshot_to_file  android_wake
```

Client config — see [`examples/mcp_config.json`](examples/mcp_config.json).
Absolute paths only; MCP clients do not inherit your shell's cwd.

```json
{
  "mcpServers": {
    "android-control": {
      "command": "/ABSOLUTE/PATH/TO/android-control/.venv/bin/python",
      "args": ["/ABSOLUTE/PATH/TO/android-control/mcp_server.py"]
    }
  }
}
```

| Client | Where it goes |
|---|---|
| Claude Desktop (macOS) | `~/Library/Application Support/Claude/claude_desktop_config.json` |
| Claude Desktop (Windows) | `%APPDATA%\Claude\claude_desktop_config.json` |
| Claude Desktop (Linux) | `~/.config/Claude/claude_desktop_config.json` |
| Cursor | Settings → MCP → Add, or `.cursor/mcp.json` in the project |
| Claude Code | `claude mcp add android-control -- <command> <args…>` |

Design notes:

- **Logs go to stderr.** stdout is the JSON-RPC wire; one stray `print` kills
  the session.
- **Errors are data, not exceptions.** With no phone attached, `android_tap`
  returns `{"ok": false, "error": "NoDeviceError: …", "hint": "Run `adb
  devices`…"}`. Verified live:

  ```json
  {"ok": false,
   "error": "NoDeviceError: No ADB device connected. Plug in a device over USB or run `adb connect <ip>:<port>` for WiFi.",
   "hint": "Run `adb devices`. Enable USB debugging, or `adb connect <ip>:5555` for WiFi."}
  ```

  A model can act on that; a stack trace it cannot.
- `android_screen_state` bundles screenshot + tree + app, which is one round
  trip instead of three.

---

## 8. Optional: the `lamda` backend

`AndroidDevice` is duck-typed — it only calls
`click / swipe / send_keys / screenshot / dump_hierarchy / shell / app_* / press
/ window_size / device_info` on whatever object you hand it. Swapping backends
is a one-class change:

```python
from androidctl import AndroidDevice
from lamda.client import Device as LamdaDevice        # host, port=65000

d = AndroidDevice(LamdaDevice("192.168.1.50", 65000), serial="pixel5")
```

Before you do: uncomment `lamda>=10.6` in `requirements.txt`, obtain the
on-device server from `device-farm.com` under its disclaimer, and read §2 —
that disclaimer states root is required. Worth it only for MITM capture,
bundled Frida, or virtual displays.

I have **not** written or tested a lamda adapter here: it needs a rooted device
running their closed server, which does not exist in this environment, and I
would rather hand you a documented integration point than code I could not run.

---

## 9. Wiring it into RASHEED

[`integrations/android_tool.py`](integrations/android_tool.py) matches the
module-level-function style of your existing `backend/actions/` modules
(`Alert.py`, `Battery.py`, …). Copy it in:

```bash
cp integrations/android_tool.py "<project>/costem agent/backend/actions/android_tool.py"
export ANDROIDCTL_HOME=/path/to/android-control     # Windows: set ANDROIDCTL_HOME=…
```

```python
from android_tool import PHONE, android_available, ANDROID_TOOLS

if android_available():
    android_launch("com.whatsapp")
    print(android_ui_tree())
    android_tap(540, 1200)
```

- `PHONE` is a **lazy, thread-safe proxy**: importing the module never touches
  adb, so your app still boots with no phone attached. It connects on first
  use, caches the session, and `PHONE.reset()` drops it.
- Every helper **returns a string instead of raising**, so a dead phone cannot
  crash your main loop.
- `ANDROID_TOOLS` is a ready-made tool list (`name` / `fn` / `description` /
  `args`) for `actions/executor.py` or `actions/agent_registry.py`.

Smoke check:

```bash
.venv/bin/python integrations/android_tool.py
# androidctl import : ok
# available         : False
# devices           : []
```

---

## 10. Production notes

**Reliability**
- uiautomator2 pushes an APK + starts an HTTP server on the phone. First
  `connect()` is slow (several seconds); it is cached afterwards. Do not connect
  per action.
- The server dies if the phone reboots or the app is swiped away. Wrap long
  runs in retry: catch `SessionBrokenError` / `UiAutomatorError`, call
  `PHONE.reset()`, reconnect.
- `dump_hierarchy()` on a huge list can take ~1s. Poll with `wait_for()` rather
  than tight-looping.
- Screen off → empty hierarchy. Call `d.wake()` first.

**Concurrency**
- One u2 session per serial. Never share one `AndroidDevice` across threads.
- `DeviceManager.parallel()` gives each device its own worker.
- One adb server per machine, shared by all clients — do not spawn several.

**Security**
- ADB is full shell as the `shell` user: it can read app data, install APKs,
  change settings. Treat `android_shell` as arbitrary code execution.
- Non-root `shell` cannot: read `/data/data` of other apps, modify
  `/system`, or inject into other processes.
- Wireless ADB is unencrypted on your LAN. Pair over a trusted network, or
  tunnel: `adb -s <serial> forward tcp:9008 tcp:9008`.
- Never wire raw `android_shell` to an LLM without an allowlist.

**Performance**
- Screenshot ≈ 100–300 ms, hierarchy dump ≈ 200 ms–1 s. `screen_state()` is the
  cheap combined call.
- Downscale screenshots before sending to a vision model; 1080×2340 PNGs are
  ~1.5 MB base64.

---

## 11. Troubleshooting

| Symptom | Fix |
|---|---|
| `adb devices` empty | data cable, not charge-only; USB debugging on; accept the RSA prompt |
| `unauthorized` | accept the prompt on the phone; tick *Always allow* |
| `offline` | `adb kill-server`, replug; or re-`adb connect` |
| `no permissions` (Linux) | udev rule from §4a, then replug |
| `device not found` on Windows | OEM USB driver / Google USB Driver |
| `AdbNotFoundError` | `export ADB_PATH=/path/to/adb`, or `pip install adbutils` |
| `MultipleDevicesError` | pass a serial, or set `ANDROID_SERIAL` |
| WiFi drops after a while | normal — phone power-saves. Re-`connect_wifi()` |
| Empty hierarchy | screen off or app still loading → `d.wake()`, `d.wait_idle(1)` |
| `type_text` inserts nothing | `d.raw.set_fastinput_ime(True)`; the ADB-broadcast fallback runs automatically |
| MCP client shows no tools | absolute paths in the config; run `mcp_server.py --list` to confirm |
| MCP session dies instantly | something is printing to stdout — logs must go to stderr |

---

## 12. Layout

```
android-control/
├── androidctl/                     # the wrapper package
│   ├── device.py                   # AndroidDevice — tap/swipe/type/screenshot/ui_tree/shell
│   ├── manager.py                  # DeviceManager — discovery, pooling, parallel fan-out
│   ├── hierarchy.py                # XML -> indexed, compact UI tree
│   ├── adb.py                      # adb discovery, `devices -l` parsing, USB/WiFi connect
│   └── errors.py
├── mcp_server.py                   # 24 MCP tools over stdio
├── examples/
│   ├── full_control_demo.py        # end-to-end demo (add --dry-run to run with no phone)
│   └── mcp_config.json             # Claude Desktop / Cursor config
├── integrations/
│   └── android_tool.py             # drop-in for backend/actions/
├── tests/                          # 62 tests, no hardware required
├── vendor/                         # uiautomator2 + lamda reference clones (gitignored)
└── requirements.txt
```

Re-clone the reference repos:

```bash
mkdir -p vendor && cd vendor
git clone --depth 1 https://github.com/openatx/uiautomator2.git
git clone --depth 1 https://github.com/firerpa/lamda.git
```

---

## 13. Verification status — read this

Run in this sandbox on 2026-08-24:

| Check | Result |
|---|---|
| `pytest tests/ -q` | **62 passed** (unit: hierarchy, device, manager, adb; e2e: MCP over real stdio JSON-RPC) |
| `mcp_server.py --list` | 24 tools registered |
| Live MCP handshake (`initialize` → `tools/list` → `tools/call`) | passed; `android_list_devices` returned `{"ok": true, "count": 0, "devices": []}` |
| `adb version` | `Android Debug Bridge 1.0.41 / 36.0.0-13206524`, daemon started |
| `examples/full_control_demo.py --dry-run` | full flow, wrote two real 12,667-byte PNGs |

**What could not be verified here:** no physical phone or emulator is attached
to this sandbox, so device-side behaviour — actual taps landing, real hierarchy
dumps, APK push, wireless pairing — is exercised only against a fake transport
that mirrors `uiautomator2`'s documented signatures (read off the installed
3.7.0 package, not from memory). Run
`examples/full_control_demo.py <SERIAL>` against a real phone before you trust
it in production. That is the one remaining step, and it needs hardware I do
not have.
