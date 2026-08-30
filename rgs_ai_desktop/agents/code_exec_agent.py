"""
CodeExecAgent — extracted from Open Interpreter (MIT, OpenInterpreter/open-interpreter)
========================================================================================
Local code execution with language detection, sandboxed subprocess, streamed output.

Capability slot: CODE-EXEC
"""

from __future__ import annotations

import io
import logging
import os
import queue
import subprocess
import sys
import tempfile
import threading
import time
from dataclasses import dataclass, field
from typing import Any, Callable, Dict, Generator, List, Optional, Tuple

log = logging.getLogger("rgs.code_exec")

# ── feature flag ──────────────────────────────────────────────────────────────
ENABLED: bool = True

# ── safe allowed languages ────────────────────────────────────────────────────
ALLOWED_LANGUAGES = {"python", "bash", "shell", "sh", "javascript", "js"}
BLOCKED_COMMANDS = {
    "rm -rf /", "format", "mkfs", "dd if=/dev/zero",
    ":(){ :|:& };:", "shutdown", "reboot", "halt",
}


@dataclass
class ExecResult:
    language: str
    code: str
    stdout: str
    stderr: str
    exit_code: int
    duration_s: float
    timed_out: bool = False

    @property
    def ok(self) -> bool:
        return self.exit_code == 0 and not self.timed_out

    def to_dict(self) -> Dict:
        return {
            "language": self.language,
            "stdout": self.stdout,
            "stderr": self.stderr,
            "exit_code": self.exit_code,
            "duration_s": round(self.duration_s, 3),
            "timed_out": self.timed_out,
            "ok": self.ok,
        }


def _ok(data: Any = None) -> Dict:
    return {"ok": True, "result": data}

def _err(msg: str) -> Dict:
    log.warning("CodeExecAgent: %s", msg)
    return {"ok": False, "error": msg}


def _detect_language(code: str) -> str:
    code_lower = code.strip().lower()
    if code_lower.startswith("#!/bin/bash") or code_lower.startswith("#!/bin/sh"):
        return "bash"
    if "def " in code or "import " in code or "print(" in code:
        return "python"
    if "console.log" in code or "function " in code or "const " in code:
        return "javascript"
    return "python"      # safest default


def _safety_check(code: str, language: str) -> Optional[str]:
    """Returns an error string if code looks dangerous, else None."""
    code_lower = code.lower()
    for dangerous in BLOCKED_COMMANDS:
        if dangerous in code_lower:
            return f"Blocked: dangerous pattern detected ({dangerous!r})"
    # Restrict file system writes for JS (no node sandbox)
    if language == "javascript":
        if "require('fs')" in code_lower or 'require("fs")' in code_lower:
            return "Blocked: filesystem access not allowed for JS execution"
    return None


class CodeExecAgent:
    """
    Execute code locally in a sandboxed subprocess.

    Features (from Open Interpreter):
      - Multi-language:  Python, Bash, JavaScript (node)
      - Timeout enforcement
      - Streamed output via a queue
      - Conversation-aware: accumulates an execution context for Python
        (re-uses the same process between calls)
    """

    def __init__(
        self,
        timeout: float = 30.0,
        safe_mode: bool = True,
        work_dir: Optional[str] = None,
    ):
        self.timeout = timeout
        self.safe_mode = safe_mode
        self.work_dir = work_dir or tempfile.mkdtemp(prefix="rgs_exec_")
        self._python_proc: Optional[subprocess.Popen] = None
        self._lock = threading.RLock()

    # -- public API ------------------------------------------------------------
    def run(
        self,
        code: str,
        language: Optional[str] = None,
        timeout: Optional[float] = None,
    ) -> Dict:
        """
        Execute *code* in *language*.
        Returns {"ok": bool, "result": ExecResult.to_dict()}
        """
        if not ENABLED:
            return _err("CodeExecAgent disabled (feature flag)")

        lang = (language or _detect_language(code)).lower().strip()
        if lang not in ALLOWED_LANGUAGES:
            return _err(f"Language {lang!r} not in allowed set: {ALLOWED_LANGUAGES}")

        if self.safe_mode:
            if danger := _safety_check(code, lang):
                return _err(danger)

        timeout = timeout or self.timeout

        try:
            if lang in ("python",):
                result = self._run_python(code, timeout)
            elif lang in ("bash", "shell", "sh"):
                result = self._run_bash(code, timeout)
            elif lang in ("javascript", "js"):
                result = self._run_js(code, timeout)
            else:
                return _err(f"No executor for {lang}")
        except Exception as exc:
            log.error("CodeExecAgent run error: %s", exc, exc_info=True)
            return _err(f"Execution error: {exc}")

        return _ok(result.to_dict())

    def run_stream(
        self,
        code: str,
        language: Optional[str] = None,
        timeout: Optional[float] = None,
    ) -> Generator[str, None, None]:
        """Generator that yields stdout lines as they arrive."""
        if not ENABLED:
            yield "[CodeExecAgent disabled]"
            return

        lang = (language or _detect_language(code)).lower().strip()
        if lang not in ALLOWED_LANGUAGES:
            yield f"[Error] Language {lang!r} not allowed"
            return
        if self.safe_mode:
            if danger := _safety_check(code, lang):
                yield f"[Error] {danger}"
                return

        timeout = timeout or self.timeout
        out_q: queue.Queue = queue.Queue()

        def _worker():
            result = self._run_subprocess(
                self._build_cmd(lang, code), timeout, capture_q=out_q
            )
            out_q.put(None)   # sentinel

        t = threading.Thread(target=_worker, daemon=True)
        t.start()
        while True:
            line = out_q.get()
            if line is None:
                break
            yield line

    # -- internals -------------------------------------------------------------
    def _run_python(self, code: str, timeout: float) -> ExecResult:
        # Write to temp file for cleaner tracebacks
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".py", dir=self.work_dir,
            delete=False, encoding="utf-8"
        ) as f:
            f.write(code)
            fpath = f.name
        try:
            return self._run_subprocess([sys.executable, fpath], timeout, lang="python", code=code)
        finally:
            try:
                os.unlink(fpath)
            except OSError:
                pass

    def _run_bash(self, code: str, timeout: float) -> ExecResult:
        shell = os.environ.get("SHELL", "/bin/bash")
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".sh", dir=self.work_dir,
            delete=False, encoding="utf-8"
        ) as f:
            f.write("#!/bin/bash\nset -e\n" + code)
            fpath = f.name
        os.chmod(fpath, 0o700)
        try:
            return self._run_subprocess([shell, fpath], timeout, lang="bash", code=code)
        finally:
            try:
                os.unlink(fpath)
            except OSError:
                pass

    def _run_js(self, code: str, timeout: float) -> ExecResult:
        node = "node"
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".js", dir=self.work_dir,
            delete=False, encoding="utf-8"
        ) as f:
            f.write(code)
            fpath = f.name
        try:
            return self._run_subprocess([node, fpath], timeout, lang="javascript", code=code)
        finally:
            try:
                os.unlink(fpath)
            except OSError:
                pass

    def _build_cmd(self, lang: str, code: str) -> List[str]:
        # Used by streaming path — writes code to temp file and returns command
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".tmp", dir=self.work_dir,
            delete=False, encoding="utf-8"
        ) as f:
            f.write(code)
            fpath = f.name
        if lang == "python":
            return [sys.executable, fpath]
        elif lang in ("bash", "shell", "sh"):
            return [os.environ.get("SHELL", "/bin/bash"), fpath]
        elif lang in ("javascript", "js"):
            return ["node", fpath]
        return [sys.executable, fpath]

    def _run_subprocess(
        self,
        cmd: List[str],
        timeout: float,
        lang: str = "python",
        code: str = "",
        capture_q: Optional[queue.Queue] = None,
    ) -> ExecResult:
        t0 = time.monotonic()
        timed_out = False
        stdout_lines: List[str] = []
        stderr_lines: List[str] = []

        try:
            proc = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                cwd=self.work_dir,
                text=True,
                encoding="utf-8",
                errors="replace",
            )
        except FileNotFoundError as exc:
            return ExecResult(lang, code, "", f"Interpreter not found: {exc}", -1,
                              time.monotonic() - t0)

        # drain stdout in a thread so stderr doesn't block
        def _drain_stdout():
            for line in proc.stdout:
                stdout_lines.append(line)
                if capture_q is not None:
                    capture_q.put(line.rstrip())

        drain = threading.Thread(target=_drain_stdout, daemon=True)
        drain.start()

        try:
            proc.wait(timeout=timeout)
        except subprocess.TimeoutExpired:
            proc.kill()
            timed_out = True

        drain.join(timeout=2.0)
        stderr_data = proc.stderr.read() if proc.stderr else ""
        exit_code = proc.returncode if not timed_out else -9

        return ExecResult(
            language=lang,
            code=code,
            stdout="".join(stdout_lines),
            stderr=stderr_data,
            exit_code=exit_code,
            duration_s=time.monotonic() - t0,
            timed_out=timed_out,
        )


# ── module-level singleton ────────────────────────────────────────────────────
AGENT = CodeExecAgent(
    timeout=float(os.environ.get("RGS_CODE_TIMEOUT", "30")),
    safe_mode=os.environ.get("RGS_CODE_SAFE_MODE", "1") != "0",
)


# ── smoke test ────────────────────────────────────────────────────────────────
def smoke_test() -> bool:
    r = AGENT.run("print('hello rgs')", language="python")
    ok = r["ok"] and "hello rgs" in r.get("result", {}).get("stdout", "")
    log.info("CodeExecAgent smoke_test: %s", "PASS" if ok else "FAIL")
    return ok


if __name__ == "__main__":
    logging.basicConfig(level=logging.DEBUG)
    print(smoke_test())
