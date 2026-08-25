package com.rgs.companion.companion

import android.util.Log
import com.rgs.companion.chat.LlmClient
import com.rgs.companion.control.PhoneControl
import kotlinx.coroutines.sync.Mutex
import kotlinx.coroutines.sync.withLock
import java.time.Instant
import java.time.temporal.ChronoUnit

/**
 * The whole companion in one place: persona + memory + LLM + emotion + phone
 * control.
 *
 * ```
 * val agent = CompanionAgent(persona, memory, llm, phoneControl)
 * val reply = agent.send("I had a rough day")
 *
 * reply.text              // "Aww babe, come here. What happened? [affectionate]"
 * reply.emotion           // Emotion.AFFECTIONATE  -> drive the avatar
 * reply.actions           // []                    -> nothing to do on the phone
 * ```
 *
 * Concurrency is serialised with a [Mutex]: a chat app can easily fire two
 * requests (a retry, a proactive ping) and interleaved history writes corrupt
 * the transcript.
 */
class CompanionAgent(
    private val persona: Persona,
    private val memory: MemoryStore,
    private val llm: LlmClient,
    private val phoneControl: PhoneControl? = null,
    private val config: PersonaConfig = PersonaConfig(),
) {
    private val mutex = Mutex()
    private val emotionState = EmotionState()

    @Volatile
    var currentEmotion: Emotion = Emotion.NEUTRAL
        private set

    @Volatile
    var lastInteractionAt: Long = Instant.now().epochSecond
        private set

    /**
     * Send a user message and get her reply.
     *
     * Pipeline: recall memory -> build prompt -> call LLM -> parse text/emotion/
     * actions -> persist turn -> execute safe actions.
     */
    suspend fun send(userMessage: String): CompanionReply = mutex.withLock {
        val nowMs = System.currentTimeMillis()
        lastInteractionAt = Instant.now().epochSecond

        // 1. Memory. Recalled against what they just said, so relevant facts win.
        val facts = memory.recall(userMessage)
        val systemPrompt = persona.buildSystemPrompt(memory.formatForPrompt(facts))
        val history = memory.transcriptMessages()

        // 2. Ask.
        val raw = llm.complete(systemPrompt, history, userMessage)

        // 3. Parse the structured reply.
        val parsed = Persona.parse(raw)

        // 4. Emotion: the LLM's tag wins; otherwise guess from the text.
        val explicit = Emotion.fromTag(parsed.emotionTag)
            .takeIf { parsed.emotionTag != null }
        val inferred = SentimentGuesser.guess(parsed.text)
        val emotion = emotionState.offer(explicit, inferred, nowMs) ?: currentEmotion
        currentEmotion = emotion

        // 5. Persist. The raw text, not the tagged version.
        memory.addTurn("user", userMessage)
        memory.addTurn("assistant", parsed.text, emotion.tag)

        // 6. Phone actions -- confirmations are enforced in PhoneControl, here we
        //    just refuse to run anything at all if control is unavailable.
        val actionResults = if (parsed.actions.isEmpty()) emptyList()
        else parsed.actions.map { executeAction(it) }

        CompanionReply(
            text = parsed.text,
            emotion = emotion,
            actions = parsed.actions,
            actionResults = actionResults,
        )
    }

    /**
     * She starts the conversation.
     *
     * Called from a scheduler (see `proactive/`). The prompt is deliberately
     * different: no user turn, an explicit instruction to be brief and to have a
     * reason for messaging, so she does not spam "hey" every hour.
     */
    suspend fun initiate(reason: ProactiveReason): CompanionReply? = mutex.withLock {
        val hoursSince = ChronoUnit.HOURS.between(
            Instant.ofEpochSecond(lastInteractionAt), Instant.now(),
        )

        val facts = memory.recall("")
        val prompt = buildString {
            appendLine(persona.buildSystemPrompt(memory.formatForPrompt(facts)))
            appendLine()
            appendLine("You are starting the conversation yourself. " +
                "It has been $hoursSince hour(s) since you last talked. " +
                "Reason: ${reason.description}")
            appendLine("Send ONE short message (1-2 sentences). Have a specific reason " +
                "for messaging -- something you remembered, a question about their " +
                "day, something you noticed about the time of day. Do not just say hi.")
            appendLine("If you genuinely have nothing worth saying, reply with exactly: SKIP")
        }

        val raw = try {
            llm.complete(prompt, emptyList(), "(start the conversation)")
        } catch (e: Exception) {
            Log.w(TAG, "proactive generation failed", e)
            return@withLock null
        }

        val parsed = Persona.parse(raw)
        if (parsed.text.isBlank() || parsed.text.equals("SKIP", ignoreCase = true)) {
            return@withLock null
        }

        val emotion = emotionState.offer(
            parsed.emotionTag?.let { Emotion.fromTag(it) },
            SentimentGuesser.guess(parsed.text),
            System.currentTimeMillis(),
        ) ?: Emotion.HAPPY
        currentEmotion = emotion

        memory.addTurn("assistant", parsed.text, emotion.tag)
        lastInteractionAt = Instant.now().epochSecond

        CompanionReply(parsed.text, emotion, emptyList(), emptyList())
    }

    /** Force an emotion from outside (e.g. tapping her head). */
    fun react(emotion: Emotion) {
        emotionState.force(emotion, System.currentTimeMillis())
        currentEmotion = emotion
    }

    /** Called every second-ish to let emotions decay back to neutral. */
    fun tick(): Emotion? {
        val next = emotionState.tick(System.currentTimeMillis())
        if (next != null) currentEmotion = next
        return next
    }

    // ------------------------------------------------------------------
    private suspend fun executeAction(action: String): ActionResult {
        val control = phoneControl
            ?: return ActionResult(action, ok = false, "phone control is not enabled")

        return try {
            val parts = action.trim().split(Regex("\\s+"), limit = 2)
            val verb = parts[0]
            val arg = parts.getOrNull(1).orEmpty()

            val ok = when (verb) {
                "open_app" -> control.openApp(arg)
                "tap_text" -> control.tapByText(arg)
                "type" -> control.typeText(arg)
                "read_screen" -> { control.readScreen(); true }
                "back" -> control.pressBack()
                "home" -> control.pressHome()
                "scroll" -> control.scroll(arg.ifEmpty { "down" })
                else -> {
                    Log.w(TAG, "ignoring unknown action verb: $verb")
                    false
                }
            }
            ActionResult(action, ok, if (ok) null else "action refused or failed")
        } catch (e: Exception) {
            Log.w(TAG, "action failed: $action", e)
            ActionResult(action, ok = false, e.message ?: "failed")
        }
    }

    private companion object {
        const val TAG = "CompanionAgent"
    }
}

data class CompanionReply(
    val text: String,
    val emotion: Emotion,
    val actions: List<String>,
    val actionResults: List<ActionResult>,
)

data class ActionResult(
    val action: String,
    val ok: Boolean,
    val error: String? = null,
)

/** Why she is messaging first. Feeds the proactive prompt. */
enum class ProactiveReason(val description: String) {
    MORNING("it is morning where they are"),
    LATE_NIGHT("it is late at night and they were online recently"),
    IDLE("it has been a while since you talked"),
    REMEMBERED("you remembered something they told you earlier"),
    CHECK_IN("they mentioned something stressful recently"),
}
