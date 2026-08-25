package com.opendroid.ai.pet

import android.content.Context
import android.graphics.PixelFormat
import android.os.Build
import android.util.TypedValue
import android.view.Gravity
import android.view.MotionEvent
import android.view.View
import android.view.ViewConfiguration
import android.view.WindowManager
import android.widget.FrameLayout
import android.widget.ImageButton
import com.opendroid.ai.core.agent.AgentState
import kotlin.math.abs

/**
 * Owns Toni's overlay window: adds, moves, minimises and removes her.
 *
 * ## Why this is a separate class
 * OpenDroid's current floating button lives inside
 * `OpenDroidAccessibilityService` as a 100-line `addFloatingButton()` with two
 * inner View classes. Keeping the window mechanics out of the service means the
 * service stays readable and the pet can be tested, resized and repositioned
 * without touching agent code.
 *
 * ## The two-layer window trick (kept from OpenDroid, issue #107)
 * A square window holding a round icon swallows taps in its transparent corners
 * -- the user taps the app underneath and nothing happens, which reads as the
 * phone being broken. So:
 *
 * - **draw layer** — full size, `FLAG_NOT_TOUCHABLE`. Renders the pet.
 * - **touch layer** — inset to the icon's visible footprint, touchable. Catches
 *   drag, tap and long-press.
 *
 * Both are moved in lockstep. Do not "simplify" this to one window.
 *
 * ## Window type
 * `TYPE_ACCESSIBILITY_OVERLAY` when hosted by an AccessibilityService. That
 * needs **no** `SYSTEM_ALERT_WINDOW` grant, which is why OpenDroid can show the
 * button without sending the user to a Settings screen. If you host this from a
 * normal foreground service instead, pass `hostIsAccessibilityService = false`
 * and it falls back to `TYPE_APPLICATION_OVERLAY` (which does need the grant).
 */
class ToniPetController(
    private val context: Context,
    private val hostIsAccessibilityService: Boolean = true,
    private val sizeDp: Int = 72,
    private val minimizedSizeDp: Int = 44,
) {
    /** Fired on a plain tap (not a drag, not a long press). */
    var onTap: (() -> Unit)? = null

    /** Fired on long press -- OpenDroid uses this to start listening. */
    var onLongPress: (() -> Unit)? = null

    /** Fired when the user taps the minimize button. */
    var onMinimizeToggled: ((minimized: Boolean) -> Unit)? = null

    var isShowing: Boolean = false
        private set

    val pet: ToniPetView? get() = drawLayer

    private var windowManager: WindowManager? = null
    private var drawLayer: ToniPetView? = null
    private var touchLayer: FrameLayout? = null
    private var drawParams: WindowManager.LayoutParams? = null
    private var touchParams: WindowManager.LayoutParams? = null
    private var minimized = false

    // ------------------------------------------------------------------
    // show / hide
    // ------------------------------------------------------------------
    fun show() {
        if (isShowing) return
        if (windowManager == null) {
            windowManager = context.getSystemService(Context.WINDOW_SERVICE) as WindowManager
        }

        val sizePx = dp(minimizedSizeDp.takeIf { minimized } ?: sizeDp)
        val insetPx = dp(8)

        val wm = windowManager ?: return
        val petView = ToniPetView(context)
        drawLayer = petView

        drawParams = WindowManager.LayoutParams(
            sizePx, sizePx,
            overlayType(),
            WindowManager.LayoutParams.FLAG_NOT_FOCUSABLE or
                WindowManager.LayoutParams.FLAG_LAYOUT_NO_LIMITS or
                WindowManager.LayoutParams.FLAG_NOT_TOUCHABLE,
            PixelFormat.TRANSLUCENT,
        ).apply {
            gravity = Gravity.TOP or Gravity.START
            x = initialX(sizePx)
            y = initialY()
        }

        touchLayer = buildTouchLayer(petView, sizePx, insetPx)
        touchParams = (drawParams!!.copy()).apply {
            width = sizePx - 2 * insetPx
            height = sizePx - 2 * insetPx
            // Drop NOT_TOUCHABLE: this layer is the one that receives input.
            flags = WindowManager.LayoutParams.FLAG_NOT_FOCUSABLE or
                WindowManager.LayoutParams.FLAG_LAYOUT_NO_LIMITS
            x = drawParams!!.x + insetPx
            y = drawParams!!.y + insetPx
        }

        try {
            wm.addView(petView, drawParams)
            wm.addView(touchLayer, touchParams)
            isShowing = true
        } catch (e: Exception) {
            // A failed addView leaves a half-added window; clean both up so a
            // later hide() does not throw on a view that was never added.
            runCatching { wm.removeView(petView) }
            runCatching { wm.removeView(touchLayer) }
            drawLayer = null
            touchLayer = null
            drawParams = null
            touchParams = null
            throw e
        }
    }

    fun hide() {
        if (!isShowing) return
        val wm = windowManager ?: return
        runCatching { drawLayer?.let { wm.removeView(it) } }
        runCatching { touchLayer?.let { wm.removeView(it) } }
        drawLayer = null
        touchLayer = null
        drawParams = null
        touchParams = null
        isShowing = false
    }

    /** Collapse to a small sleeping ball, or expand back. */
    fun setMinimized(value: Boolean) {
        if (minimized == value) return
        minimized = value
        drawLayer?.minimized = value
        drawLayer?.setMood(if (value) PetMood.SLEEPING else PetMood.IDLE)
        // Resize means re-adding: WindowManager will not resize a window whose
        // LayoutParams object identity it already holds.
        hide()
        show()
        onMinimizeToggled?.invoke(value)
    }

    fun toggleMinimized() = setMinimized(!minimized)

    // ------------------------------------------------------------------
    // driven by the agent
    // ------------------------------------------------------------------
    fun updateState(state: AgentState) {
        if (minimized) return                 // a sleeping pet ignores the agent
        drawLayer?.updateState(state)
    }

    /** Feed TTS amplitude (0..1) for lip-sync. */
    fun setMouthOpen(level: Float) {
        drawLayer?.mouthOpen = level.coerceIn(0f, 1f)
    }

    /** Move her somewhere specific, e.g. out of the way of a dialog. */
    fun moveTo(x: Int, y: Int) {
        val wm = windowManager ?: return
        val dp1 = drawParams ?: return
        val tp = touchParams ?: return
        val insetPx = dp(8)
        dp1.x = x.coerceIn(0, screenWidth() - dp1.width)
        dp1.y = y.coerceIn(0, screenHeight() - dp1.height)
        tp.x = dp1.x + insetPx
        tp.y = dp1.y + insetPx
        runCatching {
            drawLayer?.let { wm.updateViewLayout(it, dp1) }
            touchLayer?.let { wm.updateViewLayout(it, tp) }
        }
    }

    // ------------------------------------------------------------------
    // touch layer
    // ------------------------------------------------------------------
    private fun buildTouchLayer(
        petView: ToniPetView,
        sizePx: Int,
        insetPx: Int,
    ): FrameLayout {
        val root = FrameLayout(context)

        // Minimize affordance, pinned to the top-right of the touchable area.
        val button = ImageButton(context).apply {
            setImageResource(android.R.drawable.arrow_down_float)
            setBackgroundResource(android.R.color.transparent)
            contentDescription = "Minimize Toni"
            setOnClickListener { toggleMinimized() }
        }
        root.addView(
            button,
            FrameLayout.LayoutParams(dp(22), dp(22), Gravity.TOP or Gravity.END),
        )

        root.setOnTouchListener(DragTouchHandler(petView, sizePx, insetPx))
        return root
    }

    /**
     * Separates drag from tap from long-press.
     *
     * The three cases need different handling and the naive version gets all of
     * them subtly wrong: a drag that ends still fires a click, a tap that
     * arrives after the long-press timeout fires both, and `updateViewLayout`
     * called on every motion event makes the window jitter.
     */
    private inner class DragTouchHandler(
        private val petView: ToniPetView,
        private val sizePx: Int,
        private val insetPx: Int,
    ) : View.OnTouchListener {

        private var startX = 0
        private var startY = 0
        private var startTouchX = 0f
        private var startTouchY = 0f
        private var isTapCandidate = false
        private val touchSlop = ViewConfiguration.get(context).scaledTouchSlop.toFloat()

        private val longPressRunnable = Runnable {
            isTapCandidate = false
            onLongPress?.invoke()
        }

        override fun onTouch(v: View, event: MotionEvent): Boolean {
            val dp = drawParams ?: return false
            val tp = touchParams ?: return false
            val wm = windowManager ?: return false

            when (event.actionMasked) {
                MotionEvent.ACTION_DOWN -> {
                    startX = dp.x
                    startY = dp.y
                    startTouchX = event.rawX
                    startTouchY = event.rawY
                    isTapCandidate = true
                    v.postDelayed(longPressRunnable,
                        ViewConfiguration.getLongPressTimeout().toLong())
                    return true
                }

                MotionEvent.ACTION_MOVE -> {
                    val dx = (event.rawX - startTouchX).toInt()
                    val dy = (event.rawY - startTouchY).toInt()

                    if (isTapCandidate &&
                        (abs(event.rawX - startTouchX) > touchSlop ||
                            abs(event.rawY - startTouchY) > touchSlop)
                    ) {
                        // Left the slop: this is a drag, so cancel the pending
                        // long press or it fires mid-drag.
                        isTapCandidate = false
                        v.removeCallbacks(longPressRunnable)
                    }

                    val nx = (startX + dx).coerceIn(0, screenWidth() - dp.width)
                    val ny = (startY + dy).coerceIn(0, screenHeight() - dp.height)
                    if (nx != dp.x || ny != dp.y) {
                        dp.x = nx
                        dp.y = ny
                        tp.x = nx + insetPx
                        tp.y = ny + insetPx
                        runCatching {
                            wm.updateViewLayout(petView, dp)
                            wm.updateViewLayout(v, tp)
                        }
                    }
                    return true
                }

                MotionEvent.ACTION_UP -> {
                    v.removeCallbacks(longPressRunnable)
                    if (isTapCandidate) {
                        petView.react()
                        v.performClick()
                        onTap?.invoke()
                    }
                    return true
                }

                MotionEvent.ACTION_CANCEL -> {
                    v.removeCallbacks(longPressRunnable)
                    return true
                }
            }
            return false
        }
    }

    // ------------------------------------------------------------------
    // geometry
    // ------------------------------------------------------------------
    private fun overlayType(): Int = when {
        hostIsAccessibilityService -> WindowManager.LayoutParams.TYPE_ACCESSIBILITY_OVERLAY
        Build.VERSION.SDK_INT >= Build.VERSION_CODES.O ->
            WindowManager.LayoutParams.TYPE_APPLICATION_OVERLAY
        else -> @Suppress("DEPRECATION") WindowManager.LayoutParams.TYPE_PHONE
    }

    private fun initialX(sizePx: Int): Int = screenWidth() - sizePx - dp(12)

    private fun initialY(): Int = (screenHeight() * 0.55f).toInt()

    private fun screenWidth(): Int = context.resources.displayMetrics.widthPixels

    private fun screenHeight(): Int = context.resources.displayMetrics.heightPixels

    private fun dp(value: Int): Int = TypedValue.applyDimension(
        TypedValue.COMPLEX_UNIT_DIP, value.toFloat(), context.resources.displayMetrics,
    ).toInt()

    /** [WindowManager.LayoutParams] has no copy(); this keeps the flags in sync. */
    private fun WindowManager.LayoutParams.copy() = WindowManager.LayoutParams(
        type, flags, format,
    ).also {
        it.width = width
        it.height = height
        it.gravity = gravity
        it.x = x
        it.y = y
    }
}
