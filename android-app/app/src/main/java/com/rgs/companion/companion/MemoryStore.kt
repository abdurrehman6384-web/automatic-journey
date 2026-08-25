package com.rgs.companion.companion

import android.content.Context
import androidx.room.Dao
import androidx.room.Database
import androidx.room.Entity
import androidx.room.Insert
import androidx.room.PrimaryKey
import androidx.room.Query
import androidx.room.Room
import androidx.room.RoomDatabase
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.withContext
import java.time.Instant

/**
 * Long-term memory: the thing that makes her feel like she remembers you.
 *
 * Three tiers, because "memory" is really three different jobs:
 *
 * 1. **Facts** ([MemoryFact]) — durable, few, injected into every system prompt.
 *    "Has an exam Thursday." "Allergic to peanuts." "Mum is called Farida."
 * 2. **Transcript** ([ChatTurn]) — the recent conversation, sliding window.
 * 3. **Recency-weighted recall** — the most recent N turns plus any facts that
 *    lexically match the current message.
 *
 * ## Why not embeddings
 * A vector store is the right answer at scale, but it drags in a model download
 * and an inference dependency for a companion that will hold a few hundred facts.
 * Keyword overlap plus recency covers the realistic case, runs offline, and can
 * be swapped for embeddings later behind [recall] without touching callers.
 */
@Entity(tableName = "facts")
data class MemoryFact(
    @PrimaryKey(autoGenerate = true) val id: Long = 0,
    val content: String,
    /** "user" | "relationship" | "world" | "preference" */
    val kind: String = "user",
    /** Higher = more central to who the user is. Facts are injected by rank. */
    val importance: Int = 5,
    val createdAt: Long = Instant.now().epochSecond,
    /** Bumped every time the fact is used, so stale facts sink. */
    val lastUsedAt: Long = Instant.now().epochSecond,
    val timesUsed: Int = 0,
)

@Entity(tableName = "turns")
data class ChatTurn(
    @PrimaryKey(autoGenerate = true) val id: Long = 0,
    val role: String,               // "user" | "assistant"
    val text: String,
    val emotion: String? = null,
    val createdAt: Long = Instant.now().epochSecond,
)

@Dao
interface MemoryDao {
    @Query("SELECT * FROM facts ORDER BY importance DESC, lastUsedAt DESC LIMIT :limit")
    suspend fun topFacts(limit: Int): List<MemoryFact>

    @Query("SELECT * FROM facts ORDER BY importance DESC, lastUsedAt DESC")
    suspend fun allFacts(): List<MemoryFact>

    @Insert
    suspend fun insertFact(fact: MemoryFact): Long

    @Query("DELETE FROM facts WHERE id = :id")
    suspend fun deleteFact(id: Long)

    @Query("UPDATE facts SET timesUsed = timesUsed + 1, lastUsedAt = :now WHERE id = :id")
    suspend fun touchFact(id: Long, now: Long)

    @Insert
    suspend fun insertTurn(turn: ChatTurn)

    @Query("SELECT * FROM turns ORDER BY id DESC LIMIT :limit")
    suspend fun recentTurns(limit: Int): List<ChatTurn>

    @Query("DELETE FROM turns WHERE id NOT IN (SELECT id FROM turns ORDER BY id DESC LIMIT :keep)")
    suspend fun pruneTurns(keep: Int)
}

@Database(entities = [MemoryFact::class, ChatTurn::class], version = 1, exportSchema = false)
abstract class MemoryDatabase : RoomDatabase() {
    abstract fun dao(): MemoryDao

    companion object {
        @Volatile
        private var instance: MemoryDatabase? = null

        fun get(context: Context): MemoryDatabase =
            instance ?: synchronized(this) {
                instance ?: Room.databaseBuilder(
                    context.applicationContext,
                    MemoryDatabase::class.java,
                    "companion_memory.db",
                ).build().also { instance = it }
            }
    }
}

class MemoryStore(context: Context) {

    private val dao = MemoryDatabase.get(context).dao()

    // ------------------------------------------------------------------
    // transcript
    // ------------------------------------------------------------------
    suspend fun addTurn(role: String, text: String, emotion: String? = null) {
        withContext(Dispatchers.IO) {
            dao.insertTurn(ChatTurn(role = role, text = text, emotion = emotion))
            dao.pruneTurns(keep = MAX_TURNS_KEPT)
        }
    }

    suspend fun recentTurns(limit: Int = 12): List<ChatTurn> =
        withContext(Dispatchers.IO) { dao.recentTurns(limit).reversed() }

    // ------------------------------------------------------------------
    // facts
    // ------------------------------------------------------------------
    suspend fun remember(content: String, kind: String = "user", importance: Int = 5) {
        val cleaned = content.trim()
        if (cleaned.isEmpty()) return
        withContext(Dispatchers.IO) {
            // De-dup case-insensitively: "likes coffee" and "Likes coffee" are one fact.
            val exists = dao.allFacts().any { it.content.equals(cleaned, ignoreCase = true) }
            if (!exists) dao.insertFact(MemoryFact(content = cleaned, kind = kind,
                importance = importance))
        }
    }

    suspend fun forget(id: Long) = withContext(Dispatchers.IO) { dao.deleteFact(id) }

    suspend fun allFacts(): List<MemoryFact> = withContext(Dispatchers.IO) { dao.allFacts() }

    /**
     * Everything worth injecting into the system prompt right now: the top facts
     * plus any fact that lexically matches what the user just said.
     */
    suspend fun recall(latestUserText: String, maxFacts: Int = 14): List<MemoryFact> =
        withContext(Dispatchers.IO) {
            val all = dao.allFacts()
            val queryTokens = latestUserText.lowercase()
                .split(Regex("[^\\p{L}\\p{N}']+"))
                .filter { it.length > 3 }
                .toSet()

            val matched = all.filter { fact ->
                val f = fact.content.lowercase()
                queryTokens.any { it in f }
            }
            val top = all.sortedWith(
                compareByDescending<MemoryFact> { it.importance }
                    .thenByDescending { it.lastUsedAt },
            )

            (matched + top).distinctBy { it.id }.take(maxFacts).also { picked ->
                val now = Instant.now().epochSecond
                picked.forEach { dao.touchFact(it.id, now) }
            }
        }

    /**
     * Render recalled memory for the system prompt.
     *
     * Phrased as instructions rather than a data dump -- models follow "bring this
     * up naturally" better than they follow a JSON blob.
     */
    fun formatForPrompt(facts: List<MemoryFact>): String {
        if (facts.isEmpty()) return ""
        return buildString {
            appendLine("What you remember about the user. Weave these in naturally " +
                "when relevant -- do not list them, do not announce that you remember.")
            facts.forEach { appendLine("- (${it.kind}) ${it.content}") }
        }
    }

    /** Recent transcript as chat messages for the API call. */
    suspend fun transcriptMessages(limit: Int = 12): List<Pair<String, String>> =
        recentTurns(limit).map { it.role to it.text }

    private companion object {
        const val MAX_TURNS_KEPT = 400
    }
}
