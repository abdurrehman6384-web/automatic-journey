# Wiring Toni into OpenDroid

Three edits to one file. Nothing else changes — no manifest edit, no new
permission, no Gradle change.

**Why no manifest change:** Toni is hosted by the existing
`OpenDroidAccessibilityService` and uses `TYPE_ACCESSIBILITY_OVERLAY`, which
needs no `SYSTEM_ALERT_WINDOW` grant. OpenDroid already declares that permission
and `BIND_ACCESSIBILITY_SERVICE`, and already registers the service.

Target file:
`app/src/main/java/com/opendroid/ai/accessibility/OpenDroidAccessibilityService.kt`

Line numbers are from the commit cloned on 2026-08-24 (`versionName 1.0.6`,
`versionCode 7`). Anchor on the code, not the number.

---

## Edit 1 — add the field (near line 60)

Find:

```kotlin
    private val serviceScope = CoroutineScope(Dispatchers.Main + SupervisorJob())
```

Add immediately after it:

```kotlin
    /** Toni, the floating pet. Null until the floating-button setting is on. */
    private var toni: com.opendroid.ai.pet.ToniPetBridge? = null
```

## Edit 2 — create her where the button was created (near line 159)

Find `refreshFloatingButtonVisibility()`:

```kotlin
    private fun refreshFloatingButtonVisibility() {
        if (showFloatingButtonSetting && !isDeviceLocked) {
            addFloatingButton()
        } else {
            removeFloatingButton()
        }
    }
```

Replace the body with:

```kotlin
    private fun refreshFloatingButtonVisibility() {
        if (showFloatingButtonSetting && !isDeviceLocked) {
            if (toni == null) {
                toni = com.opendroid.ai.pet.ToniPetBridge(
                    context = this,
                    agentState = agentLoop.agentState,
                    scope = serviceScope,
                    hostIsAccessibilityService = true,
                )
            }
            toni?.controller?.let { c ->
                c.onTap = { launchApp() }              // your existing tap action
                c.onLongPress = { triggerMicrophoneAction() }
            }
            toni?.start()
        } else {
            toni?.stop()
        }
    }
```

Two things to check against your copy:

- `launchApp()` — replace with whatever the current `TouchTargetView.performClick()`
  path calls. In `1.0.6` the tap target's `OnClickListener` opens the main
  activity; use that same call.
- `triggerMicrophoneAction()` already exists and is what the old long-press
  invoked, so that one is correct as written.

## Edit 3 — tear her down (near line 149)

Find `onDestroy()`:

```kotlin
        serviceScope.cancel()
        removeFloatingButton()
        instance = null
```

Change to:

```kotlin
        toni?.stop()
        toni = null
        serviceScope.cancel()
        removeFloatingButton()
        instance = null
```

`toni?.stop()` must come **before** `serviceScope.cancel()`: `stop()` cancels the
state-collection job, and cancelling the scope first would leave the pet's
animator running against a dead scope.

---

## Keeping the old button

The two are independent. `addFloatingButton()` / `removeFloatingButton()` still
work untouched, so you can ship Toni behind the same setting or add a second one.
If you want them mutually exclusive, add to Edit 2:

```kotlin
            removeFloatingButton()     // hide the plain icon while Toni is up
```

---

## Verify

```bash
./gradlew :app:assembleDebug
```

Then on the device: Settings → Accessibility → OpenDroid → enable, and turn on
the floating-button setting in OpenDroid. Toni should appear at the right edge,
roughly 55% down:

- idle → slow breathing, occasional blink
- give her a task → she looks up and narrows her eyes (`Thinking`), then focuses
  (`ExecutingPlan`)
- she answers → mouth animates (`Speaking`)
- long-press → starts listening (green, wide-eyed, ears up)
- if a step fails → grey, ears down, frown (`Error`)
- tap the arrow in her corner → she curls into a sleeping ball with a drifting "z"

---

## Swapping in Live2D later

`ToniPetController` only ever talks to a `ToniPetView`. To use a real Live2D
model, replace the `drawLayer` with a `GLSurfaceView`-hosted renderer and keep
the same three methods — `updateState(AgentState)`, `setMouthOpen(Float)`,
`minimized`. The controller, the bridge and the service wiring do not change.

The Live2D implementation I wrote for the other project in this repo
(`android-app/app/src/main/java/com/rgs/companion/live2d/`) drops in behind that
seam, but it needs `Live2DCubismCore.aar`, which is a licence-restricted
download. Toni needs nothing.
