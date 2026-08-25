plugins {
    alias(libs.plugins.android.application)
    alias(libs.plugins.kotlin.android)
    alias(libs.plugins.kotlin.compose)
    alias(libs.plugins.ksp)
    id("org.jetbrains.kotlin.plugin.serialization") version "2.0.20"
}

android {
    namespace = "com.rgs.companion"
    compileSdk = 36

    defaultConfig {
        applicationId = "com.rgs.companion"
        minSdk = 24   // dispatchGesture needs 24; Cubism itself needs 21
        targetSdk = 36
        versionCode = 1
        versionName = "0.1.0"

        // Live2D Cubism Core ships native libs for EXACTLY these three ABIs.
        // Verified against CubismJavaSamples' gradle.properties
        // (PROP_APP_ABI=arm64-v8a:x86:x86_64). Listing an ABI the core does not
        // ship (e.g. armeabi-v7a) makes the build fail at packaging.
        ndk {
            abiFilters += listOf("arm64-v8a", "x86", "x86_64")
        }

        // LLM credentials. Never commit real keys -- override per machine:
        //   ./gradlew assembleDebug -PllmApiKey=sk-...
        // or put them in ~/.gradle/gradle.properties.
        val llmKey = (project.findProperty("llmApiKey") as String?)
            ?: System.getenv("LLM_API_KEY") ?: ""
        val llmModel = (project.findProperty("llmModel") as String?)
            ?: System.getenv("LLM_MODEL") ?: "llama-3.1-70b-versatile"

        buildConfigField("String", "LLM_API_KEY", "\"$llmKey\"")
        buildConfigField("String", "LLM_MODEL", "\"$llmModel\"")
    }

    // ── Live2D ────────────────────────────────────────────────────────
    // Two files you must supply yourself (neither is redistributable here):
    //   1. Live2DCubismCore.aar   -> app/libs/Live2DCubismCore.aar
    //   2. CubismJavaFramework    -> included as the :Framework:framework module
    // Both come from https://www.live2d.com/en/sdk/download/java/
    // Full walkthrough: README.md section 3.
    buildFeatures {
        compose = true
        buildConfig = true
    }

    compileOptions {
        sourceCompatibility = JavaVersion.VERSION_17
        targetCompatibility = JavaVersion.VERSION_17
    }

    kotlinOptions {
        jvmTarget = "17"
    }

    buildTypes {
        release {
            isMinifyEnabled = true
            proguardFiles(
                getDefaultProguardFile("proguard-android-optimize.txt"),
                "proguard-rules.pro",
            )
        }
    }

    packaging {
        resources.excludes += "/META-INF/{AL2.0,LGPL2.1}"
    }
}

dependencies {
    // ── Live2D ─────────────────────────────────────────────────────────
    // The Framework as a Gradle module (how the official sample does it).
    implementation(project(":Framework:framework"))
    // The native core, dropped into app/libs/.
    implementation(files("libs/Live2DCubismCore.aar"))

    // ── AndroidX / Compose ─────────────────────────────────────────────
    implementation(libs.androidx.core.ktx)
    implementation(libs.androidx.lifecycle.runtime.ktx)
    implementation(libs.androidx.lifecycle.viewmodel.compose)
    implementation(libs.androidx.lifecycle.runtime.compose)
    implementation(libs.androidx.activity.compose)

    implementation(platform(libs.androidx.compose.bom))
    implementation(libs.androidx.compose.ui)
    implementation(libs.androidx.compose.ui.graphics)
    implementation(libs.androidx.compose.ui.tooling.preview)
    implementation(libs.androidx.compose.material3)
    implementation(libs.androidx.compose.material.icons)
    debugImplementation(libs.androidx.compose.ui.tooling)

    // ── persistence (long-term memory) ─────────────────────────────────
    implementation(libs.androidx.room.runtime)
    implementation(libs.androidx.room.ktx)
    ksp(libs.androidx.room.compiler)

    // ── networking + JSON for the LLM call ─────────────────────────────
    implementation(libs.okhttp)
    implementation(libs.kotlinx.serialization.json)
    implementation(libs.kotlinx.coroutines.android)
}
