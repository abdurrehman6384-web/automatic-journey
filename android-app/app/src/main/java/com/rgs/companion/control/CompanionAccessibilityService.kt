package com.rgs.companion.control

import android.accessibilityservice.AccessibilityService
import android.accessibilityservice.GestureDescription
import android.content.Intent
import android.graphics.Path
import android.os.Bundle
import android.util.Log
import android.view.accessibility.AccessibilityEvent
import android.view.accessibility.AccessibilityNodeInfo
import kotlinx.coroutines.suspendCancellableCoroutine
import kotlin.coroutines.resume

/**
 * Non-root phone control, mediated by the OS.
 *
 * The user enables this in Settings > Accessibility. Every grant is explicit and
 * revocable, which is the whole reason to prefer it over a root or ADB path in an
 * app other people install.
 *
 * A static [instance] is how the rest of the app reaches the service: Android
 * owns its lifecycle, so you cannot construct it yourself. [instance] is null
 * until the user enables it -- callers must check [PhoneControl.isAvailable].
 *
 * ## Implementation notes
 * - **Clickable ancestors.** A `TextView` reading "Sign in" is usually not itself
 *   clickable; its parent `LinearLayout` is. [clickNodeOrAncestor] walks up.
 * - **Recycling.** `AccessibilityNodeInfo` objects must be recycled on older
 *   APIs. `recycle()` is a no-op from API 33 but harmless, so we always call it.
 * - **No coordinate taps.** See [PhoneControl] for why, and what to use instead.
 */
class CompanionAccessibilityService : AccessibilityService(), PhoneControl {

    override val isAvailable: Boolean get() = instance != null

    override fun onServiceConnected() {
        super.onServiceConnected()
        instance = this
        Log.i(TAG, "accessibility service connected")
    }

    override fun onDestroy() {
        if (instance === this) instance = null
        super.onDestroy()
    }

    override fun onInterrupt() {
        Log.d(TAG, "interrupted")
    }

    /** We do not need to observe events to act, but the callback is required. */
    override fun onAccessibilityEvent(event: AccessibilityEvent?) {
        // Intentionally empty. Listening to every event on the device is both a
        // performance cost and a privacy surface we do not need.
    }

    // ------------------------------------------------------------------
    // PhoneControl
    // ------------------------------------------------------------------
    override suspend fun openApp(packageName: String): Boolean {
        if (packageName.isBlank()) return false
        val intent = packageManager.getLaunchIntentForPackage(packageName) ?: run {
            Log.w(TAG, "no launch intent for $packageName")
            return false
        }
        intent.addFlags(Intent.FLAG_ACTIVITY_NEW_TASK)
        return try {
            startActivity(intent)
            true
        } catch (e: Exception) {
            Log.w(TAG, "could not launch $packageName", e)
            false
        }
    }

    override suspend fun tapByText(label: String): Boolean {
        if (label.isBlank()) return false
        val root = rootInActiveWindow ?: return false
        return try {
            val matches = root.findAccessibilityNodeInfosByText(label)
            if (matches.isNullOrEmpty()) {
                Log.d(TAG, "no node matching '$label' on screen")
                return false
            }
            // Prefer an enabled, visible match over a disabled one.
            val target = matches.firstOrNull { it.isEnabled } ?: matches.first()
            clickNodeOrAncestor(target)
        } finally {
            root.recycle()
        }
    }

    override suspend fun typeText(text: String): Boolean {
        val root = rootInActiveWindow ?: return false
        return try {
            val focused = root.findFocus(AccessibilityNodeInfo.FOCUS_INPUT)
            if (focused == null) {
                Log.d(TAG, "nothing is focused; cannot type")
                return false
            }
            val args = Bundle().apply {
                putCharSequence(AccessibilityNodeInfo.ACTION_ARGUMENT_SET_TEXT_CHARSEQUENCE, text)
            }
            focused.performAction(AccessibilityNodeInfo.ACTION_SET_TEXT, args)
                .also { focused.recycle() }
        } finally {
            root.recycle()
        }
    }

    override suspend fun readScreen(): String {
        val root = rootInActiveWindow ?: return "could not read the screen"
        val sb = StringBuilder()
        try {
            dumpNode(root, depth = 0, out = sb)
        } finally {
            root.recycle()
        }
        return if (sb.isBlank()) "the screen has no readable text" else sb.toString()
    }

    override suspend fun pressBack() = performGlobalAction(GLOBAL_ACTION_BACK)

    override suspend fun pressHome() = performGlobalAction(GLOBAL_ACTION_HOME)

    /**
     * Accessibility has no "swipe" verb, so this scrolls the first scrollable
     * container in the tree using its own scroll action. Direction "up" scrolls
     * content up (reveals what is below), matching how people describe it.
     */
    override suspend fun scroll(direction: String): Boolean {
        val root = rootInActiveWindow ?: return false
        return try {
            val scrollable = findScrollable(root) ?: run {
                Log.d(TAG, "nothing scrollable on screen")
                return false
            }
            val action = if (direction.equals("up", ignoreCase = true)) {
                AccessibilityNodeInfo.ACTION_SCROLL_FORWARD
            } else {
                AccessibilityNodeInfo.ACTION_SCROLL_BACKWARD
            }
            scrollable.performAction(action).also { scrollable.recycle() }
        } finally {
            root.recycle()
        }
    }

    // ------------------------------------------------------------------
    // helpers
    // ------------------------------------------------------------------
    /**
     * Click [node], walking up the tree until something is actually clickable.
     * Returns false if nothing in the chain can be clicked.
     */
    private fun clickNodeOrAncestor(node: AccessibilityNodeInfo?): Boolean {
        var current = node
        var hops = 0
        while (current != null && hops < MAX_ANCESTOR_HOPS) {
            if (current.isClickable && current.isEnabled) {
                return current.performAction(AccessibilityNodeInfo.ACTION_CLICK)
            }
            val parent = current.parent
            current.recycle()
            current = parent
            hops++
        }
        current?.recycle()
        return false
    }

    private fun findScrollable(node: AccessibilityNodeInfo): AccessibilityNodeInfo? {
        if (node.isScrollable) return AccessibilityNodeInfo.obtain(node)
        for (i in 0 until node.childCount) {
            val child = node.getChild(i) ?: continue
            val found = findScrollable(child)
            if (found != null) {
                child.recycle()
                return found
            }
            child.recycle()
        }
        return null
    }

    /**
     * A compact tree dump, shaped like the one `android-control` produces, so the
     * same prompt format works whether the backend is Accessibility or ADB.
     *
     * Only nodes with text, a content description, or that are actionable are
     * emitted -- a full dump is thousands of lines of layout noise.
     */
    private fun dumpNode(node: AccessibilityNodeInfo, depth: Int, out: StringBuilder) {
        if (depth > MAX_DEPTH || out.length > MAX_DUMP_CHARS) return

        val text = node.text?.toString()?.take(80).orEmpty()
        val desc = node.contentDescription?.toString()?.take(80).orEmpty()
        val cls = node.className?.toString()?.substringAfterLast('.').orEmpty()
        val rect = android.graphics.Rect().also { node.getBoundsInScreen(it) }
        val visible = rect.width() > 0 && rect.height() > 0

        val interesting = visible && node.isEnabled &&
            (text.isNotBlank() || desc.isNotBlank() || node.isClickable || node.isScrollable)

        if (interesting) {
            out.append("  ".repeat(minOf(depth, 6)))
            out.append('[').append(cls).append(']')
            val label = text.ifBlank { desc }
            if (label.isNotBlank()) out.append(" \"").append(label).append('"')
            if (node.isClickable) out.append(" clickable")
            if (node.isScrollable) out.append(" scrollable")
            if (node.isChecked) out.append(" checked")
            out.append(" center=(")
                .append(rect.centerX()).append(',').append(rect.centerY()).append(')')
            out.append('\n')
        }

        for (i in 0 until node.childCount) {
            val child = node.getChild(i) ?: continue
            dumpNode(child, depth + 1, out)
            child.recycle()
        }
    }

    // ------------------------------------------------------------------
    // coordinate gestures (dispatchGesture, API 24+)
    // ------------------------------------------------------------------
    override suspend fun tapAt(x: Float, y: Float): Boolean =
        gesture(
            Path().apply { moveTo(x, y) },
            durationMs = TAP_DURATION_MS,
        )

    override suspend fun swipeAt(
        x1: Float, y1: Float, x2: Float, y2: Float, durationMs: Long,
    ): Boolean = gesture(
        Path().apply { moveTo(x1, y1); lineTo(x2, y2) },
        durationMs = durationMs,
    )

    /**
     * Inject one gesture. `dispatchGesture` is fire-and-forget, so this bridges
     * its callback into a suspend function -- otherwise every gesture would
     * report success before the OS had even started it.
     */
    private suspend fun gesture(path: Path, durationMs: Long): Boolean =
        suspendCancellableCoroutine { cont ->
            val stroke = GestureDescription.StrokeDescription(path, 0, durationMs)
            val request = GestureDescription.Builder().addStroke(stroke).build()

            val callback = object : GestureResultCallback() {
                override fun onCompleted(description: GestureDescription?) {
                    if (cont.isActive) cont.resume(true)
                }

                override fun onCancelled(description: GestureDescription?) {
                    Log.d(TAG, "gesture cancelled by the system")
                    if (cont.isActive) cont.resume(false)
                }
            }

            val dispatched = try {
                dispatchGesture(request, callback, null)
            } catch (e: Exception) {
                Log.w(TAG, "dispatchGesture threw", e)
                false
            }
            if (!dispatched && cont.isActive) cont.resume(false)
        }

    companion object {
        private const val TAG = "CompanionA11y"
        private const val MAX_ANCESTOR_HOPS = 6
        private const val MAX_DEPTH = 18
        private const val MAX_DUMP_CHARS = 8_000

        /** A tap must last a frame or two; 0ms gestures are dropped. */
        private const val TAP_DURATION_MS = 40L

        /** Non-null only while the user has the service switched on. */
        @Volatile
        var instance: CompanionAccessibilityService? = null
            private set

        /** Convenience for the rest of the app. */
        fun control(): PhoneControl = instance ?: NoOpPhoneControl
    }
}
