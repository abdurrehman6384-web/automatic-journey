package com.opendroid.ai.pet

import android.animation.ValueAnimator
import android.content.Context
import android.graphics.Canvas
import android.graphics.Color
import android.graphics.Paint
import android.graphics.Path
import android.graphics.RectF
import android.view.View
import com.opendroid.ai.core.agent.AgentState
import kotlin.math.sin

/**
 * Toni -- the on-screen companion pet, drawn entirely with Canvas.
 *
 * ## Why Canvas instead of a Live2D model or a sprite sheet
 * Zero assets, zero licence, zero download. It renders inside the existing
 * 64dp accessibility overlay and animates at whatever frame rate the window
 * gets. If you later want Live2D, swap this View for a `GLSurfaceView` behind
 * the same [updateState] contract -- the controller and the agent wiring do not
 * change.
 *
 * ## What drives her
 * [updateState] maps OpenDroid's real [AgentState] onto an expression, so the
 * pet is a genuine status indicator rather than decoration:
 *
 * | AgentState | Toni |
 * |---|---|
 * | `Idle` | relaxed, slow breathing, occasional blink |
 * | `Thinking` | looks up, eyes narrowed, faster bob |
 * | `Listening` | wide eyes, perked up, leaning in |
 * | `PlanProposed` | excited, big smile, bounce |
 * | `ExecutingPlan` | focused, determined |
 * | `Speaking` | mouth animates in time with speech |
 * | `Error` | worried, ears down |
 *
 * ## Animation model
 * One [ValueAnimator] running 0..1 forever drives everything: the bob, the
 * blink phase and the mouth. That is deliberate -- a single time source means
 * the parts can never drift out of phase, and there is exactly one thing to
 * cancel in [onDetachedFromWindow].
 */
class ToniPetView(context: Context) : View(context) {

    private val bodyPaint = Paint(Paint.ANTI_ALIAS_FLAG)
    private val bellyPaint = Paint(Paint.ANTI_ALIAS_FLAG)
    private val eyePaint = Paint(Paint.ANTI_ALIAS_FLAG)
    private val mouthPaint = Paint(Paint.ANTI_ALIAS_FLAG).apply {
        style = Paint.Style.STROKE
        strokeCap = Paint.Cap.ROUND
    }
    private val cheekPaint = Paint(Paint.ANTI_ALIAS_FLAG)
    private val glowPaint = Paint(Paint.ANTI_ALIAS_FLAG)
    private val earPath = Path()

    private var state: PetMood = PetMood.IDLE
    private var phase = 0f                  // 0..1, the single animation clock
    private var blinkT = 0f                 // 0..1 while a blink is in progress
    private var nextBlinkAt = 2_400L
    private var lastBlinkCheck = 0L
    private var tapBounce = 0f              // decays after a tap

    /** 0..1. Non-zero makes the mouth open; set from TTS amplitude if you have it. */
    var mouthOpen: Float = 0f

    /** Shrink to a sleeping ball. The controller toggles this. */
    var minimized: Boolean = false
        set(value) {
            field = value
            invalidate()
        }

    private val animator = ValueAnimator.ofFloat(0f, 1f).apply {
        duration = 3_000
        repeatCount = ValueAnimator.INFINITE
        repeatMode = ValueAnimator.RESTART
        addUpdateListener {
            phase = it.animatedValue as Float
            tickBlink()
            tapBounce = (tapBounce * 0.90f).coerceAtLeast(0f)
            invalidate()
        }
    }

    init {
        setLayerType(LAYER_TYPE_SOFTWARE, null)     // Path + soft edges render fine
        applyMoodColors(PetMood.IDLE)
    }

    // ------------------------------------------------------------------
    // public API
    // ------------------------------------------------------------------
    /** Map OpenDroid's agent state onto a mood and repaint. */
    fun updateState(agentState: AgentState) {
        val mood = moodFor(agentState)
        if (mood == state) return
        state = mood
        applyMoodColors(mood)
        animator.duration = mood.cycleMs
        invalidate()
    }

    /** Direct override, e.g. from a chat emotion tag. */
    fun setMood(mood: PetMood) {
        if (mood == state) return
        state = mood
        applyMoodColors(mood)
        animator.duration = mood.cycleMs
        invalidate()
    }

    /** Call on tap: she reacts. */
    fun react() {
        tapBounce = 1f
        invalidate()
    }

    // ------------------------------------------------------------------
    // lifecycle
    // ------------------------------------------------------------------
    override fun onAttachedToWindow() {
        super.onAttachedToWindow()
        if (!animator.isStarted) animator.start()
    }

    override fun onDetachedFromWindow() {
        // One animator, one cancel. Forgetting this leaks the view forever.
        animator.cancel()
        super.onDetachedFromWindow()
    }

    // ------------------------------------------------------------------
    // drawing
    // ------------------------------------------------------------------
    override fun onDraw(canvas: Canvas) {
        super.onDraw(canvas)

        val w = width.toFloat()
        val h = height.toFloat()
        if (w <= 0f || h <= 0f) return

        val scale = if (minimized) 0.62f else 1f
        val bob = sin(phase * Math.PI * 2).toFloat() * (h * 0.022f) * state.bobAmount
        val bounce = tapBounce * h * 0.06f

        val cx = w / 2f
        val cy = h / 2f + bob - bounce
        val r = minOf(w, h) * 0.34f * scale

        drawGlow(canvas, cx, cy, r)
        if (minimized) {
            drawSleeping(canvas, cx, cy, r)
            return
        }

        drawEars(canvas, cx, cy, r)
        drawBody(canvas, cx, cy, r)
        drawFace(canvas, cx, cy, r)
    }

    private fun drawGlow(canvas: Canvas, cx: Float, cy: Float, r: Float) {
        // A soft halo that pulses with the agent's activity. Subtle on purpose:
        // this sits on top of whatever app the user is in.
        val pulse = (sin(phase * Math.PI * 2).toFloat() + 1f) / 2f
        glowPaint.color = withAlpha(state.accent, (30 + pulse * 45).toInt())
        canvas.drawCircle(cx, cy, r * (1.35f + pulse * 0.18f), glowPaint)
    }

    private fun drawEars(canvas: Canvas, cx: Float, cy: Float, r: Float) {
        val perk = state.earPerk                        // -1 droopy .. +1 perked
        val earH = r * (0.55f + 0.25f * perk)
        val spread = r * 0.62f

        for (side in intArrayOf(-1, 1)) {
            earPath.reset()
            val baseX = cx + side * spread * 0.55f
            val baseY = cy - r * 0.62f
            val tipX = cx + side * spread * 1.05f
            val tipY = baseY - earH
            earPath.moveTo(baseX - side * r * 0.20f, baseY + r * 0.10f)
            earPath.quadTo(tipX, tipY - r * 0.1f, baseX + side * r * 0.20f, baseY - r * 0.05f)
            earPath.close()
            canvas.drawPath(earPath, bodyPaint)
        }
    }

    private fun drawBody(canvas: Canvas, cx: Float, cy: Float, r: Float) {
        // Slight squash on the bounce so a tap feels physical.
        val squash = 1f + tapBounce * 0.10f
        val rect = RectF(cx - r, cy - r * squash, cx + r, cy + r / squash)
        canvas.drawOval(rect, bodyPaint)

        val belly = RectF(cx - r * 0.58f, cy - r * 0.18f, cx + r * 0.58f, cy + r * 0.80f)
        canvas.drawOval(belly, bellyPaint)
    }

    private fun drawFace(canvas: Canvas, cx: Float, cy: Float, r: Float) {
        val eyeY = cy - r * (0.18f - state.lookUp * 0.12f)
        val eyeSpread = r * 0.40f
        val eyeR = r * 0.115f * state.eyeOpen

        // Blink closes the eyes to a line rather than removing them, which reads
        // far better at 64dp than a disappearing feature.
        val openness = (1f - blinkT).coerceIn(0f, 1f) * state.eyeOpen

        for (side in intArrayOf(-1, 1)) {
            val ex = cx + side * eyeSpread
            if (openness < 0.15f) {
                canvas.drawLine(ex - eyeR, eyeY, ex + eyeR, eyeY, mouthPaint.also {
                    it.strokeWidth = r * 0.09f
                    it.color = state.line
                })
            } else {
                canvas.drawOval(
                    RectF(ex - eyeR, eyeY - eyeR * openness, ex + eyeR, eyeY + eyeR * openness),
                    eyePaint,
                )
                // Catch-light -- the small white dot that makes eyes look alive.
                canvas.drawCircle(ex - eyeR * 0.35f, eyeY - eyeR * 0.35f * openness,
                    eyeR * 0.34f, bellyPaint)
            }
        }

        drawCheeks(canvas, cx, cy, r)
        drawMouth(canvas, cx, cy, r)
    }

    private fun drawCheeks(canvas: Canvas, cx: Float, cy: Float, r: Float) {
        if (state.blush <= 0f) return
        cheekPaint.color = withAlpha(Color.parseColor("#FF7A9C"), (state.blush * 110).toInt())
        for (side in intArrayOf(-1, 1)) {
            canvas.drawOval(
                RectF(
                    cx + side * r * 0.72f - r * 0.18f, cy + r * 0.05f,
                    cx + side * r * 0.72f + r * 0.18f, cy + r * 0.28f,
                ),
                cheekPaint,
            )
        }
    }

    private fun drawMouth(canvas: Canvas, cx: Float, cy: Float, r: Float) {
        mouthPaint.color = state.line
        mouthPaint.strokeWidth = r * 0.085f
        mouthPaint.style = Paint.Style.STROKE

        val my = cy + r * 0.34f
        val open = (mouthOpen * state.talkAmount).coerceIn(0f, 1f)

        if (open > 0.08f) {
            // Talking: an ellipse whose height tracks the audio/speech envelope.
            mouthPaint.style = Paint.Style.FILL
            canvas.drawOval(
                RectF(cx - r * 0.22f, my - r * 0.10f * open,
                    cx + r * 0.22f, my + r * 0.34f * open),
                mouthPaint,
            )
            mouthPaint.style = Paint.Style.STROKE
        } else {
            // Smile curvature is the mood: positive smiles, negative frowns.
            val curve = r * 0.22f * state.smile
            val path = Path().apply {
                moveTo(cx - r * 0.24f, my)
                quadTo(cx, my + curve, cx + r * 0.24f, my)
            }
            canvas.drawPath(path, mouthPaint)
        }
    }

    private fun drawSleeping(canvas: Canvas, cx: Float, cy: Float, r: Float) {
        canvas.drawCircle(cx, cy + r * 0.15f, r * 0.95f, bodyPaint)
        // Closed eyes.
        eyePaint.color = state.line
        for (side in intArrayOf(-1, 1)) {
            val ex = cx + side * r * 0.34f
            val ey = cy + r * 0.05f
            canvas.drawLine(ex - r * 0.14f, ey, ex + r * 0.14f, ey, mouthPaint.also {
                it.strokeWidth = r * 0.08f
                it.color = state.line
            })
        }
        // A "z" that drifts up, so minimized still reads as alive.
        val drift = phase
        val zx = cx + r * 0.75f
        val zy = cy - r * (0.55f + drift * 0.55f)
        mouthPaint.color = withAlpha(state.accent, ((1f - drift) * 200).toInt())
        // Paint.textSize defaults to 0, so without this the "z" is invisible.
        mouthPaint.textSize = r * 0.55f
        mouthPaint.strokeWidth = r * 0.09f
        canvas.drawText("z", zx, zy, mouthPaint.also { it.style = Paint.Style.FILL })
        mouthPaint.style = Paint.Style.STROKE
    }

    // ------------------------------------------------------------------
    // blink
    // ------------------------------------------------------------------
    /**
     * Blinks on a randomised interval rather than a fixed one. A metronomic
     * blink is the fastest way to make a character look mechanical.
     */
    private fun tickBlink() {
        val now = System.currentTimeMillis()
        if (blinkT > 0f) {
            blinkT = (blinkT - 0.16f).coerceAtLeast(0f)
            return
        }
        if (now - lastBlinkCheck > nextBlinkAt) {
            lastBlinkCheck = now
            blinkT = 1f
            nextBlinkAt = 1_800L + (Math.random() * 3_200L).toLong()
        }
    }

    // ------------------------------------------------------------------
    private fun applyMoodColors(mood: PetMood) {
        bodyPaint.color = mood.body
        bellyPaint.color = mood.belly
        eyePaint.color = mood.line
        cheekPaint.color = mood.accent
    }

    private fun withAlpha(color: Int, alpha: Int): Int =
        Color.argb(alpha.coerceIn(0, 255), Color.red(color), Color.green(color), Color.blue(color))

    companion object {
        /** Map OpenDroid's sealed [AgentState] onto a mood. */
        fun moodFor(state: AgentState): PetMood = when (state) {
            is AgentState.Idle -> PetMood.IDLE
            is AgentState.Thinking -> PetMood.THINKING
            is AgentState.Listening -> PetMood.LISTENING
            is AgentState.PlanProposed -> PetMood.EXCITED
            is AgentState.ExecutingPlan -> PetMood.FOCUSED
            is AgentState.Speaking -> PetMood.TALKING
            is AgentState.Error -> PetMood.WORRIED
        }
    }
}

/**
 * Toni's moods. Each one carries its whole look, so adding a mood is one enum
 * entry -- no branching in the draw code.
 *
 * @param smile      -1 frown .. +1 grin
 * @param eyeOpen    0 squint .. 1.4 wide
 * @param earPerk    -1 droopy .. +1 perked
 * @param lookUp     0 level .. 1 looking up
 * @param bobAmount  idle motion multiplier
 * @param talkAmount how strongly audio drives the mouth
 * @param blush      0 none .. 1 full
 */
enum class PetMood(
    val body: Int,
    val belly: Int,
    val line: Int,
    val accent: Int,
    val smile: Float,
    val eyeOpen: Float,
    val earPerk: Float,
    val lookUp: Float,
    val bobAmount: Float,
    val talkAmount: Float,
    val blush: Float,
    val cycleMs: Long,
) {
    IDLE(
        body = Color.parseColor("#7C5CFF"), belly = Color.parseColor("#EDE7FF"),
        line = Color.parseColor("#2B1B5E"), accent = Color.parseColor("#FF7A9C"),
        smile = 0.55f, eyeOpen = 1.0f, earPerk = 0.25f, lookUp = 0.0f,
        bobAmount = 1.0f, talkAmount = 0f, blush = 0.25f, cycleMs = 3_000,
    ),
    THINKING(
        body = Color.parseColor("#6A7BFF"), belly = Color.parseColor("#E6EAFF"),
        line = Color.parseColor("#1F2A5E"), accent = Color.parseColor("#9BB0FF"),
        smile = 0.10f, eyeOpen = 0.65f, earPerk = 0.55f, lookUp = 0.9f,
        bobAmount = 1.6f, talkAmount = 0f, blush = 0.1f, cycleMs = 1_100,
    ),
    LISTENING(
        body = Color.parseColor("#31C6A8"), belly = Color.parseColor("#DFFBF4"),
        line = Color.parseColor("#0E4A3E"), accent = Color.parseColor("#7CE8CF"),
        smile = 0.35f, eyeOpen = 1.35f, earPerk = 1.0f, lookUp = 0.15f,
        bobAmount = 1.3f, talkAmount = 0f, blush = 0.35f, cycleMs = 1_600,
    ),
    EXCITED(
        body = Color.parseColor("#FF6FA5"), belly = Color.parseColor("#FFE3EE"),
        line = Color.parseColor("#5E1030"), accent = Color.parseColor("#FFC2D6"),
        smile = 1.0f, eyeOpen = 1.2f, earPerk = 1.0f, lookUp = 0.25f,
        bobAmount = 2.2f, talkAmount = 0f, blush = 0.9f, cycleMs = 800,
    ),
    FOCUSED(
        body = Color.parseColor("#4E8CFF"), belly = Color.parseColor("#DCE9FF"),
        line = Color.parseColor("#12294F"), accent = Color.parseColor("#8FB6FF"),
        smile = 0.20f, eyeOpen = 0.85f, earPerk = 0.7f, lookUp = 0.35f,
        bobAmount = 0.7f, talkAmount = 0f, blush = 0.05f, cycleMs = 2_000,
    ),
    TALKING(
        body = Color.parseColor("#8A5CFF"), belly = Color.parseColor("#EFE6FF"),
        line = Color.parseColor("#2E1B5E"), accent = Color.parseColor("#FF8FB1"),
        smile = 0.65f, eyeOpen = 1.05f, earPerk = 0.6f, lookUp = 0.1f,
        bobAmount = 1.15f, talkAmount = 1.0f, blush = 0.45f, cycleMs = 1_400,
    ),
    WORRIED(
        body = Color.parseColor("#8E8EA3"), belly = Color.parseColor("#E4E4EC"),
        line = Color.parseColor("#33333F"), accent = Color.parseColor("#B0B0C0"),
        smile = -0.55f, eyeOpen = 1.15f, earPerk = -0.85f, lookUp = 0.0f,
        bobAmount = 0.45f, talkAmount = 0f, blush = 0f, cycleMs = 2_600,
    ),
    SLEEPING(
        body = Color.parseColor("#5A5478"), belly = Color.parseColor("#D8D5E6"),
        line = Color.parseColor("#25223A"), accent = Color.parseColor("#8F89B5"),
        smile = 0.30f, eyeOpen = 0.1f, earPerk = -0.6f, lookUp = 0.0f,
        bobAmount = 0.35f, talkAmount = 0f, blush = 0.1f, cycleMs = 4_200,
    ),
}
