#!/usr/bin/env bash
# Publishes this project to a NEW GitHub repository under YOUR account.
#
#   ./publish-new-repo.sh                      -> private repo, name below
#   ./publish-new-repo.sh my-cool-name         -> private, that name
#   ./publish-new-repo.sh my-cool-name --public
#
# I could not run this for you: the Arena GitHub token is a bot integration
# without the createRepository scope (`gh repo create` returns
# "Resource not accessible by integration"). Your own `gh` login has it.
#
# What it does:
#   1. verifies you are logged in to gh
#   2. creates the new repo under your account
#   3. pushes ONLY the three project folders as a clean history --
#      the original project.zip / RGS_HUD_Graphics.zip are excluded, because
#      32 MB of archives is not something you want in a fresh repo
#   4. prints the URL
set -euo pipefail

NAME="${1:-android-ai-agent-stack}"
VISIBILITY="--private"
[ "${2:-}" = "--public" ] && VISIBILITY="--public"

die() { printf '\n\033[31merror:\033[0m %s\n' "$1" >&2; exit 1; }

command -v gh >/dev/null || die "gh not installed. See https://cli.github.com"
gh auth status >/dev/null 2>&1 || die "not logged in. Run: gh auth login"

HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
STAGE="$(mktemp -d)"
trap 'rm -rf "$STAGE"' EXIT

say() { printf '\n\033[1m== %s\033[0m\n' "$1"; }

# ---------------------------------------------------------------- 1. stage
say "Staging a clean tree"
for d in android-control android-app android-agent; do
  [ -d "$HERE/$d" ] || die "missing $HERE/$d"
  cp -R "$HERE/$d" "$STAGE/$d"
  echo "  + $d"
done

# Never publish virtualenvs, clones, build output or keystores.
find "$STAGE" \( -name '.venv' -o -name 'build' -o -name '.gradle' \
                -o -name '*.keystore' -o -name '*.jks' \
                -o -name '.pytest_cache' -o -name '__pycache__' \) \
     -prune -exec rm -rf {} + 2>/dev/null || true
rm -rf "$STAGE/android-agent/opendroid"          # upstream clone, re-fetchable
echo "  size: $(du -sh "$STAGE" | cut -f1)"

cat > "$STAGE/README.md" <<'EOF'
# Android AI agent stack

Three independent pieces. None of them modify each other.

| Folder | What | Language | Build |
|---|---|---|---|
| `android-control/` | Non-root device control over ADB: screenshots, UI tree, tap/swipe/type, apps, shell, multi-device. Python API + CLI + 24-tool MCP server. | Python | `pip install -r requirements.txt` |
| `android-app/` | Live2D Cubism AI companion: GLSurfaceView renderer, lip-sync, persona, memory, voice, floating overlay. | Kotlin | Android Studio |
| `android-agent/` | OpenDroid (base Android agent) + **Toni**, a Canvas-drawn pet wired to its real `AgentState`. Includes CI that builds the APK. | Kotlin | see its README |

## Quickest win

```bash
cd android-control
python3 -m venv .venv && .venv/bin/pip install -r requirements.txt
.venv/bin/python -m pytest tests -q          # 110 tests, no phone needed
.venv/bin/python examples/full_control_demo.py --dry-run
```

## Getting an APK

You do not need a local JDK or Android SDK. See
[`android-agent/README.md`](android-agent/README.md#3-how-to-build-the-apk) --
`android-agent/pet/build-apk.yml` builds it on GitHub's runners.

## Honest status

`android-control` is tested (110 passing tests, live MCP handshake verified).
The Kotlin in `android-app` and `android-agent` **has not been compiled** -- the
environment it was written in had no JDK, Android SDK, Gradle or kotlinc, and
`dl.google.com` / `services.gradle.org` / Maven Central were unreachable. Each
README states exactly what is verified and what is not.
EOF

# ---------------------------------------------------------------- 2. create
say "Creating the repository"
gh repo create "$NAME" $VISIBILITY --description \
  "Non-root Android device control (androidctl + MCP), a Live2D AI companion app, and OpenDroid + Toni pet" \
  || die "gh repo create failed"

# ---------------------------------------------------------------- 3. push
say "Pushing"
cd "$STAGE"
git init -q -b main
git add -A
git -c user.name="$(gh api user -q .login)" \
    -c user.email="$(gh api user -q .id)+$(gh api user -q .login)@users.noreply.github.com" \
    commit -q -m "Initial commit: android-control, android-app, android-agent"
git remote add origin "https://github.com/$(gh api user -q .login)/$NAME.git"
git push -q -u origin main

say "Done"
echo "  https://github.com/$(gh api user -q .login)/$NAME"
echo
echo "To build the APK, go to that repo's Actions tab and run"
echo "'Build APK (OpenDroid + Toni)' -- but first follow android-agent/README.md"
echo "to clone OpenDroid and run pet/install.sh, since the upstream app is not"
echo "committed here."
