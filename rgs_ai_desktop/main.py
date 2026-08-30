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

    # ── RASHEED Agents (from abdurrehman-ai project.zip) ─────────────────────

    # SystemControlAgent (app launch, file ops, OS control, notifications)
    try:
        from rgs_ai_desktop.agents.rasheed.system_control_agent import (
            AGENT as sys_agent, smoke_test as sys_test
        )
        if sys_test():
            def _sys_dispatch(goal: str, **kw):
                action = kw.get("action", "get_datetime")
                fn_map = {
                    "open_app":       lambda: sys_agent.open_app(kw.get("app_name", goal)),
                    "close_app":      lambda: sys_agent.close_app(kw.get("app_name", goal)),
                    "open_website":   lambda: sys_agent.open_website(kw.get("url", goal)),
                    "run_command":    lambda: sys_agent.run_command(kw.get("command", goal)),
                    "list_files":     lambda: sys_agent.list_files(kw.get("path", "desktop")),
                    "create_file":    lambda: sys_agent.create_file(kw["path"], kw.get("content", "")),
                    "delete_file":    lambda: sys_agent.delete_file(kw["path"]),
                    "read_file":      lambda: sys_agent.read_file(kw["path"]),
                    "search_file":    lambda: sys_agent.search_file(kw.get("name", goal)),
                    "create_folder":  lambda: sys_agent.create_folder(kw["path"]),
                    "rename_file":    lambda: sys_agent.rename_file(kw["src"], kw["new_name"]),
                    "system_info":    lambda: sys_agent.get_system_info(),
                    "battery":        lambda: sys_agent.get_battery(),
                    "processes":      lambda: sys_agent.get_running_processes(),
                    "kill_process":   lambda: sys_agent.kill_process(kw.get("name_or_pid", "")),
                    "shutdown":       lambda: sys_agent.shutdown(),
                    "restart":        lambda: sys_agent.restart(),
                    "lock":           lambda: sys_agent.lock_screen(),
                    "sleep":          lambda: sys_agent.sleep_pc(),
                    "volume_up":      lambda: sys_agent.volume_up(),
                    "volume_down":    lambda: sys_agent.volume_down(),
                    "mute":           lambda: sys_agent.volume_mute(),
                    "get_clipboard":  lambda: sys_agent.get_clipboard(),
                    "set_clipboard":  lambda: sys_agent.set_clipboard(kw.get("text", goal)),
                    "get_datetime":   lambda: sys_agent.get_datetime(),
                    "notify":         lambda: sys_agent.show_notification(kw.get("title", "RGS"), kw.get("message", goal)),
                    "google_search":  lambda: sys_agent.google_search(goal),
                    "youtube_search": lambda: sys_agent.youtube_search(goal),
                    "screenshot":     lambda: sys_agent.take_screenshot(kw.get("path")),
                }
                fn = fn_map.get(action, lambda: sys_agent.get_datetime())
                return fn()
            core.register_agent(
                "system", capability="tool_calling",
                fn=_sys_dispatch,
                meta={"description": "RASHEED System Control — apps, files, OS, notifications"},
            )
    except Exception as exc:
        log.error("SystemControlAgent load failed: %s", exc)

    # LifestyleAgent (prayer, crypto, budget, reminders, knowledge graph)
    try:
        from rgs_ai_desktop.agents.rasheed.lifestyle_agent import (
            AGENT as life_agent, smoke_test as life_test
        )
        if life_test():
            def _life_dispatch(goal: str, **kw):
                action = kw.pop("action", "prayer_times")
                # inject goal as relevant param if not specified
                if action == "crypto_price" and "symbol" not in kw:
                    kw["symbol"] = goal.upper().replace(" ", "")
                elif action in ("set_reminder",) and "message" not in kw:
                    kw["message"] = goal
                return life_agent.dispatch(action, **kw)
            core.register_agent(
                "lifestyle", capability="tool_calling",
                fn=_life_dispatch,
                meta={"description": "RASHEED Lifestyle — prayer, crypto, budget, reminders, knowledge graph"},
            )
    except Exception as exc:
        log.error("LifestyleAgent load failed: %s", exc)

    # GenerativeAgent (image gen, content creator, PDF assistant)
    try:
        from rgs_ai_desktop.agents.rasheed.generative_agent import (
            AGENT as gen_agent, smoke_test as gen_test
        )
        if gen_test():
            gen_agent.set_llm(llm.as_callable())
            def _gen_dispatch(goal: str, **kw):
                action = kw.pop("action", "write_code")
                if "prompt" not in kw and "topic" not in kw and "description" not in kw:
                    # Route goal to most likely param
                    if action in ("generate_image", "thumbnail_prompt"):
                        kw["prompt"] = goal
                    elif action in ("write_script", "analyze_trends"):
                        kw["topic"] = goal
                    elif action in ("write_code",):
                        kw["description"] = goal
                    elif action in ("seo_optimize",):
                        kw["title"] = goal
                return gen_agent.dispatch(action, **kw)
            core.register_agent(
                "generative", capability="tool_calling",
                fn=_gen_dispatch,
                meta={"description": "RASHEED Generative AI — image, script, SEO, PDF, code"},
            )
    except Exception as exc:
        log.error("GenerativeAgent load failed: %s", exc)

    # ProactiveAgent (clipboard, RPA, digital twin, proactive engine)
    try:
        from rgs_ai_desktop.agents.rasheed.proactive_agent import (
            AGENT as pro_agent, smoke_test as pro_test
        )
        if pro_test():
            def _pro_dispatch(goal: str, **kw):
                action = kw.pop("action", "clipboard_history")
                return pro_agent.dispatch(action, **kw)
            core.register_agent(
                "proactive", capability="tool_calling",
                fn=_pro_dispatch,
                meta={"description": "RASHEED Proactive — clipboard, RPA macros, digital twin"},
            )
    except Exception as exc:
        log.error("ProactiveAgent load failed: %s", exc)

    # SecurityAgent (vault, encryption, network scan, honeypot)
    try:
        from rgs_ai_desktop.agents.rasheed.security_agent import (
            AGENT as sec_agent, smoke_test as sec_test
        )
        if sec_test():
            def _sec_dispatch(goal: str, **kw):
                action = kw.pop("action", "local_ip")
                return sec_agent.dispatch(action, **kw)
            core.register_agent(
                "security", capability="tool_calling",
                fn=_sec_dispatch,
                meta={"description": "RASHEED Security — vault, encryption, network, honeypot"},
            )
    except Exception as exc:
        log.error("SecurityAgent load failed: %s", exc)

    log.info("All agents loaded. Registered: %s", core.agent_names())
    return core


def main():
    log.info("RGS AI Desktop starting…")
    core = build_orchestration_core()

    # Wire extracted repo agents
    from rgs_ai_desktop.services.model_router import ModelRouter
    llm = ModelRouter.from_env()
    build_extracted_agents(core, llm)

    # Launch the IRIS shell
    from rgs_ai_desktop.ui.ui_shell import launch
    launch(orchestration_core=core)


if __name__ == "__main__":
    main()


def build_extracted_agents(core, llm):
    """Wire all extracted repo agents into orchestration core."""
    from rgs_ai_desktop.core.orchestration_core import LicenseTier

    # ── SoCVisionAgent (Self-Operating Computer full loop) ───────────────────
    try:
        from rgs_ai_desktop.agents.extracted.soc_vision_agent import (
            LOOP as soc_loop, OS_CTRL, OCR_FIND, smoke_test as soc_test
        )
        if soc_test():
            soc_loop.set_llm(llm.as_callable())
            def _soc_dispatch(goal: str, **kw):
                action = kw.get("action", "screenshot")
                if action == "run":
                    return soc_loop.run(goal, max_steps=kw.get("max_steps", 10))
                elif action == "click":
                    return OS_CTRL.click_at_percentage(kw["x"], kw["y"])
                elif action == "write":
                    return OS_CTRL.write(kw.get("text", goal))
                elif action == "press":
                    return OS_CTRL.press(kw.get("keys", []))
                elif action == "find_text":
                    import tempfile, base64
                    sc = OS_CTRL.screenshot()
                    if not sc["ok"]:
                        return sc
                    with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as f:
                        import base64 as b64
                        f.write(b64.b64decode(sc["result"]["base64"]))
                        return OCR_FIND.find_text(f.name, kw.get("search_text", goal))
                return OS_CTRL.screenshot()
            core.register_agent("soc_vision", capability="screen_control",
                fn=_soc_dispatch,
                meta={"description": "Self-Operating Computer — full visual operate loop"})
    except Exception as exc:
        log.error("SoCVisionAgent load failed: %s", exc)

    # ── HermesAgent (NousResearch full tool set) ─────────────────────────────
    try:
        from rgs_ai_desktop.agents.extracted.hermes_agent import (
            AGENT as hermes, smoke_test as hermes_test
        )
        if hermes_test():
            def _hermes_dispatch(goal: str, **kw):
                tool = kw.pop("tool", "terminal")
                if not kw and tool in ("web_search", "web_extract"):
                    kw["query" if tool == "web_search" else "url"] = goal
                elif not kw and tool == "terminal":
                    kw["command"] = goal
                elif not kw and tool in ("read_file","write_file","search_files"):
                    kw["path"] = goal
                return hermes.dispatch(tool, **kw)
            core.register_agent("hermes", capability="tool_calling",
                fn=_hermes_dispatch,
                meta={"description": "Hermes (NousResearch) — 40+ tools: files, terminal, web, HA, cron"})
    except Exception as exc:
        log.error("HermesAgent load failed: %s", exc)

    # ── OrkasSEO Agent ────────────────────────────────────────────────────────
    try:
        from rgs_ai_desktop.agents.extracted.orkas_seo_agent import (
            AGENT as orkas, smoke_test as orkas_test
        )
        if orkas_test():
            def _orkas_dispatch(goal: str, **kw):
                action = kw.pop("action", "full_audit")
                if action == "full_audit" and "url" not in kw:
                    kw["url"] = goal
                elif action == "process_keywords" and "keywords" not in kw:
                    kw["keywords"] = [goal]
                return orkas.dispatch(action, **kw)
            core.register_agent("orkas_seo", capability="tool_calling",
                fn=_orkas_dispatch,
                meta={"description": "Orkas SEO — crawl, content audit, GEO score, keywords, CWV"})
    except Exception as exc:
        log.error("OrkasSEO load failed: %s", exc)

    # ── JARVISAgent ───────────────────────────────────────────────────────────
    try:
        from rgs_ai_desktop.agents.extracted.jarvis_agent import (
            AGENT as jarvis, smoke_test as jarvis_test
        )
        if jarvis_test():
            jarvis.set_llm(llm.as_callable())
            def _jarvis_dispatch(goal: str, **kw):
                action = kw.pop("action", "frame_questions")
                if action in ("frame_questions", "research_loop") and "topic" not in kw:
                    kw["topic"] = goal
                elif action == "codebrew" and "task" not in kw:
                    kw["task"] = goal
                elif action == "play_youtube" and "query" not in kw:
                    kw["query"] = goal
                elif action == "github_search" and "query" not in kw:
                    kw["query"] = goal
                return jarvis.dispatch(action, **kw)
            core.register_agent("jarvis", capability="tool_calling",
                fn=_jarvis_dispatch,
                meta={"description": "JARVIS — CodeBrew, question framer, GitHub, YOLOv8, YouTube"})
    except Exception as exc:
        log.error("JARVISAgent load failed: %s", exc)

    # ── OpenDesktopAgent (ContextualBrain + GhostMode + GlobalHotkey) ────────
    try:
        from rgs_ai_desktop.agents.extracted.opendesktop_agent import (
            AGENT as opendesk, smoke_test as od_test
        )
        if od_test():
            def _od_dispatch(goal: str, **kw):
                action = kw.pop("action", "brain_search")
                if action in ("brain_add",) and "content" not in kw:
                    kw["content"] = goal
                    kw.setdefault("node_type", "fact")
                elif action in ("brain_search","brain_context") and "query" not in kw:
                    kw["query"] = goal
                elif action == "ghost_start" and "goal" not in kw:
                    kw["goal"] = goal
                return opendesk.dispatch(action, **kw)
            core.register_agent("opendesktop", capability="tool_calling",
                fn=_od_dispatch,
                meta={"description": "OpenDesktop — ContextualBrain, GhostMode night missions, GlobalHotkey"})
    except Exception as exc:
        log.error("OpenDesktopAgent load failed: %s", exc)

    # ── AutoGPT Blocks Agent ──────────────────────────────────────────────────
    try:
        from rgs_ai_desktop.agents.extracted.autogpt_blocks_agent import (
            AGENT as agpt, smoke_test as agpt_test
        )
        if agpt_test():
            agpt.set_llm(llm.as_callable())
            def _agpt_dispatch(goal: str, **kw):
                block = kw.pop("block", "calculate")
                if block == "calculate" and "expression" not in kw:
                    kw["expression"] = goal
                elif block == "text_split" and "text" not in kw:
                    kw["text"] = goal
                elif block in ("http_get","http_post") and "url" not in kw:
                    kw["url"] = goal
                elif block == "rss_fetch" and "feed_url" not in kw:
                    kw["feed_url"] = goal
                elif block == "time_parse" and "date_string" not in kw:
                    kw["date_string"] = goal
                return agpt.dispatch(block, **kw)
            core.register_agent("autogpt_blocks", capability="tool_calling",
                fn=_agpt_dispatch,
                meta={"description": "AutoGPT Blocks — AI condition, text, math, HTTP, email, KV, RSS, CSV, time, YouTube, Mem0"})
    except Exception as exc:
        log.error("AutoGPTBlocksAgent load failed: %s", exc)

    log.info("Extracted agents loaded. All registered: %s", core.agent_names())


