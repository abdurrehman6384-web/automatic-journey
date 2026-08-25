package com.rgs.companion.live2d

import android.content.Context
import android.graphics.BitmapFactory
import android.opengl.GLES20
import android.opengl.GLSurfaceView
import android.opengl.GLUtils
import android.util.Log
import com.live2d.sdk.cubism.framework.math.CubismMatrix44
import javax.microedition.khronos.egl.EGLConfig
import javax.microedition.khronos.opengles.GL10
import kotlin.math.max
import kotlin.math.min

/**
 * The Cubism update + draw loop.
 *
 * Responsibilities, in the order Cubism expects them:
 *
 * 1. **once per context** — bootstrap the framework, load the model, upload
 *    textures to GL.
 * 2. **per frame** — drain UI-thread requests (expression / motion), tick the
 *    model by real elapsed time, then draw with an MVP matrix that fits the
 *    model in the viewport.
 *
 * Timing uses [System.nanoTime] rather than a fixed 1/60s. On a 120 Hz display a
 * fixed step makes every animation play at double speed; on a throttled one it
 * makes her stutter.
 */
class Live2DRenderer(private val context: Context) : GLSurfaceView.Renderer {

    // ── state written from the UI thread, read on the GL thread ─────────
    @Volatile var pendingExpression: String? = null
    @Volatile var pendingMotion: PendingMotion? = null
    @Volatile var mouthOpen: Float = 0f
    @Volatile var dragX: Float = 0f
    @Volatile var dragY: Float = 0f
    @Volatile var resumed: Boolean = true

    private var model: CompanionModel? = null
    private var pendingLoadPath: String? = null

    private var viewWidth = 1
    private var viewHeight = 1
    private var lastFrameNanos = 0L

    private val mvp = CubismMatrix44.create()
    private val deviceToScreen = CubismMatrix44.create()
    private val modelToScreen = CubismMatrix44.create()
    private val mvpOut = FloatArray(16)

    /** Tap coordinates in model space, consumed on the next frame. */
    private var pendingTapX: Float? = null
    private var pendingTapY: Float? = null

    // ------------------------------------------------------------------
    // GLSurfaceView.Renderer
    // ------------------------------------------------------------------
    override fun onSurfaceCreated(gl: GL10?, config: EGLConfig?) {
        CubismBootstrap.ensureStarted(context.applicationContext, logging = BuildConfigLike.DEBUG)
        GLES20.glClearColor(0f, 0f, 0f, 0f)      // transparent
        GLES20.glEnable(GLES20.GL_BLEND)
        GLES20.glBlendFunc(GLES20.GL_ONE, GLES20.GL_ONE_MINUS_SRC_ALPHA)

        // A GL context can be recreated (rotation, backgrounding). Reload.
        pendingLoadPath?.let { loadModel(it) }
    }

    override fun onSurfaceChanged(gl: GL10?, width: Int, height: Int) {
        viewWidth = max(width, 1)
        viewHeight = max(height, 1)
        GLES20.glViewport(0, 0, viewWidth, viewHeight)

        // Device -> screen, exactly as the official sample builds it: uniform
        // scale on the smaller axis, Y flipped because GL points up while view
        // coordinates point down, then centre.
        deviceToScreen.loadIdentity()
        if (viewWidth.toFloat() / viewHeight > 1f) {
            deviceToScreen.scaleRelative(viewHeight.toFloat() / viewWidth, -1f)
        } else {
            deviceToScreen.scaleRelative(1f, -viewWidth.toFloat() / viewHeight)
        }
        deviceToScreen.translateRelative(0f, 0f)
    }

    override fun onDrawFrame(gl: GL10?) {
        val now = System.nanoTime()
        val deltaSeconds = if (lastFrameNanos == 0L) 1f / 60f
        else min((now - lastFrameNanos) / 1_000_000_000f, MAX_DELTA)
        lastFrameNanos = now

        val m = model
        if (m == null || !resumed) {
            GLES20.glClear(GLES20.GL_COLOR_BUFFER_BIT or GLES20.GL_DEPTH_BUFFER_BIT)
            return
        }

        GLES20.glClear(GLES20.GL_COLOR_BUFFER_BIT or GLES20.GL_DEPTH_BUFFER_BIT)

        // ── drain requests from the UI thread ──────────────────────────
        pendingExpression?.let { m.setExpression(it); pendingExpression = null }
        pendingMotion?.let {
            m.startMotion(it.group, it.index, it.priority.value)
            pendingMotion = null
        }
        pendingTapX?.let { x ->
            pendingTapY?.let { y ->
                val hit = m.hitTest(x, y)
                if (hit != null) {
                    // Convention: tapping a hit area plays the "Tap<Area>" group.
                    m.startMotion("Tap$hit", 0, MotionPriority.NORMAL.value)
                }
            }
            pendingTapX = null
            pendingTapY = null
        }

        // ── inputs ─────────────────────────────────────────────────────
        m.setLipSync(mouthOpen)
        m.setDrag(dragX, dragY)

        // ── animate + draw ─────────────────────────────────────────────
        m.update(deltaSeconds)

        buildModelMatrix()
        CubismMatrix44.multiply(modelToScreen.getArray(), deviceToScreen.getArray(),
            mvpOut)
        mvp.setMatrix(mvpOut)
        m.androidRenderer().setMvpMatrix(mvp)
        m.androidRenderer().drawModel()
    }

    /**
     * Fit the model in the viewport without distorting it. Models are authored
     * in arbitrary units, so we scale uniformly by the constraining axis and
     * nudge the model down so full-body art is not cropped at the chin.
     */
    private fun buildModelMatrix() {
        modelToScreen.loadIdentity()

        val scale = MODEL_SCALE
        modelToScreen.scaleRelative(scale, scale)
        modelToScreen.translateRelative(0f, -VERTICAL_OFFSET)
    }
    // ------------------------------------------------------------------
    // called from the UI thread
    // ------------------------------------------------------------------
    /** Must be called on the GL thread (Live2DView dispatches via `queueEvent`). */
    fun loadModel(assetPath: String) {
        pendingLoadPath = assetPath
        val dir = assetPath.substringBeforeLast('/', "") .let { if (it.isEmpty()) "" else "$it/" }
        val name = assetPath.substringAfterLast('/')

        model?.releaseAll()
        val m = CompanionModel(dir, name)
        try {
            m.setup()
        } catch (e: Exception) {
            Log.e(TAG, "model setup failed for $assetPath", e)
            return
        }
        uploadTextures(m)
        model = m
        Log.d(TAG, "loaded $assetPath")
    }

    private fun uploadTextures(m: CompanionModel) {
        m.textureFileNames().forEachIndexed { index, path ->
            val bytes = CubismBootstrap.read(path)
            if (bytes == null) {
                Log.e(TAG, "missing texture: $path")
                return@forEachIndexed
            }
            val bitmap = BitmapFactory.decodeByteArray(bytes, 0, bytes.size)
            if (bitmap == null) {
                Log.e(TAG, "could not decode texture: $path")
                return@forEachIndexed
            }

            val texIds = IntArray(1)
            GLES20.glGenTextures(1, texIds, 0)
            GLES20.glBindTexture(GLES20.GL_TEXTURE_2D, texIds[0])
            GLUtils.texImage2D(GLES20.GL_TEXTURE_2D, 0, bitmap, 0)
            GLES20.glGenerateMipmap(GLES20.GL_TEXTURE_2D)
            GLES20.glTexParameterf(
                GLES20.GL_TEXTURE_2D, GLES20.GL_TEXTURE_MIN_FILTER,
                GLES20.GL_LINEAR_MIPMAP_LINEAR.toFloat(),
            )
            GLES20.glTexParameterf(
                GLES20.GL_TEXTURE_2D, GLES20.GL_TEXTURE_MAG_FILTER,
                GLES20.GL_LINEAR.toFloat(),
            )
            bitmap.recycle()

            m.bindTexture(index, texIds[0], premultipliedAlpha = true)
        }
    }

    // ------------------------------------------------------------------
    // touch
    // ------------------------------------------------------------------
    fun touchesBegan(x: Float, y: Float) {
        // nothing needed; kept for symmetry with the sample's TouchManager
    }

    fun touchesMoved(x: Float, y: Float) {
        // drag is applied via setDrag()
    }

    fun touchesEnded(x: Float, y: Float) {
        // Convert view coords (0..1, y down) to model space (-1..1, y up).
        pendingTapX = x * 2f - 1f
        pendingTapY = -(y * 2f - 1f)
    }

    // ------------------------------------------------------------------
    fun expressionNames(): List<String> = model?.expressionNames() ?: emptyList()

    fun motionGroups(): List<String> = model?.motionGroups() ?: emptyList()

    private companion object {
        const val TAG = "Live2DRenderer"

        /** Clamp the delta so returning from background does not fast-forward. */
        const val MAX_DELTA = 0.1f

        /** Overall zoom. Tune per model. */
        const val MODEL_SCALE = 0.9f

        /** Push the model down in the frame so full-body art is not cropped. */
        const val VERTICAL_OFFSET = 0.15f
    }
}

/** Avoids a hard dependency on BuildConfig in a library-shaped module. */
private object BuildConfigLike {
    val DEBUG: Boolean = System.getProperty("companion.debug") == "true"
}
