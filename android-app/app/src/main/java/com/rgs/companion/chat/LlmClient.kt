package com.rgs.companion.chat

import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.withContext
import kotlinx.serialization.Serializable
import kotlinx.serialization.json.Json
import okhttp3.MediaType.Companion.toMediaType
import okhttp3.OkHttpClient
import okhttp3.Request
import okhttp3.RequestBody.Companion.toRequestBody
import java.io.IOException
import java.util.concurrent.TimeUnit

/**
 * Minimal OpenAI-compatible chat client.
 *
 * One class, one call, no SDK. Works against OpenAI, Groq, OpenRouter, Together,
 * DeepSeek, Ollama and anything else that speaks `/v1/chat/completions` -- you
 * change [baseUrl] and [model], nothing else.
 *
 * Streaming is deliberately omitted: the companion speaks the whole reply at once
 * through TTS, so token streaming would only add complexity. Add an SSE reader
 * here if you later want incremental text.
 */
class LlmClient(
    private val baseUrl: String,
    private val apiKey: String,
    private val model: String,
    private val temperature: Float = 0.85f,
    private val maxTokens: Int = 350,
) {
    private val json = Json { ignoreUnknownKeys = true; encodeDefaults = true }

    private val http = OkHttpClient.Builder()
        .connectTimeout(20, TimeUnit.SECONDS)
        .readTimeout(60, TimeUnit.SECONDS)
        .build()

    /**
     * @param system system prompt
     * @param history prior turns, oldest first, as (role, content)
     * @param user the new user message
     * @throws IOException on network failure, [LlmException] on an API error
     */
    suspend fun complete(
        system: String,
        history: List<Pair<String, String>>,
        user: String,
    ): String = withContext(Dispatchers.IO) {
        val messages = buildList {
            add(ChatMessage("system", system))
            history.forEach { (role, content) -> add(ChatMessage(role, content)) }
            add(ChatMessage("user", user))
        }

        val body = json.encodeToString(
            ChatRequest.serializer(),
            ChatRequest(model = model, messages = messages,
                temperature = temperature, max_tokens = maxTokens),
        )

        val request = Request.Builder()
            .url("$baseUrl/chat/completions")
            .header("Authorization", "Bearer $apiKey")
            .header("Content-Type", "application/json")
            .post(body.toRequestBody(JSON_MEDIA))
            .build()

        http.newCall(request).execute().use { response ->
            val text = response.body?.string().orEmpty()
            if (!response.isSuccessful) {
                throw LlmException(response.code, text.take(500))
            }
            val parsed = json.decodeFromString(ChatResponse.serializer(), text)
            parsed.choices.firstOrNull()?.message?.content?.trim()
                ?: throw LlmException(response.code, "empty completion: ${text.take(200)}")
        }
    }

    private companion object {
        val JSON_MEDIA = "application/json; charset=utf-8".toMediaType()
    }
}

class LlmException(val code: Int, message: String) :
    IOException("LLM request failed (HTTP $code): $message")

// ── wire types ────────────────────────────────────────────────────────────
@Serializable
private data class ChatMessage(val role: String, val content: String)

@Serializable
private data class ChatRequest(
    val model: String,
    val messages: List<ChatMessage>,
    val temperature: Float,
    val max_tokens: Int,
)

@Serializable
private data class ChatResponse(val choices: List<Choice> = emptyList())

@Serializable
private data class Choice(val message: ChatMessage? = null)

/**
 * Provider presets. Pick one, or construct [LlmClient] directly for a custom
 * endpoint.
 */
enum class LlmProvider(val baseUrl: String, val defaultModel: String) {
    OPENAI("https://api.openai.com/v1", "gpt-4o-mini"),
    GROQ("https://api.groq.com/openai/v1", "llama-3.1-70b-versatile"),
    OPENROUTER("https://openrouter.ai/api/v1", "meta-llama/llama-3.1-70b-instruct"),
    DEEPSEEK("https://api.deepseek.com/v1", "deepseek-chat"),
    TOGETHER("https://api.together.xyz/v1", "meta-llama/Llama-3.3-70B-Instruct-Turbo"),
    OLLAMA("http://10.0.2.2:11434/v1", "llama3.2"),   // 10.0.2.2 = host from an emulator
    ;

    fun client(apiKey: String, model: String = defaultModel) =
        LlmClient(baseUrl, apiKey, model)
}
