package com.rgs.companion.live2d

import android.content.Context
import android.opengl.GLSurfaceView
import android.util.AttributeSet
import android.view.MotionEvent

/**
 * A drop-in `View` that renders a Live2D Cubism model.
 *
 * From a classic View hierarchy:
 * ```
 * val live2d = findViewById<Live2DView>(R.id.live2d)
 * live2d.loadModel("models/hiyori/hiyori.model3.json")
 * live2d.setExpression("Happy")
 * live2d.startMotion("TapBody", 0)
 * live2d.setMouthOpen(0.7f)              // driven by TTS volume
 * ```
 *
 * From Jetpack Compose:
 * ```
 * AndroidView(
 *     factory = { ctx -> Live2DView(ctx).apply { onTap = { _, _ -> viewModel.poke() } } },
 *     update  = { view -> view.setExpression(emotion.expressionName) },
 * )
 * ```
 *
 * ## Threading
 * All model work happens on the GL thread. The public setters only write to
 * volatile fields on the renderer, so calling them from the UI thread or a
 * coroutine is safe; the renderer reads them on its next frame. `loadModel`
 * is dispatched onto the GL thread with [queueEvent].
 *
 * ## Why GLSurfaceView rather than a Compose Canvas
 * Cubism renders through OpenGL ES 2.0 with its own shaders and a native core
 * (`Live2DCubismCore`). Compose has no GL interop surface, so `GLSurfaceView`
 * is the supported host and `AndroidView` embeds it in Compose.
 */
class Live2DView @JvmOverloads constructor(
    context: Context,
    attrs: AttributeSet? = null,
) : GLSurfaceView(context, attrs) {

    /**
     * Fires when the user taps (not drags) the model. Coordinates are normalised
     * 0..1 across the view, which is enough to hit-test head / body / etc.
     */
    var onTap: ((x: Float, y: Float) -> Unit)? = null

    private val renderer = Live2DRenderer(context)

    init {
        setEGLContextClientVersion(2)                  // Cubism requires GLES 2.0
        setEGLConfigChooser(8, 8, 8, 8, 16, 0)         // RGBA8888 + 16-bit depth
        setRenderer(renderer)
        // CONTINUOUSLY because idle motion, breathing and blinking animate even
        // when nothing else is happening. Switch to RENDERMODE_WHEN_DIRTY if you
        // need to save battery and are happy to invalidate on demand.
        renderMode = RENDERMODE_CONTINUOUSLY
        setZOrderOnTop(false)
        setZOrderMediaOverlay(true)
        holder.setFormat(android.graphics.PixelFormat.TRANSLUCENT)
    }

    // ------------------------------------------------------------------
    // lifecycle -- GLSurfaceView requires these to be forwarded
    // ------------------------------------------------------------------
    override fun onResume() {
        super.onResume()
        renderer.resumed = true
    }

    override fun onPause() {
        renderer.resumed = false
        super.onPause()
    }

    // ------------------------------------------------------------------
    // public API
    // ------------------------------------------------------------------
    /** Load a `.model3.json` from assets, e.g. `"models/hiyori/hiyori.model3.json"`. */
    fun loadModel(assetPath: String) {
        queueEvent { renderer.loadModel(assetPath) }
    }

    /** Play an expression by the name used in the model's `Expressions` group. */
    fun setExpression(name: String) {
        renderer.pendingExpression = name
    }

    /** Play a motion from a group, e.g. `startMotion("TapBody", 1)`. */
    fun startMotion(
        group: String,
        index: Int,
        priority: MotionPriority = MotionPriority.NORMAL,
    ) {
        renderer.pendingMotion = PendingMotion(group, index, priority)
    }

    /**
     * Lip-sync: 0f..1f, typically the RMS of the TTS buffer currently playing.
     * Drives `ParamMouthOpenY`.
     */
    fun setMouthOpen(value: Float) {
        renderer.mouthOpen = value.coerceIn(0f, 1f)
    }

    /** Look direction, -1f..1f per axis (`ParamAngleX/Y`, `ParamEyeBallX/Y`). */
    fun setDrag(x: Float, y: Float) {
        renderer.dragX = x.coerceIn(-1f, 1f)
        renderer.dragY = y.coerceIn(-1f, 1f)
    }

    /** The model's expression names -- useful for building a picker. */
    fun expressionNames(): List<String> = renderer.expressionNames()

    /** The model's motion group names. */
    fun motionGroups(): List<String> = renderer.motionGroups()

    // ------------------------------------------------------------------
    // touch -> drag + tap reaction
    // ------------------------------------------------------------------
    override fun onTouchEvent(event: MotionEvent): Boolean {
        val nx = event.x / width.coerceAtLeast(1)
        val ny = event.y / height.coerceAtLeast(1)

        when (event.actionMasked) {
            MotionEvent.ACTION_DOWN -> {
                downX = event.x
                downY = event.y
                renderer.touchesBegan(nx, ny)
            }

            MotionEvent.ACTION_MOVE -> {
                renderer.touchesMoved(nx, ny)
                // She follows your finger.
                setDrag((nx - 0.5f) * 2f, (ny - 0.5f) * 2f)
            }

            MotionEvent.ACTION_UP, MotionEvent.ACTION_CANCEL -> {
                val dx = event.x - downX
                val dy = event.y - downY
                val isTap = dx * dx + dy * dy < TAP_SLOP_PX * TAP_SLOP_PX
                renderer.touchesEnded(nx, ny)
                if (isTap) onTap?.invoke(nx, ny)
            }
        }
        return true
    }

    private var downX = 0f
    private var downY = 0f

    private companion object {
        /** Tell a tap from a drag without depending on ViewConfiguration. */
        const val TAP_SLOP_PX = 24f
    }
}
