package com.rgs.companion.control

/**
 * What the companion can do to the phone.
 *
 * ## Why Accessibility and not ADB
 * ADB gives you real coordinate taps and shell access, but it needs a PC, a USB
 * cable or wireless debugging, and a user who has enabled Developer Options.
 * Accessibility runs entirely on-device, is granted through a normal Settings
 * screen, and can be revoked in one tap.
 *
 * **Capability boundary:** an `AccessibilityService` can click *nodes*, read the
 * tree, **and** inject gestures at arbitrary coordinates via
 * `dispatchGesture` (API 24+). What it still cannot do is run shell commands or
 * touch another app's private data. So:
 *
 * | Capability | Accessibility (this) | ADB (`android-control/`) |
 * |---|---|---|
 * | Read the UI tree | yes | yes |
 * | Click a labelled control | yes | yes |
 * | Tap raw coordinates | yes, via `dispatchGesture` (API 24+) | yes |
 * | Swipe at coordinates | yes, via `dispatchGesture` | yes |
 * | Type into the focused field | yes (`ACTION_SET_TEXT`) | yes |
 * | Back / Home / Recents | yes | yes |
 * | Open an app | yes | yes |
 * | Shell commands | **no** | yes |
 * | Install/uninstall apps | **no** | yes |
 * | Needs a PC | no | yes |
 *
 * Node-based clicking is still preferable to coordinate taps: labels survive
 * layout changes and different screen sizes, coordinates do not. Use
 * [tapByText] first and [tapAt] only when the target has no usable label.
 */
interface PhoneControl {

    /** Is control actually granted right now? */
    val isAvailable: Boolean

    /** Launch by package name, e.g. `com.whatsapp`. */
    suspend fun openApp(packageName: String): Boolean

    /** Find a visible node whose text matches and click it. */
    suspend fun tapByText(label: String): Boolean

    /**
     * Tap raw screen coordinates. Requires API 24+ and `canPerformGestures`
     * (some accessibility configurations disable gesture injection).
     */
    suspend fun tapAt(x: Float, y: Float): Boolean

    /** Swipe between two points, e.g. for a carousel with no scroll action. */
    suspend fun swipeAt(x1: Float, y1: Float, x2: Float, y2: Float,
                        durationMs: Long = 300): Boolean

    /** Type into the currently focused field. */
    suspend fun typeText(text: String): Boolean

    /** A compact dump of what is on screen, for the LLM to reason over. */
    suspend fun readScreen(): String

    suspend fun pressBack(): Boolean

    suspend fun pressHome(): Boolean

    /** "up" | "down" -- scrolls the focused scrollable container. */
    suspend fun scroll(direction: String): Boolean
}

/** Used when the user has not enabled the accessibility service yet. */
object NoOpPhoneControl : PhoneControl {
    override val isAvailable = false
    override suspend fun openApp(packageName: String) = false
    override suspend fun tapByText(label: String) = false
    override suspend fun tapAt(x: Float, y: Float) = false
    override suspend fun swipeAt(x1: Float, y1: Float, x2: Float, y2: Float, durationMs: Long) = false
    override suspend fun typeText(text: String) = false
    override suspend fun readScreen() = "phone control is not enabled"
    override suspend fun pressBack() = false
    override suspend fun pressHome() = false
    override suspend fun scroll(direction: String) = false
}
