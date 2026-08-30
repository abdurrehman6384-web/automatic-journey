"""
main.py — RGS AI Desktop entry point
======================================
1. Instantiate OrchestrationCore with proper license tier
2. Load all agent plugins via PluginLifecycleManager
3. Register agents into the orchestrator
4. Launch IRIS shell

Run:
    python -m rgs_ai_desktop.main
    OR
    python rgs_ai_desktop/main.py
"""

from __future__ import annotations

import logging
import os
import sys

# Add repo root to path so relative imports work when run as script
_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _ROOT not in sys.path:
    sys.path.insert(0, _ROOT)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(name)s] %(levelname)s: %(message)s",
    datefmt="%H:%M:%S",
)
log = logging.getLogger("rgs.main")


def build_orchestration_core():
    """
    Wire all agents into the orchestration core.
    Each registration is wrapped in try/except so a broken plugin
    never prevents other agents from loading.
    """
    from rgs_ai_desktop.core.orchestration_core import (
        OrchestrationCore, LicenseGate, LicenseTier,
    )
    from rgs_ai_desktop.services.model_router import ModelRouter

    # License tier from env (default STARTER)
    tier_str = os.environ.get("RGS_LICENSE_TIER", "STARTER").upper()
    tier = {
        "STARTER": LicenseTier.STARTER,
        "PRO": LicenseTier.PRO,
        "GOD_MODE": LicenseTier.GOD_MODE,
    }.get(tier_str, LicenseTier.STARTER)

    llm = ModelRouter.from_env()

    core = OrchestrationCore(LicenseGate(tier))
    log.info("Orchestration core created — tier: %s", tier.value)

    # ── Register agents (each in its own try block) ──────────────────────────

    # ToolRunner
    try:
        from rgs_ai_desktop.agents.tool_runner import REGISTRY as tool_registry, smoke_test as tr_test
        if tr_test():
            core.register_agent(
                "tools", capability="tool_calling",
                fn=lambda goal, **kw: tool_registry.call(
                    kw.get("tool_name", "echo"),
                    kw.get("arguments", {"text": goal})
                ),
                meta={"description": "Goose-inspired tool calling registry"},
            )
    except Exception as exc:
        log.error("ToolRunner load failed: %s", exc)

    # ScreenControlAgent
    try:
        from rgs_ai_desktop.agents.screen_control_agent import AGENT as screen_agent, smoke_test as sc_test
        def _screen_dispatch(goal: str, **kw):
            action = kw.get("action", "screenshot")
            if action == "click":
                return screen_agent.click(kw["x"], kw["y"])
            elif action == "type":
                return screen_agent.type_text(kw.get("text", goal))
            elif action == "hotkey":
                return screen_agent.hotkey(*kw.get("keys", []))
            return screen_agent.screenshot(as_base64=False)
        core.register_agent(
            "screen_control", capability="screen_control",
            fn=_screen_dispatch,
            meta={"description": "Bytebot-inspired mouse/keyboard/screenshot control"},
        )
    except Exception as exc:
        log.error("ScreenControlAgent load failed: %s", exc)

    # VisionAgent
    try:
        from rgs_ai_desktop.agents.vision_agent import AGENT as vision_agent, smoke_test as va_test
        vision_agent.llm = llm.as_callable()
        def _vision_dispatch(goal: str, **kw):
            img = kw.get("image_source")
            if img is None:
                return {"ok": False, "error": "No image_source provided"}
            return vision_agent.describe(img, prompt=goal)
        core.register_agent(
            "vision", capability="vision",
            fn=_vision_dispatch,
            meta={"description": "Self-Operating Computer inspired OCR/SoM vision"},
        )
    except Exception as exc:
        log.error("VisionAgent load failed: %s", exc)

    # MemoryAgent (CANONICAL)
    try:
        from rgs_ai_desktop.agents.memory_agent import AGENT as memory_agent, smoke_test as ma_test
        if ma_test():
            def _memory_dispatch(goal: str, **kw):
                action = kw.get("action", "search")
                if action == "remember":
                    eid = memory_agent.remember(kw.get("content", goal), kind=kw.get("kind", "fact"))
                    return {"ok": True, "id": eid}
                elif action == "forget":
                    return {"ok": memory_agent.forget(kw["entry_id"])}
                elif action == "history":
                    return memory_agent.get_history(kw.get("last_n", 20))
                return memory_agent.search(goal, top_k=kw.get("top_k", 5))
            core.register_agent(
                "memory", capability="memory",
                fn=_memory_dispatch,
                meta={"description": "Hermes-inspired persistent memory + skill learning"},
            )
    except Exception as exc:
        log.error("MemoryAgent load failed: %s", exc)

    # BrowserAgent + KnowledgeBaseAgent
    try:
        from rgs_ai_desktop.agents.browser_agent import BROWSER, KB, smoke_test as ba_test
        if ba_test():
            def _browser_dispatch(goal: str, **kw):
                action = kw.get("action", "fetch")
                url = kw.get("url", "")
                if action == "navigate":
                    return BROWSER.navigate(url)
                elif action == "fetch":
                    return BROWSER.fetch_text(url or goal)
                elif action == "kb_add":
                    return KB.add_document(kw.get("content", goal))
                elif action == "kb_search":
                    return KB.search(goal)
                elif action == "kb_answer":
                    return KB.answer(goal, llm=llm.as_callable())
                return BROWSER.fetch_text(goal)
            core.register_agent(
                "browser", capability="browser_use",
                fn=_browser_dispatch,
                meta={"description": "OpenAgent-inspired browser + RAG knowledge base"},
            )
    except Exception as exc:
        log.error("BrowserAgent load failed: %s", exc)

    # CodeExecAgent
    try:
        from rgs_ai_desktop.agents.code_exec_agent import AGENT as exec_agent, smoke_test as ce_test
        if ce_test():
            def _code_dispatch(goal: str, **kw):
                code = kw.get("code", goal)
                lang = kw.get("language")
                return exec_agent.run(code, language=lang)
            core.register_agent(
                "code_exec", capability="code_exec",
                fn=_code_dispatch,
                meta={"description": "Open Interpreter inspired local code execution"},
            )
    except Exception as exc:
        log.error("CodeExecAgent load failed: %s", exc)

    # VoiceAgent (CANONICAL — merged from OpenDesktop + JARVIS + OpenJarvis)
    try:
        from rgs_ai_desktop.agents.voice_agent import AGENT as voice_agent, smoke_test as voa_test
        if voa_test():
            def _voice_dispatch(goal: str, **kw):
                action = kw.get("action", "speak")
                if action == "speak":
                    return voice_agent.speak(goal)
                elif action == "listen":
                    return voice_agent.listen_once(timeout=kw.get("timeout", 5.0))
                return voice_agent.speak(goal)
            core.register_agent(
                "voice", capability="voice",
                fn=_voice_dispatch,
                meta={"description": "Unified VoiceAgent (OpenDesktop+JARVIS+OpenJarvis merged)"},
            )
    except Exception as exc:
        log.error("VoiceAgent load failed: %s", exc)

    # Simple chat passthrough (routes to LLM)
    try:
        def _chat_dispatch(goal: str, **kw):
            return llm.ask(goal)
        core.register_agent(
            "chat", capability="chat",
            fn=_chat_dispatch,
            meta={"description": "Direct LLM chat"},
        )
    except Exception as exc:
        log.error("Chat agent wiring failed: %s", exc)

    log.info("All agents loaded. Registered: %s", core.agent_names())
    return core


def main():
    log.info("RGS AI Desktop starting…")
    core = build_orchestration_core()

    # Launch the IRIS shell
    from rgs_ai_desktop.ui.ui_shell import launch
    launch(orchestration_core=core)


if __name__ == "__main__":
    main()
