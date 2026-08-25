package com.rgs.companion

import android.Manifest
import android.content.Intent
import android.content.pm.PackageManager
import android.os.Build
import android.os.Bundle
import android.provider.Settings
import androidx.activity.ComponentActivity
import androidx.activity.compose.setContent
import androidx.activity.result.contract.ActivityResultContracts
import androidx.activity.viewModels
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.Surface
import androidx.compose.material3.darkColorScheme
import androidx.compose.ui.Modifier
import androidx.core.content.ContextCompat
import com.rgs.companion.chat.ChatScreen
import com.rgs.companion.chat.ChatViewModel
import com.rgs.companion.overlay.FloatingCompanionService

/**
 * Hosts the chat screen and owns the permission flow.
 *
 * Three permissions, three different mechanisms -- this is the part people get
 * wrong, so it is spelled out:
 *
 * | Permission | Mechanism |
 * |---|---|
 * | `RECORD_AUDIO` | runtime dialog (`rememberLauncherForActivityResult`) |
 * | `POST_NOTIFICATIONS` | runtime dialog, API 33+ only |
 * | `SYSTEM_ALERT_WINDOW` | **not** a dialog -- a Settings screen |
 * | Accessibility | **not** a dialog -- a Settings screen, per service |
 */
class MainActivity : ComponentActivity() {

    private val viewModel: ChatViewModel by viewModels()

    private val micPermission =
        registerForActivityResult(ActivityResultContracts.RequestPermission()) { granted ->
            if (!granted) {
                // Degrade: typed chat still works, so we do not block the app.
                android.util.Log.i(TAG, "mic denied; voice input disabled")
            }
        }

    private val notificationPermission =
        registerForActivityResult(ActivityResultContracts.RequestPermission()) { }

    private val overlayPermission =
        registerForActivityResult(ActivityResultContracts.StartActivityForResult()) {
            if (FloatingCompanionService.canDrawOverlays(this)) {
                FloatingCompanionService.start(this)
            }
        }

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)

        requestPermissionsIfNeeded()

        setContent {
            MaterialTheme(colorScheme = darkColorScheme()) {
                Surface(modifier = Modifier, color = MaterialTheme.colorScheme.background) {
                    ChatScreen(viewModel = viewModel)
                }
            }
        }
    }

    private fun requestPermissionsIfNeeded() {
        if (ContextCompat.checkSelfPermission(this, Manifest.permission.RECORD_AUDIO)
            != PackageManager.PERMISSION_GRANTED
        ) {
            micPermission.launch(Manifest.permission.RECORD_AUDIO)
        }

        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.TIRAMISU &&
            ContextCompat.checkSelfPermission(this, Manifest.permission.POST_NOTIFICATIONS)
            != PackageManager.PERMISSION_GRANTED
        ) {
            notificationPermission.launch(Manifest.permission.POST_NOTIFICATIONS)
        }
    }

    /**
     * Call from a "Floating companion" switch in your settings screen.
     * Overlay permission cannot be requested with a dialog, so we send the user
     * to the system screen and start the service when they come back.
     */
    fun enableFloatingCompanion() {
        if (FloatingCompanionService.canDrawOverlays(this)) {
            FloatingCompanionService.start(this)
        } else {
            overlayPermission.launch(FloatingCompanionService.overlayPermissionIntent(this))
        }
    }

    /** Send the user to Settings > Accessibility to enable phone control. */
    fun openAccessibilitySettings() {
        startActivity(Intent(Settings.ACTION_ACCESSIBILITY_SETTINGS))
    }

    private companion object {
        const val TAG = "MainActivity"
    }
}
