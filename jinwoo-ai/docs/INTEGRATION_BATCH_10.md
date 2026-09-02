# Controlled Integration Batch 10 — Desktop Assistant and Hand-Gesture Safety Intake

**Status:** the owner-requested
[Jarvis One-Click Setup](https://github.com/Gauravsachdeva23e/Jarvis-One-Click-Set-Up)
and
[Control PC Using Hand Gesture](https://github.com/Gauravsachdeva23e/Control_pc_using_Hand-Gesture)
repositories are represented as **source-review-required, non-executing
interaction contracts**. Their source code, models, setup flows and runtimes are
not integrated into Jinwoo.

Batch 10 updates the existing mobile-friendly Interaction Lab so the desktop
assistant and hand-gesture lanes are visible with their actual locked state. It
adds no webcam, input control, installer, process, provider, browser, audio,
model, desktop or device capability.

Jinwoo Native remains the canonical mission engine. It retains policy,
Planner → Executor → Verifier controls, explicit approval, privacy,
selected-workspace confinement and redacted local-audit ownership.

## Source review record

Only GitHub public metadata, recursive tree metadata, licence locations,
manifest contents and high-level static source structure/import/capability
signatures were reviewed on **2026-09-03**. No repository was cloned, no archive
was unpacked, and no upstream script, installer, model, media file, dependency,
provider, command, browser, camera, input route or executable was run.

| Adapter ID | Upstream review commit | Licence result | Static review highlights | Jinwoo owner | Current state |
| --- | --- | --- | --- | --- | --- |
| `jarvis-one-click-setup` | `5242523130ede73426e9e90a8576b89fd24670f4` | **Unverified for root:** no root `LICENSE` was found. A nested `agent-starter-react/LICENSE` contains MIT text, but does not grant reuse of the Jarvis root, CLI or Python content. | Installer/batch/bootstrap paths; LiveKit, providers, voice/media, MCP, memory, web request/search, window/file and process surfaces; bundled media and compiled caches. | Nox | **Source review required; execution disabled** |
| `pc-hand-gesture-control` | `391a0b0561d11bd3722bd774d4d7fe22fb8bfdb2` | **Unverified:** no repository `LICENSE` or verified reuse grant found. | OpenCV/MediaPipe camera and hand tracking, bundled `hand_landmarker.task` model, PyAutoGUI pointer control, and committed compiled caches. | Nox | **Source review required; execution disabled** |

### Jarvis One-Click Setup review

The root tree contains a Windows batch launcher, a CLI bootstrap path, Jarvis
Python sources and a nested React starter. Its reviewed dependency manifests
name LiveKit agent/client/server packages, Google/OpenAI/Silero/noise-cancellation
plugins, `python-dotenv`, web requests, Mem0, MCP, Next.js and related media/UI
packages. Static imports/signatures identify provider/network, voice/audio,
camera/video UI, browser/setup, MCP/external-tool, file/window and
subprocess/process-launch surfaces.

The tree also contains a roughly 9 MB media file named as an API-key tutorial and
compiled Python cache files. The static secret scan found no credential literal
according to the limited patterns used, but that result is not a licence grant,
security approval or assurance that configuration/media is safe to redistribute.

The nested starter's MIT text is deliberately treated as **subtree-scoped only**.
It does not license the unlicensed root code, its setup scripts, Jarvis Python
components, bundled configuration expectations or associated assets.

### Control PC Using Hand Gesture review

The tree contains Python camera/tracker/controller code, compiled Python caches
and a roughly 7.8 MB `hand_landmarker.task` model artifact. Its reviewed
requirements list `opencv-python`, `mediapipe`, `numpy` and `pyautogui`.
Static imports/signatures identify frame capture, hand/gesture processing and
mouse/pointer control.

Even if a future source licence became available, webcam-derived hand data,
accessibility/input permissions, model provenance, OS integration, accidental
click risk, emergency stop, data retention and accessibility safety would each
need separate review. No capture or input capability is appropriate for Jinwoo
V1.

## What Batch 10 implements locally

- `GET /api/frameworks` exposes two registry records:
  `jarvis-one-click-setup` and `pc-hand-gesture-control`.
- Both records are `source-review-required`, `reference-only` at their activation
  boundary and `execution_enabled: false`.
- Their dry runs remain bounded to three proposed Planner/Executor/Verifier roles
  and always report `external_runtime_invoked: false`.
- `POST /api/control/review` adds
  `batch-ten-desktop-gesture-safety`, which fails if either record is missing,
  changes status/boundary, or becomes executable.
- The existing Interaction Lab clearly shows **Camera off**, **Pointer locked**,
  **No setup script** and **No physical action**, together with the relevant
  source-review status badges. Its layout remains responsive on narrow screens.
- `scripts/check_safe_intake.py` now covers the Batch 07–12 clean-room
  surfaces, including the Batch 10 Interaction Lab. It rejects reviewed
  gesture/assistant runtime modules and manifest packages from Jinwoo's
  implementation until a separate activation review deliberately changes the
  guard.

## Explicitly excluded capabilities

Jinwoo does **not** copy, bundle, install, import, invoke or redistribute:

- Jarvis root/CLI/Python code, batch files, bootstrap logic, prompts, configuration,
  media, compiled cache, nested starter code or dependencies;
- any assistant installer, package install, one-click launch, shell/process,
  file opener, window manager, web search/request, browser, provider, credential,
  memory sync, MCP/external-tool or messaging route;
- voice, microphone, audio playback/capture, video, camera, screen, model,
  LiveKit session, transcription or media retention path;
- hand-gesture Python code, OpenCV/MediaPipe/PyAutoGUI dependencies, compiled
  caches, `hand_landmarker.task`, webcam capture, hand/biometric data,
  pointer/mouse/keyboard event, OS/window, device or accessibility control; or
- automatic upload, send, delete, workspace write, desktop action or physical
  action.

## Required activation gate

Neither upstream lane can move beyond a declarative contract until all applicable
conditions are satisfied:

1. Obtain and document an exact, compatible source licence/reuse grant for the
   pinned revision and every intended source subtree, model, asset and dependency.
2. Remove compiled artifacts, tutorial media, opaque models, upstream config and
   credential assumptions from the proposed intake; perform supply-chain and
   provenance review.
3. Define one narrow, original Jinwoo adapter with typed input/output, explicit
   data scope, local/offline test coverage, time/size/rate limits, disable path
   and visible stop control.
4. Keep provider/network, setup/package, shell/process, browser, voice/audio,
   screen/camera and desktop/device permissions off by default.
5. Before any camera or gesture experiment, require revocable in-app consent,
   visible capture indicator, local-processing evidence, strict retention rules,
   false-positive/fail-safe testing, accessibility review, per-action target
   preview and an immediately effective emergency stop.
6. Before any desktop action, use a disposable sandbox with no host credentials,
   no default network, no default workspace write, no automation persistence and
   an explicit Jinwoo approval for every impactful step.
7. Preserve the selected-workspace boundary, Planner → Executor → Verifier
   oversight and redacted audit controls. No external framework or assistant may
   bypass Jinwoo's canonical control plane.

## Final boundary

Batch 10 is a **safety intake and original status-UX update only**. It does not
turn Jinwoo into a one-click installer, voice assistant, camera tracker,
hand-gesture controller, mouse/keyboard controller, browser agent, MCP client,
provider runtime, desktop controller or hardware/device automation application.
