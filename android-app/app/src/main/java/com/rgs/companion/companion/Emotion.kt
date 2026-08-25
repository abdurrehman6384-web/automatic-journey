package com.rgs.companion.companion

/**
 * Emotional states the companion can be in, and how each one drives the avatar.
 *
 * Two layers of naming, on purpose:
 *
 * - [expressionName] / [motionGroup] are the names used by the **free Live2D
 *   sample models** (Hiyori, Haru, Mark...). If you use your own model, either
 *   name your expressions the same way or add a mapping row here.
 * - [tag] is what the LLM emits inline, e.g. `"I missed you [affectionate]"`.
 *
 * Fallbacks matter more than they look: models routinely ship only 3 of the 8
 * expressions. [CompanionAgent] asks the model which expressions it actually
 * has and degrades to [fallback] rather than silently doing nothing.
 */
enum class Emotion(
    val tag: String,
    val expressionName: String,
    val fallback: String,
    val motionGroup: String,
    /** How long the expression holds before drifting back to neutral. */
    val holdMs: Long,
) {
    NEUTRAL("neutral", "Relaxed", "Idle", "Idle", 0),
    HAPPY("happy", "Smile", "Relaxed", "TapBody", 6_000),
    AFFECTIONATE("affectionate", "Smile", "Relaxed", "TapBody", 8_000),
    SHY("shy", "Relaxed", "Relaxed", "Idle", 5_000),
    PLAYFUL("playful", "Smile", "Relaxed", "TapBody", 6_000),
    SAD("sad", "Sad", "Relaxed", "Idle", 9_000),
    WORRIED("worried", "Angry", "Relaxed", "Idle", 7_000),
    ANGRY("angry", "Angry", "Relaxed", "TapBody", 7_000),
    SURPRISED("surprised", "Surprised", "Relaxed", "TapBody", 3_000),
    SLEEPY("sleepy", "Relaxed", "Relaxed", "Idle", 12_000),
    ;

    companion object {
        private val byTag = entries.associateBy { it.tag }

        fun fromTag(tag: String?): Emotion =
            tag?.lowercase()?.trim()?.let { byTag[it] } ?: NEUTRAL

        /** All tags, for injection into the system prompt. */
        val allTags: List<String> get() = entries.map { it.tag }
    }
}

/**
 * Decides which emotion to show, with two rules that stop the avatar looking
 * broken:
 *
 * 1. **Don't flicker.** A short message should not strobe through three faces.
 *    A new emotion only replaces the current one if it differs *and* the
 *    current one has been held for at least [MIN_HOLD_MS].
 * 2. **Drift back.** Emotions decay to [Emotion.NEUTRAL] rather than freezing,
 *    which is what makes an avatar feel alive instead of stuck.
 */
class EmotionState {

    var current: Emotion = Emotion.NEUTRAL
        private set

    private var sinceMs = 0L

    /**
     * @param explicit emotion the LLM asked for, if any
     * @param inferred emotion guessed from the text when the LLM gave none
     */
    fun offer(explicit: Emotion?, inferred: Emotion, nowMs: Long): Emotion? {
        val target = explicit ?: inferred
        val heldFor = nowMs - sinceMs

        if (target == current) return null
        if (current != Emotion.NEUTRAL && heldFor < MIN_HOLD_MS) return null

        current = target
        sinceMs = nowMs
        return target
    }

    /** Tick the drift. Returns NEUTRAL once when it flips, else null. */
    fun tick(nowMs: Long): Emotion? {
        if (current == Emotion.NEUTRAL) return null
        if (nowMs - sinceMs < current.holdMs) return null
        current = Emotion.NEUTRAL
        sinceMs = nowMs
        return Emotion.NEUTRAL
    }

    fun force(emotion: Emotion, nowMs: Long) {
        current = emotion
        sinceMs = nowMs
    }

    private companion object {
        const val MIN_HOLD_MS = 1_200L
    }
}

/**
 * Lightweight sentiment guess, used when the LLM does not emit an emotion tag.
 *
 * Deliberately dumb and dependency-free: a keyword lexicon plus punctuation
 * cues. It is wrong sometimes; that is fine, because it only picks a face for a
 * chat bubble and the LLM tag overrides it whenever present.
 */
object SentimentGuesser {

    private val positive = setOf(
        "love", "loved", "miss", "missed", "happy", "glad", "yay", "awesome",
        "great", "sweet", "cute", "thank", "thanks", "proud", "excited", "fun",
        "haha", "lol", "good", "nice", "beautiful", "adorable",
    )
    private val negative = setOf(
        "sad", "sorry", "tired", "exhausted", "angry", "mad", "annoyed", "hate",
        "awful", "terrible", "bad", "hurt", "cry", "crying", "lonely", "stressed",
        "anxious", "worried", "sick", "pain",
    )
    private val affectionate = setOf(
        "love you", "miss you", "baby", "babe", "sweetheart", "hug", "kiss",
        "cuddle", "cutie", "darling",
    )

    fun guess(text: String): Emotion {
        val t = text.lowercase()

        if (affectionate.any { it in t }) return Emotion.AFFECTIONATE
        if (negative.any { it in t }) return if ("worried" in t || "anxious" in t) Emotion.WORRIED else Emotion.SAD

        val pos = positive.count { it in t }
        val neg = negative.count { it in t }

        return when {
            pos > neg -> if (t.contains("!!") || t.contains("😂")) Emotion.PLAYFUL else Emotion.HAPPY
            neg > pos -> Emotion.SAD
            t.trimEnd().endsWith("?") -> Emotion.NEUTRAL
            else -> Emotion.NEUTRAL
        }
    }
}
