package com.opendroid.ai.pet

import com.opendroid.ai.core.agent.AgentState
import kotlinx.coroutines.CoroutineScope
import kotlinx.coroutines.Job
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.collectLatest
import kotlinx.coroutines.launch

/**
 * Wires Toni to OpenDroid's [AgentState] stream in one call.
 *
 * The point of this class is to keep the diff to `OpenDroidAccessibilityService`
 * down to three lines. Without it, the service has to own a coroutine, remember
 * to cancel the job, and remember to cancel the animator -- three things that are
 * easy to get wrong and only show up as a leak or a frozen pet.
 *
 * Usage inside the service:
 * ```
 * private var toni: ToniPetBridge? = null
 *
 * // where the old floating button was created:
 * toni = ToniPetBridge(this, agentLoop.agentState, serviceScope).also { it.start() }
 *
 * // in onServiceConnected / onDestroy:
 * toni?.start()
 * toni?.stop()
 * ```
 */
class ToniPetBridge(
    context: android.content.Context,
    private val agentState: StateFlow<AgentState>,
    private val scope: CoroutineScope,
    hostIsAccessibilityService: Boolean = true,
) {
    val controller = ToniPetController(context, hostIsAccessibilityService)
    private var job: Job? = null

    /**
     * Show the pet and follow the agent state.
     *
     * `collectLatest` rather than `collect`: if the agent flips
     * Thinking -> ExecutingPlan -> Speaking quickly, we only ever render the
     * newest state instead of queueing stale ones behind it.
     */
    fun start() {
        controller.show()
        if (job?.isActive == true) return
        job = scope.launch {
            agentState.collectLatest { state ->
                controller.updateState(state)
                // Mouth animation while she speaks. AgentState.Speaking carries the
                // text; if you have real TTS amplitude, call setMouthOpen() with it
                // instead and this synthetic envelope becomes unnecessary.
                if (state is AgentState.Speaking) {
                    animateTalking(state.text)
                } else {
                    controller.setMouthOpen(0f)
                }
            }
        }
    }

    fun stop() {
        job?.cancel()
        job = null
        controller.hide()
    }

    /**
     * Drive the mouth from the text length when no audio amplitude is available.
     *
     * OpenDroid's `TextToSpeechEngine` does not expose per-buffer RMS, so this
     * approximates speech rhythm from syllable count. It is good enough to read
     * as talking at 72dp; wire real amplitude here if you add it.
     */
    private suspend fun animateTalking(text: String) {
        val syllables = estimateSyllables(text).coerceAtLeast(1)
        val perSyllableMs = 240L
        var i = 0
        while (i < syllables) {
            // Open then close, so the mouth visibly works rather than sitting open.
            controller.setMouthOpen(0.85f)
            kotlinx.coroutines.delay(perSyllableMs / 2)
            controller.setMouthOpen(0.15f)
            kotlinx.coroutines.delay(perSyllableMs / 2)
            i++
        }
        controller.setMouthOpen(0f)
    }

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
            count.coerceAtLeast(1)
        }
    }
}
