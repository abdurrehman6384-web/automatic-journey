pluginManagement {
    repositories {
        google {
            content {
                includeGroupByRegex("com\\.android.*")
                includeGroupByRegex("com\\.google.*")
                includeGroupByRegex("androidx.*")
            }
        }
        mavenCentral()
        gradlePluginPortal()
    }
}

dependencyResolutionManagement {
    repositoriesMode.set(RepositoriesMode.FAIL_ON_PROJECT_REPOS)
    repositories {
        google()
        mavenCentral()
    }
}

rootProject.name = "RGS Companion"
include(":app")

// ── Live2D Cubism Framework ──────────────────────────────────────────────
// Clone it next to this project, then this include resolves:
//   git clone https://github.com/Live2D/CubismJavaFramework.git CubismJavaFramework
// The official samples include it as a git submodule at ./Framework; either
// layout works as long as the path below matches where you put it.
include(":Framework:framework")
project(":Framework:framework").projectDir = file("../CubismJavaFramework/framework")
