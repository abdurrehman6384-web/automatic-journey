package com.rgs.companion.overlay

import android.app.Notification
import android.app.NotificationChannel
import android.app.NotificationManager
import android.app.PendingIntent
import android.app.Service
import android.content.Context
import android.content.Intent
import android.graphics.PixelFormat
import android.os.Build
import android.os.IBinder
import android.util.Log
import android.view.Gravity
import android.view.MotionEvent
import android.view.View
import android.view.WindowManager
import android.widget.FrameLayout
import android.widget.ImageButton
import com.rgs.companion.MainActivity
import com.rgs.companion.R
import com.rgs.companion.live2d.Live2DView
import com.rgs.companion.live2d.MotionPriority
import kotlin.math.abs

/**
 * The desktop-pet overlay: a Live2D avatar floating above every app.
 *
 * ## Architecture
 * ```
 * FloatingCompanionService            (foreground service, owns the window)
 *   └── WindowManager overlay         (TYPE_APPLICATION_OVERLAY)
 *         └── FrameLayout  "bubble"
 *               ├── Live2DView        (GLSurfaceView, transparent, draggable)
 *               └── ImageButton       (minimize / expand)
 * ```
 *
 * Why a foreground `Service` and not an `Activity`: an overlay has to survive the
 * user leaving your app, and Android 8+ only lets a *started foreground* service
 * add `TYPE_APPLICATION_OVERLAY` windows reliably.
 *
 * ## Two things that trip people up
 * 1. **`FLAG_NOT_FOCUSABLE`** is required, otherwise the overlay steals the
 *    keyboard from whatever app is underneath and the user cannot type.
 * 2. **`GLSurfaceView` lifecycle.** The GL thread must be paused when the window
 *    is removed and resumed when re-added, or you leak a context and a thread.
 *    Handled in [removeOverlay] / [addOverlay].
 *
 * ## Permissions
 * - `SYSTEM_ALERT_WINDOW`, granted through
 *   `Settings.ACTION_MANAGE_OVERLAY_PERMISSION` (not a runtime dialog).
 * - `FOREGROUND_SERVICE` + `FOREGROUND_SERVICE_SPECIAL_USE`.
 */
class FloatingCompanionService : Service() {

    private lateinit var windowManager: WindowManager
    private var bubble: FrameLayout? = null
    private var live2d: Live2DView? = null
    private var params: WindowManager.LayoutParams? = null
    private var minimized = false

    /** Tap listener the host app can set (wired to the chat sheet). */
    var onAvatarTap: (() -> Unit)? = null

    override fun onBind(intent: Intent?): IBinder? = null

    override fun onCreate() {
        super.onCreate()
        windowManager = getSystemService(WINDOW_SERVICE) as WindowManager
        startInForeground()
    }

    override fun onStartCommand(intent: Intent?, flags: Int, startId: Int): Int {
        when (intent?.action) {
            ACTION_SHOW -> show()
            ACTION_HIDE -> hide()
            ACTION_TOGGLE -> if (bubble == null) show() else hide()
            ACTION_SPEAK -> {
                val text = intent.getStringExtra(EXTRA_EMOTION)
                if (text != null) setEmotion(text)
            }
            else -> show()
        }
        // START_STICKY: if the system kills us, come back. A pet that vanishes
        // forever after a low-memory event reads as a bug.
        return START_STICKY
    }

    override fun onDestroy() {
        removeOverlay()
        super.onDestroy()
    }

    // ------------------------------------------------------------------
    // window
    // ------------------------------------------------------------------
    private fun show() {
        if (bubble != null) return
        if (!canDrawOverlays(this)) {
            Log.w(TAG, "overlay permission not granted")
            return
        }
        addOverlay()
    }

    private fun hide() {
        removeOverlay()
    }

    private fun addOverlay() {
        val size = currentSize()

        val lp = WindowManager.LayoutParams(
            size, size,
            overlayType(),
            // NOT_FOCUSABLE so the app underneath keeps the keyboard.
            // LAYOUT_NO_LIMITS lets the pet be dragged partially off-screen.
            WindowManager.LayoutParams.FLAG_NOT_FOCUSABLE or
                WindowManager.LayoutParams.FLAG_LAYOUT_NO_LIMITS,
            PixelFormat.TRANSLUCENT,
        ).apply {
            gravity = Gravity.TOP or Gravity.START
            x = initialX()
            y = initialY()
        }
        params = lp

        val root = FrameLayout(this)

        val avatar = Live2DView(this).apply {
            onTap = { _, _ ->
                // A tap that is not a drag opens the chat.
                onAvatarTap?.invoke()
            }
        }
        live2d = avatar
        root.addView(
            avatar,
            FrameLayout.LayoutParams(
                FrameLayout.LayoutParams.MATCH_PARENT,
                FrameLayout.LayoutParams.MATCH_PARENT,
            ),
        )

        root.addView(makeMinimizeButton(), minimizeButtonLayoutParams())

        makeDraggable(root, lp)
        bubble = root
        windowManager.addView(root, lp)

        avatar.loadModel(modelAssetPath())
        Log.i(TAG, "overlay shown (${size}px)")
    }

    private fun removeOverlay() {
        val root = bubble ?: return
        // Stop the GL thread before the view leaves the window.
        live2d?.onPause()
        live2d = null
        runCatching { windowManager.removeView(root) }
            .onFailure { Log.w(TAG, "removeView failed", it) }
        bubble = null
    }

    // ------------------------------------------------------------------
    // dragging
    // ------------------------------------------------------------------
    /**
     * Distinguishes drag from tap by movement, and only writes layout params when
     * the position actually changed -- `updateViewLayout` on every motion event is
     * the classic cause of a jittery overlay.
     */
    private fun makeDraggable(view: View, lp: WindowManager.LayoutParams) {
        var initialTouchX = 0f
        var initialTouchY = 0f
        var startX = 0
        var startY = 0
        var moved = false

        view.setOnTouchListener { _, event ->
            when (event.actionMasked) {
                MotionEvent.ACTION_DOWN -> {
                    initialTouchX = event.rawX
                    initialTouchY = event.rawY
                    startX = lp.x
                    startY = lp.y
                    moved = false
                    false                                   // let children see it too
                }

                MotionEvent.ACTION_MOVE -> {
                    val dx = (event.rawX - initialTouchX).toInt()
                    val dy = (event.rawY - initialTouchY).toInt()
                    if (!moved && abs(dx) + abs(dy) > DRAG_SLOP_PX) moved = true
                    if (moved) {
                        val nx = startX + dx
                        val ny = startY + dy
                        if (nx != lp.x || ny != lp.y) {
                            lp.x = nx
                            lp.y = ny
                            runCatching { windowManager.updateViewLayout(view, lp) }
                        }
                    }
                    moved
                }

                else -> false
            }
        }
    }

    // ------------------------------------------------------------------
    // minimize
    // ------------------------------------------------------------------
    private fun makeMinimizeButton(): ImageButton =
        ImageButton(this).apply {
            setImageResource(R.drawable.ic_minimize)
            setBackgroundResource(android.R.color.transparent)
            contentDescription = getString(R.string.minimize_companion)
            setOnClickListener { toggleMinimized() }
        }

    private fun minimizeButtonLayoutParams() = FrameLayout.LayoutParams(
        MINIMIZE_BUTTON_PX, MINIMIZE_BUTTON_PX, Gravity.TOP or Gravity.END,
    )

    private fun toggleMinimized() {
        minimized = !minimized
        removeOverlay()
        addOverlay()
    }

    // ------------------------------------------------------------------
    // driven from outside
    // ------------------------------------------------------------------
    fun setEmotion(expressionName: String) {
        live2d?.setExpression(expressionName)
    }

    fun setMouthOpen(v: Float) {
        live2d?.setMouthOpen(v)
    }

    fun playMotion(group: String, index: Int = 0) {
        live2d?.startMotion(group, index, MotionPriority.NORMAL)
    }

    // ------------------------------------------------------------------
    // geometry
    // ------------------------------------------------------------------
    private fun currentSize(): Int =
        if (minimized) MINIMIZED_SIZE_PX else EXPANDED_SIZE_PX

    private fun initialX(): Int = 0

    private fun initialY(): Int {
        val h = resources.displayMetrics.heightPixels
        return (h * 0.45f).toInt()
    }

    private fun overlayType(): Int =
        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.O) {
            WindowManager.LayoutParams.TYPE_APPLICATION_OVERLAY
        } else {
            @Suppress("DEPRECATION")
            WindowManager.LayoutParams.TYPE_PHONE
        }

    /**
     * Which model the overlay shows. Reads from shared prefs so the user can
     * switch models without a rebuild; falls back to the bundled one.
     */
    private fun modelAssetPath(): String =
        getSharedPreferences(PREFS, MODE_PRIVATE)
            .getString(KEY_MODEL, DEFAULT_MODEL) ?: DEFAULT_MODEL

    // ------------------------------------------------------------------
    // foreground notification
    // ------------------------------------------------------------------
    private fun startInForeground() {
        val manager = getSystemService(NOTIFICATION_SERVICE) as NotificationManager
        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.O) {
            manager.createNotificationChannel(
                NotificationChannel(
                    CHANNEL_ID,
                    getString(R.string.companion_channel_name),
                    NotificationManager.IMPORTANCE_LOW,     // no sound, no heads-up
                ),
            )
        }

        val open = PendingIntent.getActivity(
            this, 0, Intent(this, MainActivity::class.java),
            PendingIntent.FLAG_IMMUTABLE or PendingIntent.FLAG_UPDATE_CURRENT,
        )

        val notification = Notification.Builder(this, CHANNEL_ID)
            .setSmallIcon(R.drawable.ic_companion)
            .setContentTitle(getString(R.string.companion_notification_title))
            .setContentText(getString(R.string.companion_notification_text))
            .setContentIntent(open)
            .setOngoing(true)
            .build()

        startForeground(NOTIFICATION_ID, notification)
    }

    companion object {
        private const val TAG = "FloatingCompanion"
        private const val CHANNEL_ID = "companion_overlay"
        private const val NOTIFICATION_ID = 4201

        private const val PREFS = "companion_prefs"
        private const val KEY_MODEL = "model_path"

        /** Bundled model. Change to whichever you ship in assets/models/. */
        const val DEFAULT_MODEL = "models/hiyori/hiyori.model3.json"

        private const val EXPANDED_SIZE_PX = 620
        private const val MINIMIZED_SIZE_PX = 260
        private const val MINIMIZE_BUTTON_PX = 72
        private const val DRAG_SLOP_PX = 12

        const val ACTION_SHOW = "com.rgs.companion.overlay.SHOW"
        const val ACTION_HIDE = "com.rgs.companion.overlay.HIDE"
        const val ACTION_TOGGLE = "com.rgs.companion.overlay.TOGGLE"
        const val ACTION_SPEAK = "com.rgs.companion.overlay.SPEAK"
        const val EXTRA_EMOTION = "emotion"

        fun canDrawOverlays(context: Context): Boolean =
            if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.M) {
                android.provider.Settings.canDrawOverlays(context)
            } else {
                true
            }

        fun overlayPermissionIntent(context: Context): Intent =
            Intent(
                android.provider.Settings.ACTION_MANAGE_OVERLAY_PERMISSION,
                android.net.Uri.parse("package:${context.packageName}"),
            )

        fun start(context: Context) {
            context.startForegroundService(Intent(context, FloatingCompanionService::class.java))
        }
    }
}
