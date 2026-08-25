package com.rgs.companion.live2d

/**
 * Motion priority, matching the convention used by the official Cubism samples
 * (`LAppDefine.Priority`). Higher numbers win when a motion is already playing.
 */
enum class MotionPriority(val value: Int) {
    NONE(0),
    IDLE(1),
    NORMAL(2),
    FORCE(3),
}

/** A motion request handed from the UI thread to the GL thread. */
data class PendingMotion(
    val group: String,
    val index: Int,
    val priority: MotionPriority = MotionPriority.NORMAL,
)
