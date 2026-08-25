#!/usr/bin/env python3
"""Applies the Toni wiring patch to OpenDroidAccessibilityService.kt.

This exists because "make three manual edits" does not survive CI, and because a
blind sed on someone else's service produces a build failure you cannot see. So
this script:

  * matches on **code anchors**, not line numbers (line numbers drift)
  * **verifies** every anchor before writing anything
  * is **idempotent** -- running it twice is a no-op, so CI can always call it
  * **fails loudly** with the anchor it could not find, and writes nothing if any
    anchor is missing (all-or-nothing; no half-patched file)
  * refuses to patch a file it does not recognise as the right version

Usage:
    python3 apply_patch.py <path-to-opendroid>
    python3 apply_patch.py <path-to-opendroid> --check     # verify only
    python3 apply_patch.py <path-to-opendroid> --revert
"""

from __future__ import annotations

import argparse
import shutil
import sys
from pathlib import Path

REL_SERVICE = Path("app/src/main/java/com/opendroid/ai/accessibility/"
                   "OpenDroidAccessibilityService.kt")

MARKER = "// >>> toni-pet-patch >>>"
END_MARKER = "// <<< toni-pet-patch <<<"

# ---------------------------------------------------------------------------
# anchors -- matched verbatim (whitespace-normalised) in the upstream file
# ---------------------------------------------------------------------------
ANCHOR_FIELD = "private val serviceScope = CoroutineScope(Dispatchers.Main + SupervisorJob())"

ANCHOR_REFRESH = """private fun refreshFloatingButtonVisibility() {
        if (showFloatingButtonSetting && !isDeviceLocked) {
            addFloatingButton()
        } else {
            removeFloatingButton()
        }
    }"""

ANCHOR_DESTROY = """serviceScope.cancel()
        removeFloatingButton()
        instance = null"""

# ---------------------------------------------------------------------------
# replacements
# ---------------------------------------------------------------------------
FIELD_INSERT = f"""{MARKER}
    /** Toni, the floating pet. Null until the floating-button setting is on. */
    private var toni: com.opendroid.ai.pet.ToniPetBridge? = null
    {END_MARKER}"""

REFRESH_NEW = f"""private fun refreshFloatingButtonVisibility() {{
        if (showFloatingButtonSetting && !isDeviceLocked) {{
            {MARKER}
            if (toni == null) {{
                toni = com.opendroid.ai.pet.ToniPetBridge(
                    context = this,
                    agentState = agentLoop.agentState,
                    scope = serviceScope,
                    hostIsAccessibilityService = true,
                )
            }}
            toni?.controller?.let {{ c ->
                c.onTap = {{ openMainActivityAction() }}
                c.onLongPress = {{ triggerMicrophoneAction() }}
            }}
            toni?.start()
            {END_MARKER}
        }} else {{
            {MARKER}
            toni?.stop()
            {END_MARKER}
        }}
    }}"""

DESTROY_NEW = f"""{MARKER}
        // stop() before cancel(): it cancels the state-collection job, and
        // cancelling the scope first would orphan the pet's animator.
        toni?.stop()
        toni = null
        {END_MARKER}
        serviceScope.cancel()
        removeFloatingButton()
        instance = null"""


def normalise(text: str) -> str:
    """Collapse whitespace runs so indentation differences do not break matching."""
    return " ".join(text.split())


class PatchError(Exception):
    pass


def find_anchor(text: str, anchor: str, label: str) -> int:
    """Return the index of `anchor` in `text`, matched on normalised whitespace.

    Raises PatchError naming the anchor if it is absent -- the whole point is
    that a drift in upstream code stops the patch instead of silently mangling
    the file.
    """
    norm_text = normalise(text)
    norm_anchor = normalise(anchor)
    if norm_anchor not in norm_text:
        raise PatchError(
            f"anchor '{label}' not found.\n"
            f"  expected (whitespace-insensitive): {norm_anchor[:120]}...\n"
            "  OpenDroid may have changed this code. Open "
            "pet/APPLY.md and apply the edit by hand."
        )
    return norm_text.index(norm_anchor)


def locate_span(text: str, anchor: str) -> tuple[int, int]:
    """Map a normalised-whitespace anchor back to real offsets in `text`."""
    norm_anchor = normalise(anchor)
    # walk the original text tracking normalised position
    norm = []
    index_map = []
    last_was_space = False
    for i, ch in enumerate(text):
        if ch.isspace():
            if not last_was_space:
                norm.append(" ")
                index_map.append(i)
            last_was_space = True
        else:
            norm.append(ch)
            index_map.append(i)
            last_was_space = False
    joined = "".join(norm)
    pos = joined.find(norm_anchor)
    if pos < 0:
        raise PatchError("internal: anchor vanished during span mapping")
    start = index_map[pos]
    end_char = pos + len(norm_anchor) - 1
    end = index_map[end_char] + 1
    return start, end


def apply_patch(text: str) -> str:
    if MARKER in text:
        raise PatchError("already patched (marker present) -- nothing to do")

    # Verify ALL anchors before mutating anything.
    find_anchor(text, ANCHOR_FIELD, "serviceScope field")
    find_anchor(text, ANCHOR_REFRESH, "refreshFloatingButtonVisibility()")
    find_anchor(text, ANCHOR_DESTROY, "onDestroy() teardown")

    # Replace in reverse document order so earlier offsets stay valid.
    spans = []
    for anchor, replacement, label in (
        (ANCHOR_DESTROY, DESTROY_NEW, "onDestroy() teardown"),
        (ANCHOR_REFRESH, REFRESH_NEW, "refreshFloatingButtonVisibility()"),
    ):
        start, end = locate_span(text, anchor)
        spans.append((start, end, replacement, label))

    for start, end, replacement, label in sorted(spans, reverse=True):
        text = text[:start] + replacement + text[end:]

    # The field is an insertion after the anchor, not a replacement.
    start, end = locate_span(text, ANCHOR_FIELD)
    line_end = text.find("\n", end)
    if line_end < 0:
        line_end = len(text)
    text = text[:line_end + 1] + "    " + FIELD_INSERT + "\n" + text[line_end + 1:]

    return text


def revert_from_backup(service: Path) -> bool:
    """Restore the pre-patch file from the `.kt.pre-toni` backup.

    A regex un-patch is not a revert: the patch *replaces* two regions, so
    removing the markers leaves the replaced code gone (it silently deletes
    `addFloatingButton()` / `removeFloatingButton()`). The backup written at
    patch time is the only faithful undo, so that is what we use.
    """
    backup = service.with_suffix(".kt.pre-toni")
    if not backup.is_file():
        raise PatchError(
            f"no backup at {backup} -- cannot revert safely. "
            "Restore the file from git instead: `git checkout -- <path>`."
        )
    shutil.copy2(backup, service)
    return True


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("opendroid", type=Path, help="path to an OpenDroid checkout")
    ap.add_argument("--check", action="store_true",
                    help="verify anchors only; write nothing")
    ap.add_argument("--revert", action="store_true", help="undo a previous patch")
    args = ap.parse_args(argv)

    service = args.opendroid / REL_SERVICE
    if not service.is_file():
        print(f"error: {service} not found -- is this an OpenDroid checkout?",
              file=sys.stderr)
        return 1

    original = service.read_text(encoding="utf-8")

    if args.check:
        try:
            if MARKER in original:
                print("already patched")
            else:
                for anchor, label in (
                    (ANCHOR_FIELD, "serviceScope field"),
                    (ANCHOR_REFRESH, "refreshFloatingButtonVisibility()"),
                    (ANCHOR_DESTROY, "onDestroy() teardown"),
                ):
                    find_anchor(original, anchor, label)
                print("all 3 anchors present -- patch can be applied")
            return 0
        except PatchError as exc:
            print(f"CHECK FAILED: {exc}", file=sys.stderr)
            return 1

    if args.revert:
        try:
            revert_from_backup(service)
        except PatchError as exc:
            print(f"FAILED: {exc}", file=sys.stderr)
            return 1
        print(f"  reverted from backup: {service}")
        return 0

    try:
        if MARKER in original:
            # Already patched. Exit 0, not 1: CI re-runs this on every build and a
            # non-zero here would fail an otherwise-good build.
            print("already patched -- nothing to do")
            return 0
        else:
            result = apply_patch(original)
    except PatchError as exc:
        print(f"FAILED (file unchanged): {exc}", file=sys.stderr)
        return 1

    if result == original:
        print("no change")
        return 0

    backup = service.with_suffix(".kt.pre-toni")
    if not backup.exists():
        shutil.copy2(service, backup)
        print(f"  backup written: {backup.name}")

    service.write_text(result, encoding="utf-8")
    print(f"  patched: {service}")
    print("  NOTE: confirm `openMainActivityAction()` exists in your copy -- see APPLY.md")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
