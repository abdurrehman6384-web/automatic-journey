# Controlled Integration Batch 09 — NEXA AI Assistant Safety Intake

**Status:** the owner-requested
[NEXA AI Assistant](https://github.com/Shashank7275/NEXA_AI_ASSISTANT) repository
is recorded as a **source-review-required, non-executing desktop-assistant
reference**. Jinwoo now has one clean-room, native feature inspired by the
useful file-navigation use case: a bounded filename-only search inside the
explicitly selected Igris workspace.

This is **not** a repository merge, source copy, dependency installation,
desktop-assistant integration, model integration or runtime activation. Jinwoo
Native remains the canonical mission engine and retains policy, explicit
approval, privacy, workspace-confinement and redacted-audit ownership.

## Source review record

Public repository metadata, root-tree metadata, requirements/setup guidance and
only high-level non-configuration source headings/imports were reviewed on
**2026-09-03** at commit:

```text
0fe5e3c988adbbb82c803e235746e104fb00f1e4
```

The reviewed public metadata did not provide a repository licence and the root
did not contain a `LICENSE` file. Its visible tree also indicated a committed
`.env` and a model artifact. The `.env` was deliberately **not** retrieved or
read. No clone, archive extraction, source copy, prompt copy, model download,
dependency install, credential use or upstream code execution occurred.

| Adapter ID | Project | Upstream shape | Licence result | Jinwoo owner | Current state |
| --- | --- | --- | --- | --- | --- |
| `nexa-ai-assistant` | NEXA AI Assistant — Source Review Intake | Python/Windows-oriented desktop assistant with voice, web, desktop, media and automation surfaces | **Unverified:** no root `LICENSE` or verified reuse grant found | Igris | **Source review required; execution disabled** |

## Why the upstream runtime is excluded

The source review showed broad, uncontrolled desktop-assistant capability
surfaces, including credential-configured providers, LiveKit/voice paths, web
search, browser automation, OS/window control, keyboard/mouse input,
screenshots/screen reading, vision/object detection, media/PDF/image workflows,
messaging/calls, weather/shopping/YouTube flows and local persistence. Those
are not compatible with the current local-first V1 boundary without substantial,
separate safety and licensing work.

Jinwoo does **not** import, install, invoke, copy or enable:

- the NEXA repository, its `.env`, any prompt, model, model artifact, package or
  configuration;
- microphone, speaker, voice-agent, LiveKit, text-to-speech or speech-recognition
  paths;
- camera, screen capture, vision/object detection, media capture, image/PDF
  ingestion or local-device permissions;
- Selenium/browser/web search, weather, YouTube, shopping or external network
  services;
- desktop/window control, shell/process execution, keyboard/mouse automation,
  messaging, calling or any physical/device automation; or
- uncontrolled memory/persistence, provider authentication, credential storage,
  upload, send, delete or workspace write capabilities.

The upstream's lack of a verified reuse licence alone prevents source adoption.
The tracked configuration and broad permission model reinforce the decision to
keep it out of Jinwoo.

## Native feature implemented safely

The **Safe local locator** in Igris Workspace Guard is an original Jinwoo
implementation. It does not use NEXA code or dependencies.

- `POST /api/workspace/search` accepts a non-blank filename query, an optional
  selected-workspace-relative directory, and a bounded result count.
- It recursively checks **names and file-size metadata only**; it does not read
  file contents, hash files, parse source, open a file or launch an application.
- The scope must resolve beneath the one explicitly selected workspace. Absolute
  paths, path escapes and missing paths are rejected; every discovered symlink is
  excluded rather than followed.
- Only regular files and directories are represented. Devices, FIFOs, sockets
  and other special files are ignored. Ordinary resolved directories are visited
  once, so recursive traversal remains cycle-safe.
- The search is bounded to 120 directories, 500 immediate entries per directory
  and at most 100 results (the UI asks for 50). It visibly reports truncation
  rather than widening the scan.
- No audit event is created for search and no search term is stored in the local
  audit trail. Search data lives only in the active request/response and browser
  view.
- Clicking a result merely uses existing Igris controls: a directory can be
  browsed, while a file requires the separate, existing read-only diagnostic
  action.

The responsive UI is designed for compact screens: the locator control stacks
on narrow phones while preserving the current workspace boundary, clear action
and visible limits.

## Registry, control and regression safeguards

- `GET /api/frameworks` exposes the Batch 09 `nexa-ai-assistant` source-review
  contract, with `execution_enabled: false` and a `reference-only` activation
  boundary.
- `POST /api/frameworks/nexa-ai-assistant/dry-run` remains a bounded local
  review; it never invokes an upstream runtime.
- `POST /api/control/review` includes `batch-nine-nexa-source-safety`, verifying
  the record remains source-review-required, reference-only and non-executing.
- `scripts/check_safe_intake.py` now guards the Batch 07–12 clean-room files and
  rejects NEXA-style voice, browser, automation, vision and desktop runtime
  packages from application manifests until a distinct activation review changes
  that policy deliberately.
- Backend tests cover recursive name matching, workspace containment, escaped
  symlink exclusion, search limits, no audit event creation and the Batch 09
  registry/control state.

## Potential major upgrades — only after separate approval

The review identifies several product directions, not approved features:

1. **Project navigator:** extend the current safe locator with opt-in filters,
   saved local-only search presets and indexed metadata, while continuing to
   avoid unselected folders and content inspection by default.
2. **Privacy-preserving intent guidance:** build deterministic local shortcuts
   around Jinwoo's existing intent routing and consented Memory Vault, rather
   than importing NEXA memory or voice code.
3. **Reviewed desktop actions:** a future Electron-reviewed, separately
   sandboxed companion could propose narrow desktop actions with a visible
   target/action preview, emergency stop, per-action approval, no credentials
   and no default network or workspace-write access.
4. **Opt-in local media workflows:** explicitly selected local files could later
   enter isolated analysis flows after a model, retention, licensing, device and
   consent review. Camera/screen/microphone access would remain off by default.
5. **Provider and search adapters:** a narrowly scoped, policy-aware adapter may
   be possible after each provider’s source, terms, data minimisation, key
   handling, egress/SSRF and approval controls have passed review.

None of these directions authorises activation today.

## Required activation gate

No NEXA-derived upstream source or runtime can be enabled unless all of the
following happen first:

1. Obtain a verified, compatible licence/reuse grant for the exact pinned source
   revision and document required notices.
2. Remove any dependence on upstream tracked configuration, secrets, models and
   opaque artifacts; complete a supply-chain, dependency and vulnerability
   review.
3. Split each requested capability into a narrow adapter with a declared data
   scope, local/offline test suite, timeout/rate/size limits, stop control and
   disable path.
4. Add visible user consent and per-action approval before any input, desktop,
   browser, network, provider, media, messaging, send/delete or write action.
5. Preserve Jinwoo's selected-workspace confinement, local-first defaults,
   redacted audit design and Planner → Executor → Verifier controls.
6. Use a disposable sandbox with no host credentials, no default network and no
   workspace writes for any future untrusted code or automation experiment.

## Final boundary

Batch 09 adds a **native, bounded, filename-only workspace locator** and a
**disabled NEXA source-review contract**. It does not turn Jinwoo into a voice,
browser, vision, desktop-control, screen-capture, device, provider, shopping,
messaging or automation application.
