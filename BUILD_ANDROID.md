# Android APK kaise banao

Do Android projects hain is repo mein. **Pehle samajh lo kaunsa banana hai** — ek
abhi build nahi ho sakta.

| Project | Kya hai | Build ho sakta hai? |
|---|---|---|
| **`android-agent/`** | OpenDroid (asli on-device AI agent) + **Toni** pet | ✅ **Haan — yahi banao** |
| `android-app/` | Live2D Cubism companion | ⚠️ Nahi, jab tak `Live2DCubismCore.aar` na ho |

`android-app` ke liye `app/libs/Live2DCubismCore.aar` chahiye, jo **is repo mein
nahi hai** — wo Live2D ki licence-gated download hai
(<https://www.live2d.com/en/sdk/download/java/>). Bina uske build fail hoga. Isliye
neeche saare steps `android-agent` ke liye hain.

---

## Tarika 1: GitHub Actions — kuch install nahi karna (recommended)

GitHub ke `ubuntu-latest` runners mein **Android SDK pehle se installed hota
hai**. Isi liye OpenDroid ke apne CI mein bhi koi `setup-android` step nahi hai.

Workflow file is repo mein maujood hai, lekin **`.github/workflows/` mein copy
karni padegi** — Arena ka GitHub token ek bot integration hai aur uske paas
`workflows` permission nahi hai, isliye main wo file khud push nahi kar saka:

```
remote: refusing to allow a GitHub App to create or update workflow
        `.github/workflows/build-android-apk.yml` without `workflows` permission
```

Ek command mein ho jaata hai:

```bash
git clone https://github.com/abdurrehman6384-web/automatic-journey.git
cd automatic-journey
mkdir -p .github/workflows
cp android-agent/pet/build-android-apk.yml .github/workflows/
git add .github && git commit -m "Add APK build workflow" && git push
```

Phir:

```
GitHub → is repo pe jao → Actions tab
  → "Build Android APK (OpenDroid + Toni)"
  → Run workflow
```

Workflow khud ye sab karta hai:
1. OpenDroid clone (ref aap choose kar sakte ho, default `main`)
2. Toni ke 3 Kotlin files copy
3. Wiring patch apply (anchor-verified, idempotent)
4. `./gradlew :app:assembleDebug`
5. APK artifact upload

Run khatam hone pe **Artifacts** section se `toni-debug-apk` download karo:

```bash
adb install -r app-debug.apk
```

> Workflow sirf usi branch pe chalega jis branch pe aapne push kiya. `main` pe
> chahiye to `main` pe push karo (ya PR #1 merge kar do).

### Signed release bhi chahiye?

`Run workflow` pe **build_release** tick karo, aur repo mein 4 secrets daalo
(Settings → Secrets and variables → Actions):

| Secret | Kaise banao |
|---|---|
| `RELEASE_KEYSTORE_BASE64` | `base64 -w0 < opendroid-release.keystore` |
| `RELEASE_STORE_PASSWORD` | keystore ka password |
| `RELEASE_KEY_ALIAS` | `opendroid` |
| `RELEASE_KEY_PASSWORD` | key ka password |

Keystore banane ke liye:

```bash
keytool -genkeypair -v -keystore opendroid-release.keystore -alias opendroid \
  -keyalg RSA -keysize 2048 -validity 10000
```

OpenDroid **debug key se release sign karne se mana kar deta hai** — ye jaan-boojh
ke hai, taake galti se public debug key se signed app release na ho.

---

## Tarika 2: Apni machine pe (Android Studio)

### Step 1 — JDK 21 (exactly 21, 17 ya 25 fail hoga)

```bash
sudo apt install openjdk-21-jdk
java -version        # 21.x aana chahiye
```

OpenDroid `jvmToolchain(21)` use karta hai aur Gradle daemon bhi JDK 21 pe pinned
hai. Unke `docs/development_guide.md` mein likha hai *"JDK: Version 21 exactly"*.

### Step 2 — Android SDK

Sabse aasan: **Android Studio** install karo, phir SDK Manager se:
- Android SDK Platform **36**
- Android SDK Build-Tools **36**

```bash
export ANDROID_HOME=$HOME/Android/Sdk      # ya jahan install hua
```

### Step 3 — OpenDroid + Toni

```bash
git clone --depth 1 https://github.com/yashab-cyber/opendroid.git
cd opendroid

# Toni daalo (is repo se)
cp -r <yeh-repo>/android-agent/pet ./pet

# wiring patch
python3 pet/apply_patch.py --check     # pehle anchors verify
python3 pet/apply_patch.py .           # phir apply
```

### Step 4 — Build

```bash
# SDK ka path batana zaroori hai
echo "sdk.dir=$ANDROID_HOME" > local.properties

# Debug APK
./gradlew :app:assembleDebug --stacktrace
```

Ya is repo ka script, jo upar ke saare steps khud karta hai aur pehli galti pe
specific message ke saath ruk jaata hai:

```bash
<yeh-repo>/android-agent/pet/build-apk.sh
```

### Output

```
opendroid/app/build/outputs/apk/debug/app-debug.apk
```

### Step 5 — Phone pe install

```bash
adb install -r app/build/outputs/apk/debug/app-debug.apk
```

Phir phone pe:
**Settings → Accessibility → OpenDroid → enable**, aur OpenDroid ke andar
floating-button setting on karo. Toni right edge pe, ~55% neeche aa jaayegi.

---

## Toolchain versions (exact — guess nahi, unke build files se)

| Component | Version | Kahan se pata chala |
|---|---|---|
| JDK | **21 exactly** | `jvmToolchain(21)` + `gradle-daemon-jvm.properties` |
| Gradle | 9.7.0 | `gradle/wrapper/gradle-wrapper.properties` |
| Android Gradle Plugin | 9.3.1 | root `build.gradle` |
| Kotlin | 2.4.0 | root `build.gradle` |
| Hilt / Room / KSP | 2.60.1 / 2.8.4 / 2.3.10 | root `build.gradle` |
| compileSdk / targetSdk | 36 | `app/build.gradle` |
| minSdk | **26** | `app/build.gradle` |
| applicationId | `com.opendroid.aiagent` | `app/build.gradle` |

Build commands OpenDroid ke apne `.github/workflows/android-ci.yml` se liye hain,
khud se nahi banaye.

---

## Common errors

| Error | Wajah / hal |
|---|---|
| `Unsupported class file major version` | JDK 21 nahi hai. `java -version` check karo |
| `SDK location not found` | `local.properties` mein `sdk.dir=` daalo, ya `ANDROID_HOME` set karo |
| `Failed to find target android-36` | SDK Manager se Platform 36 install karo |
| `assembleRelease` signing pe fail | Keystore + 3 credentials chahiye (upar dekho), ya `-PallowUnsignedRelease` sirf compile-check ke liye |
| `INSTALL_FAILED_UPDATE_INCOMPATIBLE` | Purana differently-signed build installed hai: `adb uninstall com.opendroid.aiagent` phir dobara install |
| Toni nahi dikhti | Accessibility service enable nahi, ya floating-button setting off |
| Patch fail: `anchor not found` | OpenDroid ka code badal gaya. `android-agent/pet/APPLY.md` dekh ke haath se karo |

---

## Ek zaroori baat

**Maine yahan APK nahi banaya — bana nahi saka.** Is environment mein JDK,
Android SDK, Gradle aur kotlinc koi nahi hai, aur `services.gradle.org`,
`dl.google.com` aur Maven Central teeno unreachable hain (har turn mein dobara
test kiya hai). Isliye:

- ✅ Jo verify hua: patcher ka poora cycle (check → apply → re-apply → revert,
  revert pe file **byte-identical**), workflow YAML valid, `build-apk.sh` ka
  syntax aur JDK version parser, aur Python side ke **110 tests**.
- ❌ Jo verify nahi hua: **Kotlin compile**. Compiler yahan hai hi nahi.

Pehli build pe mamooli cheezein aa sakti hain — ek missing import, koi version
bump. Wo normal hai. Live2D wale code mein maine har framework call asli
`CubismJavaFramework` source se match kiya tha, jisne paanch API errors pehle hi
pakad liye — lekin compile ke bina guarantee nahi di ja sakti.
