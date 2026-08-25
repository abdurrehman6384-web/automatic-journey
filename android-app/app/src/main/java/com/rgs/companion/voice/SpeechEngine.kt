package com.rgs.companion.voice

import android.content.Context
import android.content.Intent
import android.os.Bundle
import android.speech.RecognitionListener
import android.speech.RecognizerIntent
import android.speech.SpeechRecognizer
import android.speech.tts.TextToSpeech
import android.speech.tts.UtteranceProgressListener
import android.util.Log
import com.rgs.companion.live2d.LipSync
import java.util.Locale
import java.util.concurrent.atomic.AtomicInteger

/**
 * Text-to-speech and speech-to-text, with lip-sync wired in.
 *
 * ## Lip-sync strategy
 * [TextToSpeech] exposes no amplitude data, and capturing the output would need
 * `AudioPlaybackCapture` (API 29+, and it cannot capture your own TTS reliably).
 * So lip-sync is driven by [LipSync]'s syllable-timed envelope, started from
 * `onStart` and stopped from `onDone`. It looks right, costs nothing, and works
 * on every TTS engine.
 *
 * If you use a neural voice that gives you an audio file (ElevenLabs, XTTS),
 * play it through `AudioTrack`, feed the PCM to
 * [com.rgs.companion.live2d.AudioRmsTap], and call [LipSync.setLevel] instead --
 * that path gives true amplitude-driven lip-sync.
 *
 * ## Threading
 * `TextToSpeech` callbacks arrive on a binder thread. [mouthLevel] is the only
 * thing the GL thread reads, and it is a volatile float, so no locking is needed.
 */
class SpeechEngine(private val context: Context) {

    var lipSync = LipSync()
        private set

    /** Read once per frame by the renderer. 0f when she is not speaking. */
    @Volatile
    var mouthLevel: Float = 0f
        private set

    /** Fired with each final transcription. */
    var onTranscript: ((String) -> Unit)? = null

    /** Fired when listening starts/stops, so the UI can show a mic indicator. */
    var onListeningChanged: ((Boolean) -> Unit)? = null

    private var tts: TextToSpeech? = null
    private var stt: SpeechRecognizer? = null
    private var ready = false
    private val utteranceSeq = AtomicInteger(0)

    var locale: Locale = Locale.US
    var pitch: Float = 1.15f          // slightly higher reads as warmer
    var speechRate: Float = 1.0f

    // ------------------------------------------------------------------
    // setup
    // ------------------------------------------------------------------
    /**
     * Initialise both engines. Safe to call from `Application.onCreate`; TTS
     * initialisation is asynchronous, so [ready] flips later.
     */
    fun init() {
        tts = TextToSpeech(context) { status ->
            if (status == TextToSpeech.SUCCESS) {
                tts?.let { engine ->
                    engine.language = locale
                    engine.setPitch(pitch)
                    engine.setSpeechRate(speechRate)
                    engine.setOnUtteranceProgressListener(utteranceListener)
                    ready = true
                }
            } else {
                Log.e(TAG, "TTS init failed (status=$status). Is a TTS engine installed?")
            }
        }
    }

    fun shutdown() {
        stopListening()
        tts?.stop()
        tts?.shutdown()
        tts = null
        stt?.destroy()
        stt = null
        ready = false
    }

    // ------------------------------------------------------------------
    // TTS
    // ------------------------------------------------------------------
    /**
     * Speak [text]. Interrupts anything currently playing, which is what you want
     * in a chat: the newest message is the one that matters.
     */
    fun speak(text: String) {
        val engine = tts
        if (engine == null || !ready) {
            Log.w(TAG, "TTS not ready; dropping utterance")
            return
        }
        if (text.isBlank()) return

        val id = "u${utteranceSeq.incrementAndGet()}"
        val params = Bundle()

        // QUEUE_FLUSH: a new reply should not queue up behind the last one.
        engine.speak(text, TextToSpeech.QUEUE_FLUSH, params, id)
        // Lip-sync starts in onStart, which fires on the binder thread.
    }

    fun stopSpeaking() {
        tts?.stop()
        lipSync.onUtteranceEnd()
        mouthLevel = 0f
    }

    private val utteranceListener = object : UtteranceProgressListener() {
        override fun onStart(utteranceId: String?) {
            // We do not have the text here, so start a generic envelope; the
            // caller can pre-seed it via speakWithLipSync() for tighter timing.
            lipSync.onUtteranceStart(lastSpokenText)
        }

        override fun onDone(utteranceId: String?) {
            lipSync.onUtteranceEnd()
            mouthLevel = 0f
        }

        @Deprecated("Deprecated in Java")
        override fun onError(utteranceId: String?) {
            lipSync.onUtteranceEnd()
            mouthLevel = 0f
        }
    }

    @Volatile
    private var lastSpokenText: String = ""

    /** Preferred entry point: seeds the lip-sync envelope with the real text. */
    fun speakWithLipSync(text: String) {
        lastSpokenText = text
        speak(text)
    }

    /**
     * Call once per frame from the GL thread (or a coroutine) to move the
     * envelope into [mouthLevel], which the renderer reads.
     */
    fun pumpLipSync() {
        mouthLevel = lipSync.sample()
    }

    // ------------------------------------------------------------------
    // STT
    // ------------------------------------------------------------------
    /**
     * Start listening. Requires `RECORD_AUDIO`.
     *
     * [SpeechRecognizer] is only available when a recognition service is present
     * (Google app on most devices). We check rather than crash, and callers should
     * fall back to typed input when this returns false.
     */
    fun startListening(languageTag: String = "en-US"): Boolean {
        if (!SpeechRecognizer.isRecognitionAvailable(context)) {
            Log.w(TAG, "no SpeechRecognizer service on this device")
            return false
        }

        stopListening()
        val recognizer = SpeechRecognizer.createSpeechRecognizer(context)
        stt = recognizer

        recognizer.setRecognitionListener(object : RecognitionListener {
            override fun onReadyForSpeech(params: Bundle?) {
                onListeningChanged?.invoke(true)
            }

            override fun onBeginningOfSpeech() {}
            override fun onRmsChanged(rmsdB: Float) {}
            override fun onBufferReceived(buffer: ByteArray?) {}
            override fun onEndOfSpeech() {}

            override fun onError(error: Int) {
                Log.d(TAG, "STT error $error")
                onListeningChanged?.invoke(false)
            }

            override fun onResults(results: Bundle?) {
                val list = results?.getStringArrayList(SpeechRecognizer.RESULTS_RECOGNITION)
                val best = list?.firstOrNull()
                if (!best.isNullOrBlank()) onTranscript?.invoke(best)
                onListeningChanged?.invoke(false)
            }

            override fun onPartialResults(partialResults: Bundle?) {}
            override fun onEvent(eventType: Int, params: Bundle?) {}
        })

        val intent = Intent(RecognizerIntent.ACTION_RECOGNIZE_SPEECH).apply {
            putExtra(RecognizerIntent.EXTRA_LANGUAGE_MODEL,
                RecognizerIntent.LANGUAGE_MODEL_FREE_FORM)
            putExtra(RecognizerIntent.EXTRA_LANGUAGE, languageTag)
            putExtra(RecognizerIntent.EXTRA_MAX_RESULTS, 1)
            putExtra(RecognizerIntent.EXTRA_PARTIAL_RESULTS, false)
        }
        recognizer.startListening(intent)
        return true
    }

    fun stopListening() {
        stt?.let {
            runCatching { it.stopListening() }
            runCatching { it.destroy() }
        }
        stt = null
        onListeningChanged?.invoke(false)
    }

    private companion object {
        const val TAG = "SpeechEngine"
    }
}
