# android-agent — OpenDroid + Toni

You gave me eight repos and asked which one to integrate, how to build the APK,
and to get the mobile pet running. Here is all three.

```
android-agent/
├── opendroid/          cloned base app (gitignored — it is upstream's 31 MB)
├── pet/                Toni, the floating pet  ← my work
│   ├── ToniPetView.kt        Canvas-drawn animated companion
│   ├── ToniPetController.kt  overlay window: drag, tap, minimize
│   ├── ToniPetBridge.kt      wires her to OpenDroid's AgentState
│   ├── install.sh            copies the three files into opendroid/
│   └── APPLY.md              the 3-edit wiring change
└── README.md           this file
```

---

## 1. The eight repos, and which one to use

I cloned and inspected all eight. They are **not** interchangeable — three are
installable Android apps, five are PC-side frameworks that drive a phone over
ADB and can never produce an APK.

| Repo | Stars | What it actually is | Can it be an APK? |
|---|---|---|---|
| **yashab-cyber/opendroid** | 930 | **On-device autonomous Android agent.** Kotlin, 283 files, clean architecture, AccessibilityService, Room, Hilt, voice, planning. Apache-2.0. Pushed 2026-08-23. | **✅ yes — this is it** |
| eggbrid2/mobileClaw | 372 | Kotlin app, but the current release is an **AI arena social game** (models bluff/vote/eliminate each other). Not a phone agent. MIT. | ✅ but wrong app |
| orailnoor/private-agent | 282 | **Flutter/Dart** app (11 manifests are Flutter plugin shells). Rewriting it means switching your whole stack to Dart. No licence file. | ✅ but Flutter |
| callstack/agent-device | 4,205 | **TypeScript framework** (2,900 `.ts` files) + helper app. Node-driven device automation. MIT. | ⚠️ helper app only |
| droidrun/mobilerun | 9,112 | **Python** agent framework, runs on a PC. MIT. | ❌ |
| minitap-ai/mobile-use | 2,783 | **Python** MCP-style phone control from a PC. Apache-2.0. | ❌ |
| zai-org/Open-AutoGLM | 26,078 | **Python** `phone_agent`, PC-side. Apache-2.0. Last push 2026-03-06 — six months stale. | ❌ |
| ghost-in-the-droid/android-agent | 318 | **Python** backend (232 files) + Docker + emulators. MIT. | ❌ |

### Recommendation: **opendroid**

It is the only one that is simultaneously (a) a real installable Android app,
(b) an actual autonomous agent rather than a game or a Flutter shell, and
(c) permissively licensed. And it is the only one whose architecture you can
extend without fighting it:

```
com/opendroid/ai/
├── accessibility/   OpenDroidAccessibilityService + node traversal
├── core/agent/      AgentLoop, AgentState (planning + execution)
├── core/llm/        provider abstraction
├── core/memory/     persistence
├── core/routine/    habit/routine detection
├── core/voice/      TTS, STT, wake word
├── data/            Room db, repositories
├── di/              Hilt modules
└── ui/              Compose screens
```

Already non-root: phone control goes through `AccessibilityService`, so no root,
no Shizuku requirement for the core path (Shizuku is present but optional).

**Why not mobileClaw**, since you listed it: I read the README. This release is
explicitly *"an AI arena… seat several AI roles… watch them talk, bluff, vote,
eliminate."* It is a spectator game about comparing models, not an agent that
does things on your phone. Different product.

**Why not private-agent**: it is Flutter. That is a legitimate app, but adopting
it means your Android work happens in Dart, and your Live2D/companion work from
earlier in this repo is Kotlin. Mixing them is worse than picking one.

---

## 2. Toni — the mobile pet

OpenDroid already has a floating button (`FloatingWidgetView`, an inner class of
the accessibility service, showing `R.drawable.bot` with a pulsing glow). Toni
replaces that static icon with an animated companion that reflects what the
agent is actually doing.

I wired her to OpenDroid's **real** `AgentState`, which is a sealed interface
with exactly seven members (verified in `AgentLoop.kt:69`):

| `AgentState` | Toni |
|---|---|
| `Idle` | relaxed, slow breathing, randomised blinks |
| `Thinking` | looks up, eyes narrow, faster bob |
| `Listening` | wide eyes, ears fully perked, green |
| `PlanProposed` | excited, big smile, pink, bouncing |
| `ExecutingPlan` | focused, determined, blue |
| `Speaking` | mouth animates in time with the reply |
| `Error` | grey, ears down, frown |

Design decisions worth knowing:

- **Canvas, no assets.** No PNGs, no Live2D, no licence, no download. She renders
  in the existing 72 dp overlay. There is a documented seam to swap in a
  `GLSurfaceView` + Live2D later without touching the controller or the wiring.
- **Kept their two-layer window trick.** OpenDroid uses a full-size
  `FLAG_NOT_TOUCHABLE` draw layer plus a smaller touchable layer, because a
  square window around a round icon swallows taps meant for the app underneath
  (their issue #107). I did not "simplify" that — it is load-bearing.
- **`TYPE_ACCESSIBILITY_OVERLAY`**, so **no `SYSTEM_ALERT_WINDOW` prompt** and no
  manifest change.
- **One `ValueAnimator`** drives bob, blink and mouth from a single clock, so the
  parts cannot drift out of phase and there is exactly one thing to cancel in
  `onDetachedFromWindow`.
- **Blinks are randomised** (1.8–5.0 s). A metronomic blink is the fastest way to
  make a character look mechanical.
- **Minimize** curls her into a sleeping ball with a drifting "z" — and while
  minimized she ignores agent state, because a sleeping pet that changes
  expression is a bug.

Install:

```bash
cd android-agent/pet
./install.sh                 # copies the 3 files into opendroid/
```

Then make the three edits in [`pet/APPLY.md`](pet/APPLY.md). They are additive
and the installer never touches OpenDroid's own sources — a blind `sed` on
someone else's service is how you get a build failure you cannot see.

---

## 3. How to build the APK

### The easy way: let GitHub build it (no local setup at all)

You do not need a JDK, Android SDK or Gradle on your machine. GitHub's
`ubuntu-latest` runners ship with the Android SDK preinstalled — which is exactly
why OpenDroid's own `android-ci.yml` has no `setup-android` step.

```bash
cd android-agent
./pet/install.sh              # copies Toni + the patcher + the workflow
cd opendroid
python3 pet/apply_patch.py .  # wires Toni in (anchor-verified, idempotent)
# commit and push to your fork, then:
#   GitHub -> Actions -> "Build APK (OpenDroid + Toni)" -> Run workflow
```

Download from the run's **Artifacts**: `toni-debug-apk` → `app-debug.apk`.
Add the four signing secrets and you also get `toni-release-apk`.

```bash
adb install -r app-debug.apk
```

Or on your own machine, one command:

```bash
android-agent/pet/build-apk.sh              # debug APK
android-agent/pet/build-apk.sh --release    # signed release
```

`build-apk.sh` checks JDK 21, finds or writes `local.properties`, installs Toni,
applies the patch, builds, and prints the APK path + sha256. It stops with a
specific message at the first thing that is wrong rather than failing deep inside
Gradle.

### The wiring is a script now, not three manual edits

`pet/apply_patch.py` replaces the hand edits in `APPLY.md`. It matters because
CI cannot do manual edits, and because a blind `sed` on someone else's service
produces a build failure you cannot see. So it:

- matches **code anchors**, not line numbers (line numbers drift)
- **verifies all three anchors before writing anything** — all-or-nothing
- is **idempotent** — re-running exits 0 with no change, so CI can always call it
- writes a `.kt.pre-toni` backup, and `--revert` restores from it
- supports `--check` to verify without touching the file

Verified against the real cloned file:

| Check | Result |
|---|---|
| `--check` on clean tree | all 3 anchors found, exit 0 |
| apply | 8 markers, braces **129/129** balanced, field inserted, exit 0 |
| correct symbol wired | `c.onTap = { openMainActivityAction() }` — read from their line 333, not guessed |
| re-apply | exit **0**, file byte-unchanged |
| `--revert` | 0 markers, braces back to **125/125**, **md5 identical to the original** |

Two bugs this caught in my own work, both fixed: I had guessed the tap symbol as
`launchMainScreen()` when the real one is `openMainActivityAction()`, and my
first `--revert` used a regex that deleted `addFloatingButton()` /
`removeFloatingButton()` without restoring them. A regex cannot un-replace code,
so revert now restores from the backup.

---


### Why the build has to happen somewhere else (proof)

This sandbox has **no JDK, no Android SDK, no Gradle, no kotlinc**. I did not
assume that; I tested every route:

| What I tried | Result |
|---|---|
| `java -version`, `javac`, `gradle`, `kotlinc` | all *command not found* |
| JDK 21 from `adoptium/temurin21-binaries` (GitHub) | URL resolved, but `release-assets.githubusercontent.com` → **SSL_ERROR_SYSCALL** |
| `services.gradle.org/distributions/gradle-9.7.0-bin.zip` | **HTTP 000** |
| AGP 9.3.1 from `dl.google.com/dl/android/maven2` | **HTTP 000** |
| AndroidX `core-ktx` from `dl.google.com/dl/android/maven2` | **HTTP 000** |
| `repo1.maven.org` (Maven Central) | **HTTP 000** |
| `apt-get install openjdk-17-jdk-headless` | `E: Unable to locate package` |

Only `github.com` (git clone) and `pypi.org` are reachable. **Google Maven being
blocked is fatal on its own** — every AndroidX artifact comes from there. So no
APK build is possible in this environment, for any Android project, not just this
one. Everything below is therefore instructions for *your* machine, taken from
OpenDroid's own `build.gradle` and `.github/workflows/android-ci.yml` rather than
guessed.

### Toolchain (exact, from their build files)

| Component | Version | Source |
|---|---|---|
| **JDK** | **21 — exactly** | `jvmToolchain(21)`, daemon pinned in `gradle/gradle-daemon-jvm.properties` |
| Gradle | 9.7.0 | wrapper, checksum-pinned |
| Android Gradle Plugin | 9.3.1 | root `build.gradle` |
| Kotlin | 2.4.0 | root `build.gradle` |
| Hilt / Room / KSP | 2.60.1 / 2.8.4 / 2.3.10 | root `build.gradle` |
| compileSdk / targetSdk | 36 | `app/build.gradle` |
| minSdk | **26** | `app/build.gradle` |
| applicationId | `com.opendroid.aiagent` | `app/build.gradle` |

JDK 21 is not a suggestion — their `docs/development_guide.md` says *"JDK:
Version 21 exactly"*, and the Gradle daemon is pinned to it. JDK 17 or 25 will
fail.

### Debug APK (fastest path, no signing)

```bash
# 1. JDK 21
sudo apt install openjdk-21-jdk          # or download Temurin 21
java -version                            # must print 21.x

# 2. Android SDK — easiest is Android Studio, or command-line only:
#    install "Android SDK Platform 36" and "Android SDK Build-Tools 36"
export ANDROID_HOME=$HOME/Android/Sdk
echo "sdk.dir=$ANDROID_HOME" > local.properties

# 3. build
cd opendroid
./gradlew assembleDebug --stacktrace
```

Output:

```
opendroid/app/build/outputs/apk/debug/app-debug.apk
```

Install:

```bash
adb install -r app/build/outputs/apk/debug/app-debug.apk
```

This is exactly what their CI runs (`android-ci.yml`:
`./gradlew testDebugUnitTest assembleDebug --stacktrace`).

### Release APK (signed, installable long-term)

OpenDroid **refuses** to sign a release with the debug key. From
`app/build.gradle`, a plain `assembleRelease` fails with a message telling you to
configure signing. You need all four things:

```bash
# 1. make a keystore (once — keep it safe, you cannot update the app without it)
keytool -genkeypair -v \
  -keystore opendroid-release.keystore \
  -alias opendroid \
  -keyalg RSA -keysize 2048 -validity 10000

# 2. put it at the PROJECT ROOT (it is gitignored by the *.keystore rule)
mv opendroid-release.keystore opendroid/

# 3. credentials in your PERSONAL gradle home — never the project's
#    gradle.properties, which is tracked in git
cat >> ~/.gradle/gradle.properties <<'EOF'
RELEASE_STORE_PASSWORD=your_store_password
RELEASE_KEY_ALIAS=opendroid
RELEASE_KEY_PASSWORD=your_key_password
EOF'

# 4. build
cd opendroid
./gradlew :app:assembleRelease --stacktrace
```

Output: `opendroid/app/build/outputs/apk/release/app-release.apk`

Property names are exact — `RELEASE_STORE_PASSWORD`, `RELEASE_KEY_ALIAS`,
`RELEASE_KEY_PASSWORD`, keystore at `<project root>/opendroid-release.keystore`.
They are read with `project.findProperty`, so environment variables also work and
are better for CI:

```bash
export ORG_GRADLE_PROJECT_RELEASE_STORE_PASSWORD=...
export ORG_GRADLE_PROJECT_RELEASE_KEY_ALIAS=opendroid
export ORG_GRADLE_PROJECT_RELEASE_KEY_PASSWORD=...
```

**Compile-checking release without signing** (their CI does this to exercise R8):

```bash
./gradlew :app:assembleRelease -PallowUnsignedRelease --stacktrace
```

That APK is **unsigned and not installable** — it only proves ProGuard/R8 passes.

### If you just want an APK without any of this

Their GitHub releases publish prebuilt, signed `app-debug.apk` and
`app-release.apk` with SHA-256 checksums (`RELEASE.md` lines 38–45). Download,
verify the hash, `adb install -r`. That gets you OpenDroid — but **not** Toni,
since the pet is local code. Build it yourself for that.

### Sideload onto the phone

```bash
adb install -r app-release.apk
# if it says INSTALL_FAILED_UPDATE_INCOMPATIBLE, an older differently-signed
# build is already installed:
adb uninstall com.opendroid.aiagent && adb install app-release.apk
```

Then: Settings → Accessibility → **OpenDroid** → enable. Toni appears once the
floating-button setting is on.

---

## 4. Verification status — read this

| Thing | Status |
|---|---|
| All 8 repos exist and clone | ✅ verified; sizes, languages, licences tabulated above |
| opendroid's `AgentState` members | ✅ read from `AgentLoop.kt:69` — 7 members, my `when` covers all 7 |
| opendroid's tap symbol | ✅ read from their line 333 — `openMainActivityAction()` (I had guessed wrong) |
| opendroid's build config | ✅ read from `app/build.gradle` + root `build.gradle` |
| Build commands | ✅ taken from `.github/workflows/android-ci.yml`, not invented |
| `pet/install.sh` | ✅ executed twice — copies 3 Kotlin files + patcher + workflow, rejects a bad target |
| `pet/apply_patch.py` full cycle | ✅ check → apply → re-apply → revert, all run; revert gives an **md5-identical** file |
| Patched file brace balance | ✅ 129/129 patched, 125/125 original |
| `build-apk.yml` | ✅ parses as YAML, 14 steps, every step has exactly one `run`/`uses` |
| `build-apk.sh` | ✅ `bash -n` clean; JDK version parser tested against 5 real version strings |
| Network blocker | ✅ re-tested this turn: gradle/google-maven/maven-central/release-assets all fail |
| **Kotlin compiles** | ❌ **not verified — no toolchain here** |
| **APK builds** | ❌ **not built here — impossible, see the proof above** |

Same caveat as the other Android code in this repo: the Kotlin is written against
APIs I read out of the actual sources, not from memory, but **not one line has
been through a compiler**. Budget for ordinary first-build friction — a missing
import, a Compose rename. The two edits in `APPLY.md` also need you to confirm
one symbol against your checkout: `launchApp()` in Edit 2 should be whatever
OpenDroid's existing tap target calls to open the main activity.
