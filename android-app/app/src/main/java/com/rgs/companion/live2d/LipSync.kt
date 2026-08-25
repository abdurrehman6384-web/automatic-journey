package com.rgs.companion.live2d

import android.media.MediaPlayer
import android.speech.tts.UtteranceProgressListener
import kotlin.math.ln
import kotlin.math.max
import kotlin.math.sqrt

/**
 * Turns TTS playback into a 0..1 mouth-open value for `ParamMouthOpenY`.
 *
 * ## Why not just use the TTS callback
 * `UtteranceProgressListener` gives you start/stop events, not amplitude. Some
 * engines expose no volume data at all. So we drive lip-sync from a **synthetic
 * envelope** derived from the utterance text, which works with every TTS engine
 * and needs no audio capture permission.
 *
 * If you play TTS through a [MediaPlayer] (e.g. ElevenLabs audio), plug real RMS
 * values into [setLevel] instead -- see `AudioRmsTap` at the bottom.
 *
 * ## Usage
 * ```
 * val lipSync = LipSync()
 * lipSync.onUtteranceStart("Hey, I missed you.")
 * // each frame:
 * live2dView.setMouthOpen(lipSync.sample())
 * ```
 */
class LipSync {

    @Volatile
    private var active = false

    @Volatile
    private var manualLevel: Float = -1f

    private var startNanos = 0L
    private var syllables: Int = 1
    private var durationMs: Long = 1000L

    /**
     * Begin animating the mouth for [text].
     *
     * Syllable count drives the flap rate: English averages ~2.5 syllables/sec in
     * natural speech, and [ESTIMATED_MS_PER_SYLLABLE] is tuned to match that.
     */
    fun onUtteranceStart(text: String) {
        val s = estimateSyllables(text)
        syllables = max(s, 1)
        durationMs = max(syllables * ESTIMATED_MS_PER_SYLLABLE, MIN_DURATION_MS)
        startNanos = System.nanoTime()
        active = true
        manualLevel = -1f
    }

    fun onUtteranceEnd() {
        active = false
        manualLevel = -1f
    }

    /**
     * Feed a real amplitude (0..1) when you have decoded audio. Takes precedence
     * over the synthetic envelope.
     */
    fun setLevel(level: Float) {
        manualLevel = level.coerceIn(0f, 1f)
    }

    /**
     * Current mouth-open value, 0..1. Call once per frame from the GL thread.
     *
     * The envelope is a smoothed rectified sine at the syllable rate, with a
     * little pseudo-random modulation so it does not look like a metronome.
     */
    fun sample(): Float {
        manualLevel.takeIf { it >= 0f }?.let { return it }
        if (!active) return 0f

        val elapsedMs = (System.nanoTime() - startNanos) / 1_000_000
        if (elapsedMs > durationMs) {
            active = false
            return 0f
        }

        val t = elapsedMs.toFloat() / durationMs                       // 0..1
        val rate = syllables.toFloat()                                  // flaps over the utterance
        val sine = (kotlin.math.sin(t * rate * Math.PI * 2).toFloat() + 1f) / 2f

        // Taper in and out so the mouth does not snap open or shut.
        val envelope = when {
            t < 0.08f -> t / 0.08f
            t > 0.90f -> (1f - t) / 0.10f
            else -> 1f
        }

        // Vary the amplitude per "syllable" so it reads as speech, not a buzz.
        val wobble = 0.65f + 0.35f * pseudoRandom((t * rate).toInt())

        return (sine * envelope * wobble).coerceIn(0f, 1f)
    }

    /** Rough English syllable count: vowel groups, minus silent-e and diphthongs. */
    private fun estimateSyllables(text: String): Int {
        val words = text.lowercase().split(Regex("[^a-z']+")).filter { it.isNotBlank() }
        return words.sumOf { word ->
            val w = word.trimEnd('e').ifEmpty { word }
            var count = 0
            var prevVowel = false
            for (c in w) {
                val isVowel = c in "aeiouy"
                if (isVowel && !prevVowel) count++
                prevVowel = isVowel
            }
            max(count, 1)
        }
    }

    /** Deterministic 0..1 noise, so the same utterance animates identically. */
    private fun pseudoRandom(n: Int): Float {
        val x = kotlin.math.sin(n * 12.9898f) * 43758.5453f
        return x - kotlin.math.floor(x)
    }

    private companion object {
        const val ESTIMATED_MS_PER_SYLLABLE = 260L
        const val MIN_DURATION_MS = 400L
    }
}

/**
 * Real amplitude from decoded TTS audio (e.g. a streaming MP3 from ElevenLabs).
 *
 * Android has no built-in RMS callback, so this reads the PCM you are about to
 * hand to an [android.media.AudioTrack] and reports a smoothed level. Call
 * [push] for each buffer you write.
 */
class AudioRmsTap(private val smoothing: Float = 0.35f) {

    private var level = 0f

    /** @param pcm signed 16-bit little-endian samples. */
    fun push(pcm: ByteArray, length: Int = pcm.size): Float {
        if (length < 2) return level
        var sum = 0.0
        var i = 0
        var samples = 0
        while (i + 1 < length) {
            val lo = pcm[i].toInt() and 0xFF
            val hi = pcm[i + 1].toInt()
            val value = (hi shl 8) or lo
            val normalized = value.toDouble() / Short.MAX_VALUE
            sum += normalized * normalized
            samples++
            i += 2
        }
        if (samples == 0) return level

        val rms = sqrt(sum / samples)
        // Log scale reads much closer to perceived loudness than linear RMS.
        val perceived = (ln(1.0 + rms * 40.0) / ln(41.0)).toFloat().coerceIn(0f, 1f)
        level = level * smoothing + perceived * (1f - smoothing)
        return level
    }

    fun reset() {
        level = 0f
    }
}

/**
 * Bridges `TextToSpeech` utterance events into a [LipSync].
 *
 * ```
 * tts.setOnUtteranceProgressListener(lipSync.asUtteranceListener())
 * ```
 */
fun LipSync.asUtteranceListener(): UtteranceProgressListener =
    object : UtteranceProgressListener() {
        override fun onStart(utteranceId: String?) {}
        override fun onDone(utteranceId: String?) { onUtteranceEnd() }
        @Deprecated("Deprecated in Java")
        override fun onError(utteranceId: String?) { onUtteranceEnd() }
    }

@Suppress("unused")
private fun unusedReferenceToKeepMediaPlayerImported(mp: MediaPlayer) = mp.isPlaying
