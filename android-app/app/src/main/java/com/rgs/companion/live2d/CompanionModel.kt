package com.rgs.companion.live2d

import android.util.Log
import com.live2d.sdk.cubism.framework.CubismDefaultParameterId.ParameterId
import com.live2d.sdk.cubism.framework.CubismFramework
import com.live2d.sdk.cubism.framework.CubismModelSettingJson
import com.live2d.sdk.cubism.framework.ICubismModelSetting
import com.live2d.sdk.cubism.framework.effect.CubismBreath
import com.live2d.sdk.cubism.framework.effect.CubismEyeBlink
import com.live2d.sdk.cubism.framework.effect.CubismLook
import com.live2d.sdk.cubism.framework.id.CubismId
import com.live2d.sdk.cubism.framework.model.CubismMoc
import com.live2d.sdk.cubism.framework.model.CubismUserModel
import com.live2d.sdk.cubism.framework.motion.ACubismMotion
import com.live2d.sdk.cubism.framework.motion.CubismBreathUpdater
import com.live2d.sdk.cubism.framework.motion.CubismExpressionUpdater
import com.live2d.sdk.cubism.framework.motion.CubismEyeBlinkUpdater
import com.live2d.sdk.cubism.framework.motion.CubismLookUpdater
import com.live2d.sdk.cubism.framework.motion.CubismMotion
import com.live2d.sdk.cubism.framework.motion.CubismPhysicsUpdater
import com.live2d.sdk.cubism.framework.motion.CubismPoseUpdater
import com.live2d.sdk.cubism.framework.rendering.android.CubismRendererAndroid

/**
 * Loads and animates one `.model3.json` model from assets.
 *
 * Kotlin port of the official sample's `LAppModel`, trimmed to what a companion
 * app needs: idle motion, expressions, lip-sync, blink, breath, physics, pose
 * and hit-testing. Every framework call below was checked against
 * `CubismJavaFramework` source (protected members of `CubismUserModel` and
 * `ICubismModelSetting`), because those APIs are easy to guess wrong.
 *
 * **All of this runs on the GL thread.**
 *
 * @param homeDir directory inside assets, e.g. `"models/hiyori/"` (trailing slash)
 * @param fileName e.g. `"hiyori.model3.json"`
 */
class CompanionModel(
    private val homeDir: String,
    private val fileName: String,
) : CubismUserModel() {

    /** `CubismUserModel` has no `modelSetting` field -- the sample owns its own. */
    private var modelSetting: ICubismModelSetting? = null

    private val expressions = LinkedHashMap<String, ACubismMotion>()
    private val motions = HashMap<String, CubismMotion>()
    private val hitAreas = LinkedHashMap<String, CubismId>()

    private var expressionNamesCache: List<String> = emptyList()
    private var motionGroupsCache: List<String> = emptyList()

    private var userTimeSeconds = 0f
    private var motionUpdated = false

    @Volatile
    var lipSyncValue: Float = 0f
        private set

    val isLoaded: Boolean get() = isInitialized

    // ------------------------------------------------------------------
    // setup
    // ------------------------------------------------------------------
    /**
     * Parse `model3.json`, build the moc/model, wire up effects, preload
     * expressions. Idempotent -- safe to call every time a surface is created.
     */
    fun setup() {
        if (isInitialized) return

        val setting = CubismModelSettingJson(readBytes(homeDir + fileName))
        modelSetting = setting

        // ── moc + model ────────────────────────────────────────────────
        // loadModel() creates both the moc and the model for us.
        val mocName = setting.getModelFileName()
        require(mocName.isNotEmpty()) { "$homeDir$fileName declares no moc3 file" }
        val mocBytes = readBytes(homeDir + mocName)
            ?: error("could not read moc: $homeDir$mocName")
        mocConsistency = CubismMoc.hasMocConsistency(mocBytes)
        loadModel(mocBytes, mocConsistency)

        setupRenderer(CubismRendererAndroid.create())

        // ── physics + pose ─────────────────────────────────────────────
        setting.getPhysicsFileName().takeIf { it.isNotEmpty() }?.let {
            loadPhysics(readBytes(homeDir + it))
            if (physics != null) updateScheduler.addUpdatableList(CubismPhysicsUpdater(physics))
        }
        setting.getPoseFileName().takeIf { it.isNotEmpty() }?.let {
            loadPose(readBytes(homeDir + it))
            if (pose != null) updateScheduler.addUpdatableList(CubismPoseUpdater(pose))
        }

        // ── blink / breath / look ──────────────────────────────────────
        eyeBlink = CubismEyeBlink.create(setting)
        if (eyeBlink != null) {
            eyeBlink.setBlinkingInterval(3.5f)
            updateScheduler.addUpdatableList(CubismEyeBlinkUpdater(eyeBlink))
        }

        breath = CubismBreath.create()?.also { b ->
            val ids = CubismFramework.getIdManager()
            b.setParameters(
                listOf(
                    CubismBreath.BreathParameterData(
                        ids.getId(ParameterId.ANGLE_X.getId()), 0.0f, 15.0f, 6.5345f, 0.5f,
                    ),
                    CubismBreath.BreathParameterData(
                        ids.getId(ParameterId.ANGLE_Y.getId()), 0.0f, 8.0f, 3.5345f, 0.5f,
                    ),
                    CubismBreath.BreathParameterData(
                        ids.getId(ParameterId.BODY_ANGLE_X.getId()), 0.0f, 10.0f, 15.0f, 0.5f,
                    ),
                    CubismBreath.BreathParameterData(
                        ids.getId(ParameterId.BREATH.getId()), 0.5f, 0.5f, 3.2345f, 1.0f,
                    ),
                ),
            )
            updateScheduler.addUpdatableList(CubismBreathUpdater(b))
        }

        CubismLook.create()?.let { updateScheduler.addUpdatableList(CubismLookUpdater(it)) }

        // ── expressions ────────────────────────────────────────────────
        for (i in 0 until setting.getExpressionCount()) {
            val name = setting.getExpressionName(i) ?: continue
            val file = setting.getExpressionFileName(i) ?: continue
            if (file.isEmpty()) continue
            val motion = loadExpression(readBytes(homeDir + file)) ?: continue
            expressions[name] = motion
        }
        updateScheduler.addUpdatableList(CubismExpressionUpdater(expressionManager))
        expressionNamesCache = expressions.keys.toList()

        // ── motion groups (files are loaded lazily on first play) ──────
        motionGroupsCache = (0 until setting.getMotionGroupCount())
            .mapNotNull { setting.getMotionGroupName(it) }

        // ── hit areas ("Head", "Body", ...) ────────────────────────────
        for (i in 0 until setting.getHitAreasCount()) {
            val id = setting.getHitAreaId(i) ?: continue
            val name = setting.getHitAreaName(i) ?: continue
            hitAreas[name] = id
        }

        isInitialized(true)
        isUpdated(true)
        Log.d(
            TAG,
            "ready: ${expressions.size} expressions, ${motionGroupsCache.size} motion groups, " +
                "hit areas ${hitAreas.keys}",
        )
    }

    // ------------------------------------------------------------------
    // per frame
    // ------------------------------------------------------------------
    /**
     * Advance by [deltaSeconds]. Mirrors the sample's `update()`:
     * load saved params -> run motions -> save -> late updaters -> commit.
     */
    fun update(deltaSeconds: Float) {
        if (!isInitialized || model == null) return
        userTimeSeconds += deltaSeconds
        motionUpdated = false

        model.loadParameters()

        if (motionManager.isFinished()) {
            startRandomMotion(GROUP_IDLE, MotionPriority.IDLE.value)
        } else {
            motionUpdated = motionManager.updateMotion(model, deltaSeconds)
        }

        model.saveParameters()
        opacity = model.getModelOpacity()

        // blink, expression, look, breath, physics, pose
        updateScheduler.onLateUpdate(model, deltaSeconds)

        applyLipSync()
        model.update()
    }

    /**
     * Drive `ParamMouthOpenY` from the current TTS volume.
     *
     * Applied *after* `onLateUpdate` so it wins over whatever the running motion
     * wrote -- otherwise a talking animation silently swallows your lip-sync.
     */
    private fun applyLipSync() {
        val v = lipSyncValue.coerceIn(0f, 1f)
        if (v <= 0f && !motionUpdated) return
        lastLipSyncValue = v
        model.setParameterValue(
            CubismFramework.getIdManager().getId(ParameterId.MOUTH_OPEN_Y.getId()),
            v,
            1.0f,
        )
    }

    /** Feed the current TTS volume, 0..1. Safe from any thread. */
    fun setLipSync(value: Float) {
        lipSyncValue = value.coerceIn(0f, 1f)
    }

    /** Called by the renderer with drag deltas; drives ParamAngleX/Y + eyeballs. */
    fun setDrag(x: Float, y: Float) = setDragging(x, y)

    // ------------------------------------------------------------------
    // expressions + motions
    // ------------------------------------------------------------------
    fun setExpression(name: String): Boolean {
        val motion = expressions[name] ?: run {
            Log.w(TAG, "no expression '$name'. Available: $expressionNamesCache")
            return false
        }
        expressionManager.startMotionPriority(motion, MotionPriority.FORCE.value)
        return true
    }

    fun expressionNames(): List<String> = expressionNamesCache

    fun motionGroups(): List<String> = motionGroupsCache

    /**
     * Play `group[index]`, e.g. `startMotion("TapBody", 0, NORMAL.value)`.
     * @return the motion id, or -1 if it could not start.
     */
    fun startMotion(group: String, index: Int, priority: Int): Int {
        if (priority == MotionPriority.FORCE.value) {
            motionManager.setReservationPriority(priority)
        } else if (!motionManager.reserveMotion(priority)) {
            return -1
        }

        val key = "${group}_$index"
        var motion = motions[key]

        if (motion == null) {
            val setting = modelSetting ?: return -1
            val file = setting.getMotionFileName(group, index)
            if (file.isEmpty()) return -1
            val buffer = readBytes(homeDir + file) ?: return -1
            motion = loadMotion(buffer) ?: return -1
            motion.setFadeInTime(setting.getMotionFadeInTimeValue(group, index))
            motion.setFadeOutTime(setting.getMotionFadeOutTimeValue(group, index))
            motions[key] = motion
        }

        motionManager.setReservationPriority(MotionPriority.NONE.value)
        return motionManager.startMotionPriority(motion, priority)
    }

    private fun startRandomMotion(group: String, priority: Int) {
        val count = modelSetting?.getMotionCount(group) ?: 0
        if (count <= 0) return
        startMotion(group, (Math.random() * count).toInt(), priority)
    }

    // ------------------------------------------------------------------
    // hit testing
    // ------------------------------------------------------------------
    /** Which named hit area ("Head", "Body", ...) is at model-space x/y, if any. */
    fun hitTest(x: Float, y: Float): String? =
        hitAreas.entries.firstOrNull { isHit(it.value, x, y) }?.key

    fun hitAreaNames(): Set<String> = hitAreas.keys

    // ------------------------------------------------------------------
    // textures
    // ------------------------------------------------------------------
    /** Texture paths from `model3.json`, in the order the model expects them. */
    fun textureFileNames(): List<String> {
        val setting = modelSetting ?: return emptyList()
        return (0 until setting.getTextureCount()).mapNotNull { i ->
            setting.getTextureFileName(i)?.takeIf { it.isNotEmpty() }?.let { homeDir + it }
        }
    }

    /** Bind an already-uploaded GL texture to a model texture slot. */
    fun bindTexture(index: Int, glTextureName: Int, premultipliedAlpha: Boolean) {
        val renderer = getRenderer<CubismRendererAndroid>()
        renderer.bindTexture(index, glTextureName)
        renderer.isPremultipliedAlpha(premultipliedAlpha)
    }

    /** The renderer, for setting the MVP matrix before drawing. */
    fun androidRenderer(): CubismRendererAndroid = getRenderer()

    /** Free GL + native resources. Call when the surface is destroyed. */
    fun releaseAll() {
        motions.clear()
        expressions.clear()
        hitAreas.clear()
        deleteRenderer()
    }

    // ------------------------------------------------------------------
    private fun readBytes(path: String): ByteArray? =
        CubismFramework.getLoadFileFunction()?.load(path)

    companion object {
        private const val TAG = "CompanionModel"
        const val GROUP_IDLE = "Idle"
    }
}
