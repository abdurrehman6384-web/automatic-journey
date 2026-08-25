package com.rgs.companion.chat

import android.app.Application
import androidx.lifecycle.AndroidViewModel
import androidx.lifecycle.viewModelScope
import com.rgs.companion.BuildConfig
import com.rgs.companion.companion.CompanionAgent
import com.rgs.companion.companion.Emotion
import com.rgs.companion.companion.MemoryStore
import com.rgs.companion.companion.Persona
import com.rgs.companion.companion.PersonaConfig
import com.rgs.companion.control.CompanionAccessibilityService
import com.rgs.companion.voice.SpeechEngine
import kotlinx.coroutines.delay
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.asStateFlow
import kotlinx.coroutines.flow.update
import kotlinx.coroutines.launch

/**
 * Glues the UI to [CompanionAgent], [SpeechEngine] and the avatar.
 *
 * One ViewModel, one source of truth ([state]). The Compose screen only reads
 * `state` and calls [send] / [toggleMic]; it holds no logic of its own, which is
 * what keeps the avatar, TTS and chat from drifting apart.
 */
class ChatViewModel(app: Application) : AndroidViewModel(app) {

    private val config = PersonaConfig()          // wire this to your settings screen
    private val persona = Persona(config)
    private val memory = MemoryStore(app)
    private val llm = LlmProvider.GROQ.client(
        apiKey = BuildConfig.LLM_API_KEY,
        model = BuildConfig.LLM_MODEL,
    )

    val speech = SpeechEngine(app).also { it.init() }

    private val agent = CompanionAgent(
        persona = persona,
        memory = memory,
        llm = llm,
        // Resolved lazily: the service may be enabled after the app starts.
        phoneControl = CompanionAccessibilityService.control(),
        config = config,
    )

    private val _state = MutableStateFlow(
        ChatUiState(greeting = "Hey ${config.userNickname}, I'm ${config.name}. " +
            "I've been waiting for you."),
    )
    val state: StateFlow<ChatUiState> = _state.asStateFlow()

    init {
        // Drive the mouth and the emotion decay on a fixed tick. 50ms is 20fps,
        // which is plenty for a mouth and costs far less than a 60fps coroutine.
        viewModelScope.launch {
            while (true) {
                speech.pumpLipSync()
                _state.update { it.copy(mouthLevel = speech.mouthLevel) }
                agent.tick()?.let { _state.update { s -> s.copy(emotion = it) } }
                delay(TICK_MS)
            }
        }

        // Voice input straight into the conversation.
        speech.onTranscript = { text -> viewModelScope.launch { send(text) } }
    }

    // ------------------------------------------------------------------
    fun send(text: String) {
        val message = text.trim()
        if (message.isEmpty() || _state.value.thinking) return

        _state.update {
            it.copy(
                thinking = true,
                messages = it.messages + UiMessage(role = "user", text = message),
            )
        }

        viewModelScope.launch {
            val reply = try {
                agent.send(message)
            } catch (e: Exception) {
                // Never leave the UI stuck in "thinking" -- a dead spinner is
                // worse than an error message.
                _state.update {
                    it.copy(
                        thinking = false,
                        messages = it.messages + UiMessage(
                            role = "error",
                            text = "I couldn't reach the network. " +
                                "(${e.javaClass.simpleName})",
                        ),
                    )
                }
                return@launch
            }

            _state.update {
                it.copy(
                    thinking = false,
                    emotion = reply.emotion,
                    messages = it.messages + UiMessage(
                        role = "assistant",
                        text = reply.text,
                        emotion = reply.emotion.tag,
                    ),
                )
            }

            speech.speakWithLipSync(reply.text)
        }
    }

    fun toggleMic() {
        if (_state.value.listening) {
            speech.stopListening()
        } else {
            val ok = speech.startListening()
            if (!ok) {
                _state.update {
                    it.copy(
                        messages = it.messages + UiMessage(
                            role = "error",
                            text = "Voice input isn't available on this device.",
                        ),
                    )
                }
            }
        }
    }

    /** Tap on the avatar -> a reaction, no LLM round-trip. */
    fun pokeAvatar() {
        agent.react(Emotion.PLAYFUL)
        _state.update { it.copy(emotion = Emotion.PLAYFUL) }
    }

    /** She messages first. Called from the proactive scheduler. */
    fun proactive() {
        viewModelScope.launch {
            agent.initiate(com.rgs.companion.companion.ProactiveReason.IDLE)?.let { reply ->
                _state.update {
                    it.copy(
                        emotion = reply.emotion,
                        messages = it.messages + UiMessage(
                            role = "assistant",
                            text = reply.text,
                            emotion = reply.emotion.tag,
                            proactive = true,
                        ),
                    )
                }
                speech.speakWithLipSync(reply.text)
            }
        }
    }

    override fun onCleared() {
        speech.shutdown()
        super.onCleared()
    }

    private companion object {
        const val TICK_MS = 50L
    }
}

data class ChatUiState(
    val messages: List<UiMessage> = emptyList(),
    val thinking: Boolean = false,
    val listening: Boolean = false,
    val emotion: Emotion = Emotion.NEUTRAL,
    val mouthLevel: Float = 0f,
    val greeting: String = "",
)

data class UiMessage(
    val role: String,               // "user" | "assistant" | "error"
    val text: String,
    val emotion: String? = null,
    val proactive: Boolean = false,
)
