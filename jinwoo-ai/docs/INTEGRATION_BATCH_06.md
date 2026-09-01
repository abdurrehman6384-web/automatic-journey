# Controlled Integration Batch 06 — Gesture, Orb and Physical-Interaction Safety

**Status:** the owner-requested Barehands and Ultron Orb UI references, plus a
physical cutter/robotics concept, are registered as controlled, non-executing
capability contracts. This batch also adds an **original CSS-only Jinwoo command
orb** and an Interaction Lab UI. It does **not** copy upstream source code,
install a dependency, request camera access, load a CDN, start a local service,
or connect to a desktop, Android phone, physical tool or robotic device.

Jinwoo Native remains the sole mission engine. It owns mission state, approval,
privacy, user-selected workspace boundaries and redacted local audit records.
A Batch 06 record can prepare a bounded plan only; it cannot grant an interaction
runtime or physical-action right.

## Source review record

Repository metadata, root-tree/licence evidence and README documentation were
reviewed on **2026-09-02**. No repository was cloned, no archive was unpacked,
and no upstream code, script, package, asset or binary was executed. The observed
commits below are review references only, not installed dependency pins.

| Adapter ID | Project | Upstream source | Observed HEAD | Licence result | Jinwoo owner | Contract state |
| --- | --- | --- | --- | --- | --- | --- |
| `barehands` | Barehands Gesture Interface | <https://github.com/jaredrhod/barehands> | `eb23bed2d772f9d5a24de26fb92f46c3c76d69cf` | **AGPL-3.0-or-later** | Nox | **Licence review required; execution disabled** |
| `ultron-orb-ui` | Ultron Orb UI (Sagar Builds) | <https://github.com/SAGAR-TAMANG/ultron-by-sagar-builds> | `a65306f5a9568655551ec27445f773f20273223a` | MIT | Tusk | Contract-ready visual/interaction review; execution disabled |
| `physical-cutter-safety-intake` | Physical Cutter / Robotics Safety Intake | No source or machine selected | n/a | **Machine, controller and safety evidence required** | Nox | **Source review required; no device route exists** |

### Barehands boundary

Barehands describes a Chrome/webcam spatial board with hand tracking, external
MediaPipe and Three.js CDN loading, local state/configuration files, and local
board command protocols. Its AGPL-3.0-or-later licence requires a separate
compatibility, distribution and notice decision before any source, derivative,
service, package or runtime can be considered.

Therefore Jinwoo does **not** copy, bundle, link, install, run or invoke
Barehands. It does not request camera permissions; load MediaPipe/Three.js from
a CDN; read/write state or notes; call a localhost service; or use gesture
commands. Only high-level accessibility, consent and interaction-design
observations are represented.

### Ultron Orb UI boundary

The reviewed repository is an MIT-licensed Next.js/Three.js/MediaPipe hand
tracking interface. Its documentation references an Iron Man-inspired visual
style and an associated AI/device-control demonstration. Jinwoo does not copy
the Next.js, Three.js, MediaPipe or upstream UI implementation and does not use
third-party character, product, logo, voice or trade-dress assets.

The local `CommandOrb` component is independently written CSS/React UI. It is
only a visual readout for `ready`, `working` and `guarded` mission state. It does
not invoke `getUserMedia`, MediaPipe, Three.js, a camera, an Android device or an
autonomous controller.

### Physical cutter / robotics boundary

No machine make/model, manufacturer manual, controller protocol, firmware,
actuator, end effector, target material or lawful operating context was supplied.
The physical-cutter record therefore remains a source-intake safety boundary,
not an adapter. It cannot connect USB, serial, Bluetooth, Wi-Fi, GPIO, camera,
motor, blade, laser, actuator or industrial-control hardware.

Jinwoo cannot bypass a physical guard or interlock, move equipment, energise a
tool, instruct a device action, or perform a physical action. Any future work
must begin with the exact machine documentation, its intended lawful use, a
trained local operator, physical guarding, emergency stop, risk assessment and
independent safety sign-off.

## What is implemented locally

- `GET /api/frameworks` now exposes the three Batch 06 contracts with licence,
  source, owner, capability tags, safety boundary and disabled status.
- `POST /api/frameworks/{framework_id}/dry-run` can produce a bounded,
  non-executing plan for Barehands or Ultron UI. It returns
  `external_runtime_invoked: false` and appends interaction guardrails.
- The physical-cutter safety intake has no visible dry-run button in the UI,
  because no source or machine has been selected. Its API record remains a
  non-executing source-intake plan only.
- Native Control & Audit Review now verifies Batch 06 inventory and the
  AGPL/licence and physical-hardware source locks.
- The redesigned dashboard adds an Army Explorer, responsive command navigation,
  searchable Framework Registry, original status orb and Interaction Lab. These
  are presentation and planning features only.

## Interaction rules that remain locked

| Concern | Current rule |
| --- | --- |
| Webcam / microphone / screen capture | Off by default; no permission request or capture code in this batch |
| Hand tracking / gestures | Design and consent review only; no MediaPipe, camera loop or gesture action |
| Browser / CDN / localhost | No browser automation, CDN runtime loading or local-service call from Batch 06 |
| Desktop / Android | No desktop input, Android connection, Accessibility, screen capture or device command |
| Physical cutter / robotics | No controller, firmware, actuator, motor, blade, laser, serial, USB, Bluetooth, Wi-Fi or GPIO access |
| User data / workspace | No new file read/write, state file, notes vault, media or credential access |
| Autonomy | No background agent, scheduler, tool loop or physical action; every future impactful step needs separate approval |

## Required activation gate for any future interaction route

No gesture, camera or physical-device feature can move beyond a contract until
all applicable requirements are implemented and independently reviewed:

1. Exact upstream source/version and its licence/NOTICE obligations are resolved.
2. The interaction has a narrow typed contract and a user-visible action preview.
3. Camera/microphone/screen access is off by default and needs fresh, explicit,
   revocable in-app consent with a persistent visible capture indicator.
4. Processing, retention, storage, logging and outbound-transfer behaviour are
   documented; raw capture is minimised and never sent to an unapproved provider.
5. Gestures cannot silently trigger an impactful tool, file, browser, desktop or
   mobile action; a separate visible approval is required.
6. Any hardware proposal is reviewed against the exact machine manual,
   manufacturer limits, local legal requirements, trained-operator procedures,
   physical guarding, independent emergency stop and a documented risk assessment.
7. A physical device must be disconnected and fail safe by default; there must be
   no interlock bypass, autonomous motion, remote energisation or unattended run.
8. The implementation has local/offline tests, timeout/stop controls, a disable
   path, regression evidence and redacted audit records.

## Owner input needed for physical hardware

If you want a future **physical cutter/robotics safety-design review**, share
only non-sensitive product information: the exact machine model, manufacturer
manual URL/PDF, intended material/task, local operator role, country/site safety
requirements, and whether it is an existing certified machine. Do not share
access credentials, remote-control endpoints, keys, firmware passwords or a live
device connection.

## Final boundary

Batch 06 upgrades Jinwoo's visible command experience and records interaction
concepts. It does **not** activate camera, gesture, desktop, Android, browser,
service, hardware or physical-control capability.
