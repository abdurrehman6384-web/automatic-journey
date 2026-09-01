# RGS AI — Consolidation & Delivery Plan

> **Scope boundary:** This document is the Android/RGS companion delivery plan.
> The desktop **Jinwoo AI / Shadow Army** hierarchy, architecture, safety rules,
> and three-phase roadmap are authoritative in
> [`JINWOO_SHADOW_ARMY_PLAN.md`](./JINWOO_SHADOW_ARMY_PLAN.md). In particular,
> use its final 15 commanders × 3 sub-departments × 10 agents model rather than
> inferring Jinwoo capacity from any earlier planning notes.

**Prepared:** 31 August 2026
**Language:** Roman Urdu / English technical terms

## 1. Goal

Ek **single, installable Android APK** deliver karna hai jisme:

- **RGS Core**: task-focused AI assistant;
- **Aira / Companion mode**: warm companion chat, memory, voice aur optional avatar;
- **phone assistance**: sirf user ke apne device par, explicit Accessibility permission aur confirmation ke sath;
- **stable UI, settings, logs aur release process** hon.

Phone control kabhi bhi lock/PIN bypass, hidden screen recording, ya silent destructive action ke liye design nahi hoga. Send, delete, payment, uninstall, factory-reset jaise actions ke liye in-app confirmation zaroori hogi.

---

## 2. Repository audit — kya already bana hua hai

Yeh repo abhi **ek app nahi**, balkay useful lekin alag-alag projects/packages ka collection hai:

| Item | Kaam | Recommended role |
|---|---|---|
| `rgs-ai-mobile.zip` | RGS AI ka most complete Kotlin + Compose mobile UI: chat, agents, settings, licensing, provider routing, vision/voice seams | **Recommended primary app base** |
| `android-app/` | Separate Kotlin companion prototype: memory, TTS/STT, overlay, Accessibility service, Live2D Java renderer | Is se selected companion/control modules migrate karne hain; poora project parallel nahin rakhna |
| `rgs-mobile-os-integration.zip` | Expo/React Native device-control bridge + OpenDroid reference code | Kotlin target ke liye reference only; RN bridge directly reuse nahi hoga |
| `rgs-live2d-integration.zip` | Native C++/JNI Live2D alternative + personas | Java Live2D route **ya** NDK route choose karna hoga — dono ek sath nahi |
| `android-agent/` | External OpenDroid app ke liye Toni pet patch | Separate fallback/prototype; RGS APK mein direct merge nahi |
| `android-control/` | Desktop Python/ADB control + MCP server | Optional desktop companion/developer tool; Android APK ke andar nahi |
| `ultron-*.zip` | Next.js web orb UI | Visual inspiration or future web dashboard only |
| `project.zip` | Existing Windows desktop Python project | Future desktop integration source, Android app ka direct module nahi |

### Recommended product decision

`rgs-ai-mobile.zip` ko main **RGS AI Mobile** base banaunga aur `android-app/` se useful pieces carefully migrate karunga:

1. RGS AI ka existing navigation, multi-agent UI, provider settings aur data layer retain;
2. companion mode ko ek normal, selectable RGS feature banaya jaye — second standalone APK nahi;
3. phone-control service ko Kotlin-native accessibility module ke taur par add kiya jaye;
4. Live2D ko optional enhancement rakha jaye, launch blocker nahi.

Is se duplicate manifests, duplicate Accessibility services, duplicate databases aur conflicting package names nahi banenge.

---

## 3. Real missing / blocking items

### Current Android companion prototype (`android-app/`)

| Priority | Missing item | Impact |
|---|---|---|
| P0 | `gradlew` aur `gradle/wrapper/gradle-wrapper.properties` absent hain | Standard reproducible build command nahi chal sakta |
| P0 | `app/proguard-rules.pro` referenced hai magar file absent hai | Release build fail ho sakta hai |
| P0 | Manifest `.proactive.BootReceiver` declare karta hai, class missing hai | Kotlin/Android build fail hoga |
| P0 | Live2D Core AAR, Cubism Framework aur licensed model absent hain | Existing Live2D build/run possible nahi |
| P1 | Settings/DataStore screen missing hai | Persona, provider, privacy, overlay aur opt-in controls change nahi ho sakte |
| P1 | Proactive scheduler missing hai | Boot receiver declared hone ke bawajood check-ins ka safe flow nahi |
| P1 | Automated tests absent hain | Parser, memory, emotion, action safety regressions pakray nahi jayenge |
| P1 | Provider UI/config missing hai | Client presently Groq preset aur build-time key par hard-coded hai |

### Integration decisions still needed

- Avatar: Live2D Java, Live2D NDK, orb/Canvas fallback, ya avatar-less v1.
- LLM: existing edge proxy, user-supplied API key, ya self-hosted/local backend.
- Licensing: HWID paid tiers v1 mein chahiye ya launch ke baad.
- Vision: real camera/screen context required hai ya phase 2.
- Existing external code: user jo naya zip/files add karega uska target module aur intended behaviour identify karna hoga.

---

## 4. Target architecture

```text
RGS AI Mobile APK
│
├── presentation/       Compose navigation, Home, Chat, Agents, Settings
├── assistant/
│   ├── core/           RGS task mode
│   ├── companion/      Aira persona, emotion, memory, proactive rules
│   └── tools/          structured tool intents + confirmation policy
├── data/
│   ├── local/          Room / DataStore, chat, memory, settings
│   └── network/        provider router + secure edge-proxy client
├── devicecontrol/      Accessibility service, UI-tree, allowed actions, audit log
├── voice/              explicit mic consent, STT/TTS, foreground state when needed
├── avatar/             Canvas/orb initially; optional Live2D implementation later
└── security/           secrets, consent state, license policy, privacy/export/delete
```

### Non-negotiable boundaries

- **LLM output never executes raw shell code.** It is parsed into a small allow-listed action schema.
- **High-impact actions require an explicit final confirmation** from the user in the current conversation/UI.
- **Accessibility, overlay, microphone, notifications, and screen capture are separate opt-ins.** Unrelated permissions are not requested at startup.
- **API secrets do not ship as permanent APK strings.** Preferred route is a rate-limited backend/edge proxy; local development can use a user-entered encrypted setting.
- **Memories are viewable, editable, exportable and deletable.** Sensitive values (passwords, tokens, OTPs) are not automatically stored.

---

## 5. Delivery roadmap

### Phase 0 — Scope lock and source intake

**Output:** one agreed product baseline and an integration map.

1. Confirm RGS AI Mobile as primary base (or choose another base).
2. Extract the selected source into a normal tracked Android project; archives stay as original backups.
3. Rename package/application IDs deliberately; do not leave `com.example` in a production build.
4. Inventory every newly supplied file: licence, dependencies, target package, and conflict risk.
5. Record the v1 feature list and defer non-essential modules.

**Exit check:** a clean tree has one clearly named primary Android application.

### Phase 1 — Make the base buildable

**Output:** reproducible debug APK baseline before feature merging.

1. Add/restore Gradle wrapper and complete build files.
2. Fix manifest/class/resource mismatches, including the absent BootReceiver path.
3. Add minimal ProGuard rules and debug/release signing documentation.
4. Add CI workflow for unit tests + debug APK artifact.
5. Build on Android Studio/GitHub Actions with the exact supported JDK/SDK.

**Exit check:** fresh clone → one documented command/workflow → debug APK.

### Phase 2 — Core RGS app and configuration

**Output:** usable chat app with durable settings.

1. Preserve existing RGS chat/agents/navigation UI.
2. Add DataStore-backed settings: mode (RGS/Aira), language, provider/proxy, model, TTS, theme, privacy and permissions.
3. Add provider health test, understandable network/error states, and no-key onboarding.
4. Keep provider routing behind one interface so GLM/Gemini/Groq/Mistral/custom proxy can change without UI rewrites.
5. Add local chat session and memory-management screens.

**Exit check:** app restarts without losing selected settings and handles no-network/no-key safely.

### Phase 3 — Assistant and companion behaviour

**Output:** two personalities with one safe tool layer.

1. Move Aira persona, emotion parsing, recall and transcript logic from the companion prototype.
2. Add RGS Core / Aira mode selector; changing persona must not change permissions or tool access.
3. Implement memory review, edit, export, clear-all and sensitive-memory filtering.
4. Add structured model output validation: reply, emotion, optional tool intent.
5. Add unit tests for parser, memory ranking, emotion decay, and malformed model replies.

**Exit check:** malformed model response cannot crash the UI or invoke a tool.

### Phase 4 — On-device assistance

**Output:** transparent, user-approved phone-control flow.

1. Add one Kotlin Accessibility service and clear setup/status UI.
2. Start with low-risk actions: read visible UI, open app, back/home, labelled tap, scroll, controlled text input.
3. Add action preview + final confirmation gate for send/delete/payment/install or other high-impact operations.
4. Add action history/audit log and a global “disable phone control” switch.
5. Test across at least one physical Android 12+ device and one emulator.

**Exit check:** user can see why a permission is needed, revoke it, and review what the assistant did.

### Phase 5 — Voice, avatar and overlay

**Output:** polished optional companion experience.

1. Make microphone/TTS opt-in and show listening state clearly.
2. Use a lightweight Canvas/orb fallback first so the app can ship without restricted Live2D files.
3. If Live2D is approved, add exactly one renderer path and obtain the licensed Cubism SDK + model outside Git.
4. Add overlay only after normal in-app chat works; it must have a visible stop/hide control.
5. Implement proactive check-ins only with opt-in, quiet hours, daily limit and notification channel.

**Exit check:** app works fully with avatar/overlay disabled.

### Phase 6 — Quality, privacy and release

**Output:** release candidate.

1. Add unit, repository/network and critical UI tests.
2. Add crash/error telemetry only after consent policy is decided.
3. Create privacy policy, Accessibility disclosure, data deletion flow and permissions rationale.
4. Test upgrade/migration paths, offline behaviour, rotation/backgrounding and permission denial.
5. Produce signed release APK/AAB and a release checklist.

---

## 6. Suggested v1 vs later

### Ship in v1

- RGS Core + Aira mode switch
- chat with reliable provider/proxy configuration
- local chat history and safe memories
- settings + permissions dashboard
- voice input/output (explicit consent)
- basic, confirmed accessibility actions
- Canvas/orb avatar fallback
- build/test/CI/release foundation

### Move to phase 2 / later

- paid HWID tiers and remote licence enforcement
- full Live2D model integration
- continuous screen capture or vision workflows
- wake word/background voice service
- desktop MCP/ADB linking
- advanced multi-agent autonomy
- proactive scheduled messages

This order gives a working product early and prevents Live2D assets, licenses or a complex automation layer from blocking the core app.

---

## 7. Inputs required from the owner

Before code is merged, provide/confirm:

1. **Primary base:** RGS AI Mobile (recommended), `android-app`, or OpenDroid + Toni.
2. **Brand values:** final app name, package ID, icon/logo, RGS/Aira naming.
3. **LLM route:** proxy URL/API contract, or chosen provider for development.
4. **Avatar decision:** no avatar/orb first, or licensed Live2D SDK/model files.
5. **Existing code to import:** upload/paste the zip/files and say what feature each should add.
6. **Release target:** personal sideload APK, Play Store, or both.

---

## 8. First implementation batch after approval

Once the primary base is confirmed, I will do this first:

1. create the single primary Android source tree from the selected base;
2. make its Gradle/manifest/project structure internally consistent;
3. implement the missing configuration/permission foundation;
4. add the safe action contract and tests;
5. integrate one feature at a time with a build/test checkpoint after each change.

No archive will be blindly copied over another project. Every merge will be mapped, reviewed and kept reversible.
