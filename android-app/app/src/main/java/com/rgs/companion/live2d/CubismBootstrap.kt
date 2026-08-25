package com.rgs.companion.live2d

import android.content.Context
import android.util.Log
import com.live2d.sdk.cubism.framework.CubismFramework
import com.live2d.sdk.cubism.framework.CubismFrameworkConfig.LogLevel
import com.live2d.sdk.cubism.framework.ICubismLoadFileFunction
import com.live2d.sdk.cubism.core.ICubismLogger

/**
 * One-time Cubism Framework bootstrap, including the asset loader.
 *
 * Two things happen here and both matter:
 *
 * 1. `startUp()` / `initialize()` must run once per process, on the GL thread,
 *    before any model is created.
 * 2. **`loadFileFunction` is how the framework reads files.** Cubism never
 *    touches `AssetManager` itself -- every `.model3.json`, `.moc3`, texture and
 *    `.motion3.json` is fetched through this callback. Without it, model loading
 *    fails with a confusing "file not found" deep inside the core.
 *
 * [ensureStarted] is idempotent, so calling it from every
 * [Live2DRenderer.onSurfaceCreated] is safe. That is what lets the floating
 * companion window own a second GL surface without re-initialising the core.
 */
object CubismBootstrap {

    private const val TAG = "CubismBootstrap"

    @Volatile
    private var started = false

    /** Application context, captured once so no Activity is retained. */
    private var appContext: Context? = null

    /**
     * @param appContext used for [android.content.res.AssetManager]; the
     *   application context is captured so no Activity leaks.
     */
    @Synchronized
    fun ensureStarted(appContext: Context, logging: Boolean = false) {
        if (started) return

        val ctx = appContext.applicationContext
        this.appContext = ctx
        val assets = ctx.assets

        if (!CubismFramework.isStarted()) {
            val option = CubismFramework.Option()

            option.logFunction = ICubismLogger { message -> Log.d(TAG, message) }
            option.loggingLevel = if (logging) LogLevel.VERBOSE else LogLevel.OFF

            // The single most important line: teach Cubism how to read assets.
            option.loadFileFunction = ICubismLoadFileFunction { path ->
                readAsset(assets, path)
            }

            check(CubismFramework.startUp(option)) {
                "CubismFramework.startUp failed. Check that Live2DCubismCore.aar is in " +
                    "app/libs and that the device ABI is one of " +
                    "armeabi-v7a / arm64-v8a / x86 / x86_64."
            }
        }

        if (!CubismFramework.isInitialized()) {
            CubismFramework.initialize()
        }
        started = true
    }

    /**
     * Read any model file (texture, moc3, motion3.json) by the same rules the
     * framework's loader uses. Exposed so the renderer can decode textures with
     * `BitmapFactory` without duplicating the path logic.
     */
    fun read(path: String): ByteArray? {
        val ctx = appContext ?: return null
        return readAsset(ctx.assets, path)
    }

    /**
     * Read a path that is either inside assets (`models/hiyori/hiyori.moc3`) or
     * on external storage (`/sdcard/.../hiyori.moc3`).
     *
     * Supporting both is what makes "drop a new model on the phone and switch to
     * it" possible without rebuilding the app.
     */
    private fun readAsset(
        assets: android.content.res.AssetManager,
        path: String,
    ): ByteArray? {
        return try {
            if (path.startsWith("/")) {
                java.io.File(path).takeIf { it.exists() }?.readBytes()
            } else {
                assets.open(path).use { it.readBytes() }
            }
        } catch (e: Exception) {
            Log.e(TAG, "load failed: $path", e)
            null
        }
    }

    @Synchronized
    fun tearDown() {
        if (!started) return
        if (CubismFramework.isInitialized()) CubismFramework.dispose()
        if (CubismFramework.isStarted()) CubismFramework.cleanUp()
        started = false
    }

    val isReady: Boolean get() = started
}
