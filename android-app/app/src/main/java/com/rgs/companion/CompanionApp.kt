package com.rgs.companion

import android.app.Application
import android.util.Log

/**
 * Application entry point.
 *
 * Kept deliberately light: no work that blocks startup. The heavy things (Room,
 * TTS init, Cubism bootstrap) are all lazy -- Room on first query, TTS in
 * [com.rgs.companion.voice.SpeechEngine.init], Cubism on first GL surface.
 *
 * Deliberately *not* done here: [com.live2d.sdk.cubism.framework.CubismFramework.startUp].
 * It must run on the GL thread, so it lives in
 * [com.rgs.companion.live2d.Live2DRenderer.onSurfaceCreated].
 */
class CompanionApp : Application() {

    override fun onCreate() {
        super.onCreate()
        initInstance(this)
        Log.i(TAG, "companion starting; model dir = assets/models/")
    }

    companion object {
        private const val TAG = "CompanionApp"

        lateinit var instance: CompanionApp
            private set

        /**
         * Assigned exactly once, from [CompanionApp.onCreate].
         *
         * Going through this function rather than assigning `instance` directly
         * keeps `private set` intact -- the setter stays private to the companion
         * object, which is the only place that may write it.
         */
        internal fun initInstance(app: CompanionApp) {
            instance = app
        }
    }
}
