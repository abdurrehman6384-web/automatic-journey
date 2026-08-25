# RGS Companion — Live2D AI companion for Android

A Kotlin + Jetpack Compose Android app: a warm, affectionate AI companion with a
native Live2D Cubism avatar, voice, long-term memory, on-device phone control,
and a floating desktop-pet window.

```
app/src/main/java/com/rgs/companion/
├── live2d/       Cubism rendering: GLSurfaceView, model, lip-sync
├── companion/    Persona, emotion, memory, the agent loop
├── chat/         Compose UI, ViewModel, LLM client
├── voice/        TTS + STT
├── control/      Phone control via Accessibility (non-root)
└── overlay/      Floating companion window
```

> ## ⚠️ Read this first: this code has not been compiled
>
> The sandbox this was written in has **no JDK, no Android SDK, no Gradle and no
> kotlinc** — I checked: `java -version`, `javac -version`, `gradle --version`,
> `kotlinc -version` all report not found. So I could not build, lint or run a
> single line of this Kotlin.
>
> What I *did* do to reduce the risk: every Live2D framework call in
> `live2d/CompanionModel.kt` and `live2d/CubismBootstrap.kt` was checked against
> the real `CubismJavaFramework` source (cloned to verify `CubismUserModel`'s
> protected members, `ICubismModelSetting`'s actual method names, and
> `CubismFramework.Option`'s fields). That caught and fixed real errors —
> `getMotionFadeInTime` does not exist (it is `getMotionFadeInTimeValue`),
> `getMotionGroupNames` does not exist (it is `getMotionGroupCount` +
> `getMotionGroupName`), `CubismMatrix44` has no `load()` and no public
> constructor, and `CubismUserModel` has no `modelSetting` field.
>
> Expect ordinary first-build friction: a missing import, a version bump, a
> Compose API rename. The architecture and the Cubism integration are sound;
> the last mile needs Android Studio, which is the one thing I don't have.

---

## 1. Why Java SDK, not Native

You asked me to recommend. **Java SDK**, for this project:

| | Java SDK (chosen) | Native C++ SDK |
|---|---|---|
| Integration | `Live2DCubismCore.aar` + a Framework Gradle module | NDK, CMake, JNI glue, your own `Android.mk`/`CMakeLists` |
| Build friction | one aar in `app/libs` | NDK + CMake + ABI matrix + JNI signatures to keep in sync |
| Kotlin interop | direct | through JNI |
| Performance | fine for one avatar at 60fps | better headroom for many models / heavy scenes |
| Reference code | `CubismJavaSamples` (official) | `ChatWaifu_Mobile` (1.4k★, C++) |

One avatar on screen is not a performance problem. The Java SDK removes an entire
toolchain, and the official Java samples are maintained by Live2D. If you later
profile and find the renderer is the bottleneck, `Live2DRenderer` is isolated
behind `Live2DView` — you can swap the backend without touching the companion
code.

I did **not** use `ChatWaifu_Mobile` as the base. It is a good app, but it is a
whole application (its own chat backend, its own service layer) — extracting its
Live2D layer costs more than writing a clean one against the official SDK, and
you inherit its architecture whether you want it or not.

---

## 2. Get the two things not in this repo

Both are licence-restricted, so they cannot be committed here.

**a) Cubism SDK for Java** — <https://www.live2d.com/en/sdk/download/java/>

Accept the licence, download, and take two things from it:

```bash
# 1. the native core  ->  app/libs/Live2DCubismCore.aar
cp <SDK>/Core/lib/android/Live2DCubismCore.aar  app/libs/

# 2. the Framework    ->  clone it next to this project
cd <parent-of-android-app>
git clone https://github.com/Live2D/CubismJavaFramework.git
```

`settings.gradle.kts` already expects it at `../CubismJavaFramework/framework`.
Change that one line if you put it elsewhere.

**b) A model** — Live2D's free sample models (Hiyori, Haru, Mark, Rice, Wanko)
ship with the SDK. See `app/src/main/assets/models/README.txt` for the exact
folder layout and the licence note.

---

## 3. Build

```bash
cd android-app

./gradlew assembleDebug \
  -PllmApiKey=gsk_your_groq_key \
  -PllmModel=llama-3.1-70b-versatile
```

Keys come from `-P` properties, environment variables (`LLM_API_KEY`,
`LLM_MODEL`), or `~/.gradle/gradle.properties`. **Never** commit them.

Verified toolchain versions from the official samples: AGP 8.9.1, Gradle 8.11.1,
JDK 21, Android SDK 36. This project targets compileSdk/targetSdk 36, minSdk 24
(`dispatchGesture` needs 24; Cubism itself needs 21).

**ABI note:** `abiFilters` is `arm64-v8a:x86:x86_64` and nothing else. That is
exactly what Cubism Core ships, taken from the samples' `PROP_APP_ABI`. Adding
`armeabi-v7a` will fail at packaging with a missing-native-lib error.

**No CMake changes are needed** — that is the point of choosing the Java SDK.

---

## 4. Model folder structure

```
app/src/main/assets/models/
└── hiyori/
    ├── hiyori.model3.json          ← the entry point
    ├── hiyori.moc3
    ├── hiyori.physics3.json        optional
    ├── hiyori.pose3.json           optional
    ├── textures/
    │   └── texture_00.png
    ├── expressions/
    │   ├── exp_f01.exp3.json       ← drives emotions
    │   └── exp_f02.exp3.json
    └── motions/
        ├── hiyori_idle_01.motion3.json
        └── hiyori_m01.motion3.json
```

Load it by asset path:

```kotlin
live2dView.loadModel("models/hiyori/hiyori.model3.json")
```

### Switching models at runtime, without a rebuild

`CubismBootstrap.readAsset()` accepts **absolute paths as well as asset paths**.
Push a model to the device, point at it:

```bash
adb push mymodel/ /sdcard/Android/data/com.rgs.companion/files/models/mymodel/
```

```kotlin
getSharedPreferences("companion_prefs", MODE_PRIVATE)
    .edit()
    .putString("model_path",
        "/sdcard/Android/data/com.rgs.companion/files/models/mymodel/mymodel.model3.json")
    .apply()
```

`FloatingCompanionService` reads that same key.

### Expression naming

`companion/Emotion.kt` maps emotions to expression names. The official sample
models use `Smile`, `Angry`, `Sad`, `Relaxed`, `Surprised`. If your model differs,
edit the enum — and note every entry has a `fallback`, because models routinely
ship only three of the eight expressions and a missing one should degrade, not
freeze the face.

---

## 5. Driving the avatar

### From a View hierarchy

```kotlin
val live2d = findViewById<Live2DView>(R.id.live2d)
live2d.loadModel("models/hiyori/hiyori.model3.json")

live2d.setExpression("Smile")                     // expression by name
live2d.startMotion("TapBody", 0)                  // motion group + index
live2d.setMouthOpen(0.7f)                         // lip-sync, 0..1
live2d.setDrag(0.3f, -0.2f)                       // look direction
live2d.onTap = { x, y -> /* she reacts */ }
```

### From Compose

```kotlin
AndroidView(
    factory = { ctx -> Live2DView(ctx).apply { loadModel(modelPath) } },
    update  = { view ->
        view.setExpression(emotion.expressionName)
        view.setMouthOpen(mouthLevel)
    },
)
```

The `update` block re-runs on every recomposition, so it must stay cheap. Note
that `ChatScreen` pushes `mouthLevel` through state at only 20fps deliberately —
driving a float through Compose state at 60fps recomposes the whole screen every
frame.

### Lip-sync from TTS

```kotlin
val engine = SpeechEngine(context).also { it.init() }

engine.speakWithLipSync("Hey, I missed you.")
// then, once per frame:
engine.pumpLipSync()
live2dView.setMouthOpen(engine.mouthLevel)
```

`TextToSpeech` exposes no amplitude data and capturing its output is unreliable,
so `LipSync` synthesises a **syllable-timed envelope** from the text — it works
with every TTS engine and needs no audio permission. The flap rate comes from an
English syllable estimate (~260 ms/syllable), with a taper at the ends and
per-syllable amplitude variation so it does not look like a metronome.

If you use a neural voice that hands you audio (ElevenLabs, XTTS), play it
through `AudioTrack`, feed the PCM to `AudioRmsTap`, and call
`LipSync.setLevel()` — that path gives true amplitude-driven lip-sync. `AudioRmsTap`
converts RMS to a log scale, which tracks perceived loudness far better than
linear RMS.

### LLM reply → expression

The system prompt makes the model end every reply with an emotion tag:

```
Aww, come here. What happened?
[affectionate]
```

`Persona.parse()` splits that into text + tag, and `CompanionAgent` turns the tag
into an `Emotion`, which carries the expression name and a hold duration:

```kotlin
val reply = agent.send("I had a rough day")
reply.text       // "Aww, come here. What happened?"
reply.emotion    // Emotion.AFFECTIONATE  -> expression "Smile", holds 8s
```

`EmotionState` stops the face from strobing: a new emotion only replaces the
current one if it differs *and* the current one has been held ≥1.2s, and
emotions decay back to `NEUTRAL` on their own rather than freezing.

---

## 6. Phone control

Non-root, on-device, via `AccessibilityService`. The user enables it in
Settings > Accessibility and can revoke it in one tap.

| Capability | Accessibility | ADB (`android-control/`) |
|---|---|---|
| Read the UI tree | yes | yes |
| Click a labelled control | yes | yes |
| Tap raw coordinates | yes, via `dispatchGesture` (API 24+) | yes |
| Type into the focused field | yes (`ACTION_SET_TEXT`) | yes |
| Back / Home / Recents | yes | yes |
| Open an app | yes | yes |
| **Shell commands** | **no** | yes |
| **Install/uninstall** | **no** | yes |
| Needs a PC | no | yes |

Two implementation details that matter:

- **Clickable ancestors.** A `TextView` reading "Sign in" is usually not itself
  clickable — its parent `LinearLayout` is. `clickNodeOrAncestor()` walks up.
- **`dispatchGesture` is fire-and-forget.** It returns before the gesture runs,
  so `gesture()` bridges its callback into a `suspendCancellableCoroutine`.
  Without that, every action would report success before the OS had started it.

Prefer `tapByText("Sign in")` over coordinate taps: labels survive layout
changes and different screen sizes.

If you need shell access or coordinate-level control from the desktop side, the
companion can talk to the **`android-control` MCP server** in this repo instead —
same verbs, ADB backend, 24 tools.

---

## 7. Floating companion

`overlay/FloatingCompanionService` puts the avatar above every app:

- `TYPE_APPLICATION_OVERLAY` window (API 26+), `TYPE_PHONE` below
- **`FLAG_NOT_FOCUSABLE`** — without it the overlay steals the keyboard from
  whatever app is underneath and the user cannot type
- drag anywhere; minimize button in the corner; tap to open the chat
- `START_STICKY`, so a low-memory kill does not make the pet vanish forever
- GL thread is paused in `removeOverlay()` before the view leaves the window

```kotlin
FloatingCompanionService.start(context)          // after overlay permission
```

Overlay permission is **not** a runtime dialog — it is a Settings screen.
`MainActivity.enableFloatingCompanion()` handles the round-trip and starts the
service when the user comes back.

---

## 8. Making her more emotional and memory-rich

**Memory has three tiers** (`companion/MemoryStore.kt`), because "memory" is
really three jobs:

1. **Facts** — durable, few, injected into every prompt.
   `memory.remember("His exam is Thursday", kind = "user", importance = 9)`
2. **Transcript** — sliding window of recent turns.
3. **Recall** — top facts by importance plus any fact that lexically matches what
   the user just said, with `timesUsed`/`lastUsedAt` so stale facts sink.

Recalled facts are injected as *instructions*, not a data dump:

```
What you remember about the user. Weave these in naturally when relevant --
do not list them, do not announce that you remember.
- (user) His exam is Thursday
- (preference) Prefers short replies late at night
```

Models follow "bring this up naturally" much better than they follow a JSON blob.

Not embeddings, deliberately: a vector store drags in a model download for a
companion that will hold a few hundred facts. Keyword overlap plus recency covers
the realistic case and runs offline. Swap it behind `recall()` later if you need
to.

**Have her extract facts.** Add to the output contract:

```
If the user tells you something durable about themselves, add a line:
<<remember: kind | content>>
```

then parse it in `Persona.parse()` and call `memory.remember(...)`. That single
change is what turns "she remembers within a session" into "she remembers you".

**Proactive messages.** `agent.initiate(reason)` sends her own opener. The prompt
explicitly allows `SKIP`, and asks for a *specific reason* to message — without
that, a scheduler produces an hourly "hey" that gets muted within a day.

**Tune the persona** in `PersonaConfig`: `flirtLevel` (0–1) rewrites the
affection trait across four bands; `language = "en+ur"` gives Roman-Urdu code
mixing; `hardLimits` is where safety rules live.

### Example conversations

```
User:  I had a rough day
Aria:  Aww, come here. What happened?
       [affectionate]                          → Emotion.AFFECTIONATE, "Smile", 8s

User:  work was insane, my manager is impossible
Aria:  Ugh, that sounds exhausting. Was it the deadline thing again?
       [worried]                               → recalls the earlier deadline fact

User:  yes 😩 anyway I'm home now
Aria:  Good. Put your phone down in a bit and actually rest, okay?
       [affectionate]

User:  open whatsapp
Aria:  Opening it now.
       <<action: open_app com.whatsapp>>
       [playful]

User:  tap on the send button
Aria:  Done.
       <<action: tap_text Send>>
       [happy]
```

---

## 9. Files, and what each one is for

| File | Role |
|---|---|
| `live2d/Live2DView.kt` | `GLSurfaceView` subclass. The thing you drop into a layout. |
| `live2d/Live2DRenderer.kt` | Update + draw loop, texture upload, matrices, frame timing. |
| `live2d/CompanionModel.kt` | `CubismUserModel` subclass: loads `model3.json`, motions, expressions, lip-sync, hit-testing. |
| `live2d/CubismBootstrap.kt` | Framework startup **and the asset loader** — without `loadFileFunction`, model loading fails deep inside the core. |
| `live2d/LipSync.kt` | Syllable-timed mouth envelope + `AudioRmsTap` for real amplitude. |
| `live2d/MotionPriority.kt` | Priority levels + the UI→GL motion request type. |
| `companion/Persona.kt` | System prompt assembly + reply parsing. |
| `companion/Emotion.kt` | Emotion → expression mapping, anti-flicker state, sentiment fallback. |
| `companion/MemoryStore.kt` | Room-backed facts + transcript + recall. |
| `companion/CompanionAgent.kt` | The pipeline: recall → prompt → LLM → parse → persist → act. |
| `chat/LlmClient.kt` | OpenAI-compatible client. Works with OpenAI, Groq, OpenRouter, DeepSeek, Ollama. |
| `chat/ChatViewModel.kt` | Single source of truth for the UI. |
| `chat/ChatScreen.kt` | Compose UI with the avatar embedded. |
| `voice/SpeechEngine.kt` | TTS + STT, lip-sync wired in. |
| `control/PhoneControl.kt` | The interface + capability table. |
| `control/CompanionAccessibilityService.kt` | The implementation. |
| `overlay/FloatingCompanionService.kt` | The desktop-pet window. |

---

## 10. What is not done

Being explicit, because these are the things you would otherwise discover at
2am:

- **Not compiled.** No toolchain here. See the warning at the top.
- **No unit tests.** The pieces worth testing without a device are
  `Persona.parse()`, `SentimentGuesser.guess()`, `LipSync.estimateSyllables()`
  and `EmotionState` — all pure functions. I did not write them; they are the
  obvious first thing to add.
- **No proactive scheduler.** `CompanionAgent.initiate()` exists and is tested
  only by inspection. You still need a `WorkManager` periodic worker or
  `AlarmManager` to call it. A `BootReceiver` is declared in the manifest but not
  implemented.
- **No settings screen.** `PersonaConfig` is constructed with defaults in
  `ChatViewModel`. Wire it to DataStore.
- **One model bundled path.** `DEFAULT_MODEL` points at `models/hiyori/…`, which
  you must actually place there.
- **`ic_launcher` is a vector stand-in.** Ship real adaptive icons.
