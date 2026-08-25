package com.rgs.companion.chat

import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.PaddingValues
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.height
import androidx.compose.foundation.layout.imePadding
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.layout.size
import androidx.compose.foundation.layout.widthIn
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.foundation.lazy.items
import androidx.compose.foundation.lazy.rememberLazyListState
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.filled.Mic
import androidx.compose.material.icons.filled.Send
import androidx.compose.material3.CircularProgressIndicator
import androidx.compose.material3.Icon
import androidx.compose.material3.IconButton
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.OutlinedTextField
import androidx.compose.material3.Surface
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.runtime.LaunchedEffect
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.remember
import androidx.compose.runtime.setValue
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.text.font.FontStyle
import androidx.compose.ui.unit.dp
import androidx.compose.ui.viewinterop.AndroidView
import androidx.lifecycle.compose.collectAsStateWithLifecycle
import com.rgs.companion.live2d.Live2DView

/**
 * The chat screen: Live2D avatar on top, transcript in the middle, input at the
 * bottom.
 *
 * The avatar is a [Live2DView] embedded with [AndroidView]. Two details matter:
 *
 * - The `update` block must be **cheap and idempotent** -- it re-runs on every
 *   recomposition. It only pushes the current expression.
 * - Lip-sync is *not* driven through Compose state. Updating a `Float` at 20fps
 *   through the state system would recompose the whole screen every frame. The
 *   renderer reads it straight off the view instead.
 */
@Composable
fun ChatScreen(
    viewModel: ChatViewModel,
    modifier: Modifier = Modifier,
    modelAssetPath: String = "models/hiyori/hiyori.model3.json",
) {
    val state by viewModel.state.collectAsStateWithLifecycle()
    var draft by remember { mutableStateOf("") }
    val listState = rememberLazyListState()

    // Keep the newest message visible as the conversation grows.
    LaunchedEffect(state.messages.size, state.thinking) {
        val target = state.messages.size + (if (state.thinking) 1 else 0)
        if (target > 0) listState.animateScrollToItem(target - 1)
    }

    Column(
        modifier = modifier
            .fillMaxSize()
            .imePadding(),
    ) {
        // ── avatar ─────────────────────────────────────────────────────
        Box(
            modifier = Modifier
                .fillMaxWidth()
                .height(AVATAR_HEIGHT_DP.dp),
            contentAlignment = Alignment.Center,
        ) {
            AndroidView(
                modifier = Modifier.fillMaxSize(),
                factory = { ctx ->
                    Live2DView(ctx).apply {
                        onTap = { _, _ -> viewModel.pokeAvatar() }
                        loadModel(modelAssetPath)
                    }
                },
                update = { view ->
                    view.setExpression(state.emotion.expressionName)
                    view.setMouthOpen(state.mouthLevel)
                },
            )
        }

        // ── transcript ─────────────────────────────────────────────────
        LazyColumn(
            state = listState,
            modifier = Modifier
                .weight(1f)
                .fillMaxWidth()
                .padding(horizontal = 12.dp),
            contentPadding = PaddingValues(vertical = 8.dp),
            verticalArrangement = Arrangement.spacedBy(8.dp),
        ) {
            if (state.messages.isEmpty() && state.greeting.isNotEmpty()) {
                item {
                    MessageBubble(
                        text = state.greeting,
                        fromUser = false,
                        italic = true,
                    )
                }
            }
            items(state.messages, key = { it.hashCode() }) { message ->
                MessageBubble(
                    text = message.text,
                    fromUser = message.role == "user",
                    isError = message.role == "error",
                    proactive = message.proactive,
                )
            }
            if (state.thinking) {
                item { ThinkingBubble() }
            }
        }

        // ── input ──────────────────────────────────────────────────────
        Row(
            modifier = Modifier
                .fillMaxWidth()
                .padding(horizontal = 12.dp, vertical = 8.dp),
            verticalAlignment = Alignment.CenterVertically,
        ) {
            OutlinedTextField(
                value = draft,
                onValueChange = { draft = it },
                modifier = Modifier.weight(1f),
                placeholder = { Text("Say something...") },
                maxLines = 3,
                shape = RoundedCornerShape(24.dp),
            )

            IconButton(onClick = { viewModel.toggleMic() }) {
                Icon(
                    Icons.Filled.Mic,
                    contentDescription = "Voice input",
                    tint = if (state.listening) MaterialTheme.colorScheme.primary
                    else MaterialTheme.colorScheme.onSurfaceVariant,
                )
            }

            IconButton(
                onClick = {
                    if (draft.isNotBlank()) {
                        viewModel.send(draft)
                        draft = ""
                    }
                },
            ) {
                Icon(Icons.Filled.Send, contentDescription = "Send")
            }
        }
    }
}

@Composable
private fun MessageBubble(
    text: String,
    fromUser: Boolean,
    isError: Boolean = false,
    proactive: Boolean = false,
    italic: Boolean = false,
) {
    Row(
        modifier = Modifier.fillMaxWidth(),
        horizontalArrangement = if (fromUser) Arrangement.End else Arrangement.Start,
    ) {
        Surface(
            modifier = Modifier.widthIn(max = 300.dp),
            shape = RoundedCornerShape(
                topStart = 18.dp, topEnd = 18.dp,
                bottomStart = if (fromUser) 18.dp else 4.dp,
                bottomEnd = if (fromUser) 4.dp else 18.dp,
            ),
            color = when {
                isError -> MaterialTheme.colorScheme.errorContainer
                fromUser -> MaterialTheme.colorScheme.primaryContainer
                else -> MaterialTheme.colorScheme.surfaceVariant
            },
        ) {
            Column(modifier = Modifier.padding(horizontal = 14.dp, vertical = 10.dp)) {
                if (proactive) {
                    Text(
                        "she started this",
                        style = MaterialTheme.typography.labelSmall,
                        fontStyle = FontStyle.Italic,
                        color = MaterialTheme.colorScheme.onSurfaceVariant,
                    )
                }
                Text(
                    text = text,
                    style = MaterialTheme.typography.bodyLarge,
                    fontStyle = if (italic) FontStyle.Italic else FontStyle.Normal,
                )
            }
        }
    }
}

@Composable
private fun ThinkingBubble() {
    Row(
        modifier = Modifier.fillMaxWidth(),
        horizontalArrangement = Arrangement.Start,
    ) {
        Surface(
            shape = RoundedCornerShape(18.dp),
            color = MaterialTheme.colorScheme.surfaceVariant,
        ) {
            Row(
                modifier = Modifier.padding(horizontal = 16.dp, vertical = 12.dp),
                verticalAlignment = Alignment.CenterVertically,
            ) {
                CircularProgressIndicator(modifier = Modifier.size(16.dp), strokeWidth = 2.dp)
                Text(
                    "  typing...",
                    style = MaterialTheme.typography.bodyMedium,
                    color = MaterialTheme.colorScheme.onSurfaceVariant,
                )
            }
        }
    }
}

private const val AVATAR_HEIGHT_DP = 320
