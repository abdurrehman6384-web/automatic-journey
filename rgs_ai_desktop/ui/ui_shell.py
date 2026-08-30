"""
ui_shell.py — IRIS-style PyQt6 Desktop Shell (RGS AI Desktop)
===============================================================

SINGLE UI for the entire system.
  Visual design inspired by IRIS-GO / IRIS-Mini glass-panel look
  (implemented in original PyQt6 — NO React/TSX code copied).

Layout:
  ┌─────────────────────────────────────────────────────────────┐
  │  TOP BAR  — model label | license tier | system status      │
  ├──────────┬──────────────────────────────┬───────────────────┤
  │          │                              │                   │
  │  LEFT    │    CENTRE  — animated ORB    │   RIGHT           │
  │  DOCK    │    + status pulse animation  │   PANEL           │
  │  (agents)│                              │   (activity log)  │
  │          │                              │                   │
  ├──────────┴──────────────────────────────┴───────────────────┤
  │  BOTTOM BAR — chat / voice command input                    │
  └─────────────────────────────────────────────────────────────┘

Dark glass theme:
  - Semi-transparent panels with QGraphicsBlurEffect behind them
  - Accent colours: cyan #00FFFF orb, dark navy #0A0F1E background
  - QPropertyAnimation on orb glow for active / idle states
  - Frosted-glass QSS on all panels
"""

from __future__ import annotations

import sys
import json
import threading
import time
import math
from typing import Any, Dict, List, Optional, Callable

# ── PyQt6 guard ───────────────────────────────────────────────────────────────
try:
    from PyQt6.QtWidgets import (
        QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
        QLabel, QLineEdit, QPushButton, QListWidget, QListWidgetItem,
        QTextEdit, QSplitter, QFrame, QScrollArea, QSizePolicy,
        QGraphicsDropShadowEffect, QStatusBar,
    )
    from PyQt6.QtCore import (
        Qt, QPropertyAnimation, QEasingCurve, QTimer, pyqtSignal,
        QThread, QObject, QSize, QRect, pyqtProperty,
    )
    from PyQt6.QtGui import (
        QColor, QPainter, QBrush, QPen, QRadialGradient, QFont,
        QLinearGradient, QPalette, QIcon, QPixmap,
    )
    _HAS_PYQT6 = True
except ImportError:
    _HAS_PYQT6 = False

# ── Colour palette ────────────────────────────────────────────────────────────
C_BG          = "#0A0F1E"      # deep navy
C_PANEL       = "rgba(16,26,54,200)"
C_GLASS       = "rgba(0,255,255,12)"
C_ACCENT      = "#00FFFF"      # cyan
C_ACCENT2     = "#7B68EE"      # slate-blue
C_TEXT        = "#E0F7FF"
C_TEXT_DIM    = "#5A8090"
C_BORDER      = "rgba(0,255,255,35)"
C_ORB_IDLE    = "#003344"
C_ORB_ACTIVE  = "#00FFFF"
C_LOG_USER    = "#00FFD0"
C_LOG_AGENT   = "#A0CFFF"
C_LOG_SYSTEM  = "#5A8090"
C_ERR         = "#FF4466"


# ── Glass-panel QSS ──────────────────────────────────────────────────────────
GLASS_QSS = f"""
QMainWindow {{
    background-color: {C_BG};
}}
QWidget#CentralWidget {{
    background-color: {C_BG};
}}
QFrame#GlassPanel {{
    background-color: {C_PANEL};
    border: 1px solid {C_BORDER};
    border-radius: 12px;
}}
QLabel {{
    color: {C_TEXT};
    font-family: 'Segoe UI', 'JetBrains Mono', monospace;
}}
QLabel#DimLabel {{
    color: {C_TEXT_DIM};
    font-size: 10px;
}}
QLabel#AccentLabel {{
    color: {C_ACCENT};
    font-weight: bold;
}}
QListWidget {{
    background-color: transparent;
    border: none;
    color: {C_TEXT};
    font-family: 'Segoe UI', monospace;
    font-size: 12px;
}}
QListWidget::item {{
    padding: 6px 8px;
    border-radius: 6px;
    margin: 1px 4px;
}}
QListWidget::item:selected {{
    background-color: rgba(0,255,255,30);
    color: {C_ACCENT};
    border: 1px solid {C_BORDER};
}}
QListWidget::item:hover {{
    background-color: rgba(0,255,255,15);
}}
QTextEdit {{
    background-color: rgba(5,10,25,180);
    border: 1px solid {C_BORDER};
    border-radius: 8px;
    color: {C_TEXT};
    font-family: 'JetBrains Mono', 'Consolas', monospace;
    font-size: 12px;
    padding: 8px;
}}
QLineEdit {{
    background-color: rgba(5,10,25,200);
    border: 1px solid {C_BORDER};
    border-radius: 20px;
    color: {C_TEXT};
    font-family: 'Segoe UI', monospace;
    font-size: 13px;
    padding: 8px 16px;
    selection-background-color: rgba(0,255,255,50);
}}
QLineEdit:focus {{
    border: 1px solid {C_ACCENT};
    background-color: rgba(0,255,255,8);
}}
QPushButton {{
    background-color: rgba(0,255,255,20);
    border: 1px solid {C_BORDER};
    border-radius: 16px;
    color: {C_ACCENT};
    font-family: 'Segoe UI', monospace;
    font-size: 12px;
    padding: 6px 14px;
    min-width: 60px;
}}
QPushButton:hover {{
    background-color: rgba(0,255,255,40);
    border: 1px solid {C_ACCENT};
}}
QPushButton:pressed {{
    background-color: rgba(0,255,255,60);
}}
QPushButton#VoiceBtn {{
    border-radius: 22px;
    min-width: 44px;
    min-height: 44px;
    font-size: 18px;
    background-color: rgba(123,104,238,20);
    border: 1px solid rgba(123,104,238,60);
    color: #7B68EE;
}}
QPushButton#VoiceBtn:hover {{
    background-color: rgba(123,104,238,50);
}}
QScrollBar:vertical {{
    background: transparent;
    width: 6px;
    border-radius: 3px;
}}
QScrollBar::handle:vertical {{
    background: {C_BORDER};
    border-radius: 3px;
    min-height: 20px;
}}
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
    height: 0;
}}
QStatusBar {{
    background-color: rgba(5,10,25,220);
    color: {C_TEXT_DIM};
    font-size: 10px;
    border-top: 1px solid {C_BORDER};
}}
QSplitter::handle {{
    background-color: {C_BORDER};
    width: 1px;
}}
"""


# ── Animated Orb Widget ───────────────────────────────────────────────────────
if _HAS_PYQT6:

    class OrbWidget(QWidget):
        """
        Central animated orb — QPropertyAnimation glow pulse.
        Idle: dim navy.   Active: bright cyan with outer glow rings.
        """

        def __init__(self, parent=None):
            super().__init__(parent)
            self._glow_alpha = 0.0
            self._active = False
            self._ring_phase = 0.0
            self.setMinimumSize(160, 160)
            self.setMaximumSize(200, 200)

            # pulse timer
            self._timer = QTimer(self)
            self._timer.timeout.connect(self._tick)
            self._timer.start(40)      # ~25 fps

        # -- property (for QPropertyAnimation) --------------------------------
        def _get_glow(self) -> float:
            return self._glow_alpha

        def _set_glow(self, v: float) -> None:
            self._glow_alpha = max(0.0, min(1.0, v))
            self.update()

        glow = pyqtProperty(float, _get_glow, _set_glow)

        # -- public API --------------------------------------------------------
        def set_active(self, active: bool) -> None:
            self._active = active
            if active:
                self._start_pulse()
            else:
                self._stop_pulse()

        def _start_pulse(self):
            self._anim = QPropertyAnimation(self, b"glow", self)
            self._anim.setDuration(900)
            self._anim.setStartValue(0.3)
            self._anim.setEndValue(1.0)
            self._anim.setEasingCurve(QEasingCurve.Type.SineCurve)
            self._anim.setLoopCount(-1)
            self._anim.start()

        def _stop_pulse(self):
            if hasattr(self, "_anim"):
                self._anim.stop()
            self._glow_alpha = 0.15
            self.update()

        def _tick(self):
            self._ring_phase = (self._ring_phase + 0.05) % (2 * math.pi)
            if self._active:
                self.update()

        # -- painting ----------------------------------------------------------
        def paintEvent(self, event):
            painter = QPainter(self)
            painter.setRenderHint(QPainter.RenderHint.Antialiasing)

            w, h = self.width(), self.height()
            cx, cy = w // 2, h // 2
            r = min(w, h) // 2 - 10

            alpha = self._glow_alpha if self._active else 0.15

            # outer glow rings (animated when active)
            if self._active:
                for i in range(3):
                    ring_r = r + 18 + i * 14 + int(6 * math.sin(self._ring_phase + i * 0.9))
                    ring_alpha = int(max(0, 120 - i * 40) * alpha)
                    pen = QPen(QColor(0, 255, 255, ring_alpha))
                    pen.setWidth(1)
                    painter.setPen(pen)
                    painter.drawEllipse(cx - ring_r, cy - ring_r, ring_r * 2, ring_r * 2)

            # main orb radial gradient
            grad = QRadialGradient(cx, cy, r)
            if self._active:
                core_a = int(255 * alpha)
                grad.setColorAt(0.0, QColor(0, 255, 255, core_a))
                grad.setColorAt(0.35, QColor(0, 200, 220, int(core_a * 0.7)))
                grad.setColorAt(0.7, QColor(0, 80, 120, int(core_a * 0.4)))
                grad.setColorAt(1.0, QColor(0, 30, 60, 0))
            else:
                grad.setColorAt(0.0, QColor(0, 100, 140, 180))
                grad.setColorAt(0.5, QColor(0, 50, 80, 120))
                grad.setColorAt(1.0, QColor(0, 20, 40, 0))

            painter.setBrush(QBrush(grad))
            painter.setPen(Qt.PenStyle.NoPen)
            painter.drawEllipse(cx - r, cy - r, r * 2, r * 2)

            # inner highlight
            hi_grad = QRadialGradient(cx - r // 4, cy - r // 4, r // 3)
            hi_a = int(80 * alpha) if self._active else 20
            hi_grad.setColorAt(0.0, QColor(255, 255, 255, hi_a))
            hi_grad.setColorAt(1.0, QColor(255, 255, 255, 0))
            painter.setBrush(QBrush(hi_grad))
            painter.drawEllipse(cx - r, cy - r, r * 2, r * 2)

            # centre status text
            painter.setPen(QPen(QColor(0, 255, 255, int(200 * (0.3 + alpha * 0.7)))))
            font = QFont("Segoe UI", 9)
            font.setLetterSpacing(QFont.SpacingType.AbsoluteSpacing, 1.5)
            painter.setFont(font)
            label = "ACTIVE" if self._active else "IDLE"
            painter.drawText(QRect(cx - 40, cy - 10, 80, 20),
                             Qt.AlignmentFlag.AlignCenter, label)
            painter.end()


    # ── Worker thread for agent dispatch ─────────────────────────────────────
    class AgentWorker(QObject):
        """Runs agent dispatch in a QThread so the UI stays responsive."""
        result_ready = pyqtSignal(str, dict)   # (query, result_dict)
        error_signal = pyqtSignal(str)

        def __init__(self, dispatch_fn: Callable):
            super().__init__()
            self._dispatch = dispatch_fn
            self._queue: list = []
            self._lock = threading.Lock()

        def submit(self, query: str) -> None:
            with self._lock:
                self._queue.append(query)

        def run_next(self) -> None:
            with self._lock:
                if not self._queue:
                    return
                query = self._queue.pop(0)
            try:
                result = self._dispatch(query)
                self.result_ready.emit(query, result)
            except Exception as exc:
                self.error_signal.emit(str(exc))


    # ── Main Shell Window ─────────────────────────────────────────────────────
    class IRISShell(QMainWindow):
        """
        IRIS-style PyQt6 shell — the ONE UI for the entire RGS AI Desktop.

        No secondary windows open.  All agents are exposed through this shell.
        """

        # signals
        new_log_entry = pyqtSignal(str, str)   # (text, kind) — kind in user/agent/system/error

        def __init__(self, orchestration_core=None):
            super().__init__()
            self._core = orchestration_core
            self._agent_list: List[Dict] = []
            self._setup_window()
            self._setup_ui()
            self._apply_theme()
            self._wire_signals()
            self._start_status_ticker()

        # ── window setup ──────────────────────────────────────────────────────
        def _setup_window(self):
            self.setWindowTitle("RGS AI Desktop — IRIS Shell")
            self.resize(1280, 800)
            self.setMinimumSize(960, 600)
            # App-level dark palette so native widgets don't flash light
            pal = self.palette()
            pal.setColor(QPalette.ColorRole.Window, QColor(C_BG))
            pal.setColor(QPalette.ColorRole.WindowText, QColor(C_TEXT))
            pal.setColor(QPalette.ColorRole.Base, QColor("#05091A"))
            pal.setColor(QPalette.ColorRole.AlternateBase, QColor("#0A0F1E"))
            pal.setColor(QPalette.ColorRole.Text, QColor(C_TEXT))
            pal.setColor(QPalette.ColorRole.ButtonText, QColor(C_ACCENT))
            pal.setColor(QPalette.ColorRole.Button, QColor("#0D1A3A"))
            pal.setColor(QPalette.ColorRole.Highlight, QColor(C_ACCENT))
            self.setPalette(pal)

        # ── UI construction ──────────────────────────────────────────────────
        def _setup_ui(self):
            central = QWidget()
            central.setObjectName("CentralWidget")
            self.setCentralWidget(central)
            root_layout = QVBoxLayout(central)
            root_layout.setContentsMargins(10, 6, 10, 4)
            root_layout.setSpacing(6)

            # 1 — Top Bar
            root_layout.addWidget(self._build_top_bar())

            # 2 — Middle area (left dock + centre orb + right log)
            splitter = QSplitter(Qt.Orientation.Horizontal)
            splitter.setHandleWidth(1)
            splitter.addWidget(self._build_left_dock())
            splitter.addWidget(self._build_centre_panel())
            splitter.addWidget(self._build_right_panel())
            splitter.setSizes([200, 640, 320])
            splitter.setChildrenCollapsible(False)
            root_layout.addWidget(splitter, stretch=1)

            # 3 — Bottom command bar
            root_layout.addWidget(self._build_bottom_bar())

            # Status bar
            self.statusBar().showMessage("RGS AI Desktop ready.")

        # ── Top bar ───────────────────────────────────────────────────────────
        def _build_top_bar(self) -> QWidget:
            bar = QFrame()
            bar.setObjectName("GlassPanel")
            bar.setFixedHeight(44)
            lay = QHBoxLayout(bar)
            lay.setContentsMargins(16, 0, 16, 0)
            lay.setSpacing(12)

            logo = QLabel("◈  RGS AI Desktop")
            logo.setObjectName("AccentLabel")
            logo.setFont(QFont("Segoe UI", 14, QFont.Weight.Bold))
            lay.addWidget(logo)

            lay.addStretch(1)

            self._model_label = QLabel("Model: —")
            self._model_label.setObjectName("DimLabel")
            lay.addWidget(self._model_label)

            sep = QLabel("|")
            sep.setObjectName("DimLabel")
            lay.addWidget(sep)

            self._tier_label = QLabel("Tier: STARTER")
            self._tier_label.setObjectName("AccentLabel")
            lay.addWidget(self._tier_label)

            sep2 = QLabel("|")
            sep2.setObjectName("DimLabel")
            lay.addWidget(sep2)

            self._status_label = QLabel("● ONLINE")
            self._status_label.setObjectName("AccentLabel")
            lay.addWidget(self._status_label)

            return bar

        # ── Left dock (agent list) ────────────────────────────────────────────
        def _build_left_dock(self) -> QFrame:
            dock = QFrame()
            dock.setObjectName("GlassPanel")
            lay = QVBoxLayout(dock)
            lay.setContentsMargins(8, 12, 8, 12)
            lay.setSpacing(8)

            hdr = QLabel("AGENTS")
            hdr.setObjectName("AccentLabel")
            hdr.setFont(QFont("Segoe UI", 10, QFont.Weight.Bold))
            hdr.setAlignment(Qt.AlignmentFlag.AlignCenter)
            lay.addWidget(hdr)

            self._agent_list_widget = QListWidget()
            self._agent_list_widget.setObjectName("AgentList")
            lay.addWidget(self._agent_list_widget, stretch=1)

            # default agent items — includes all RASHEED agents
            for name, icon in [
                ("🔧  ToolRunner",      "tool_runner"),
                ("🖥  ScreenControl",   "screen_control"),
                ("👁  Vision",          "vision"),
                ("🧠  Memory",          "memory"),
                ("🌐  Browser",         "browser"),
                ("💻  CodeExec",        "code_exec"),
                ("🎙  Voice",           "voice"),
                ("🔌  PluginManager",   "plugin_lifecycle"),
                ("─────────────",       "separator"),
                ("🖥  SystemControl",   "system"),
                ("🌙  Lifestyle",       "lifestyle"),
                ("🎨  Generative AI",   "generative"),
                ("⚡  Proactive",       "proactive"),
                ("🔒  Security",        "security"),
                ("💬  Chat",            "chat"),
            ]:
                item = QListWidgetItem(name)
                item.setData(Qt.ItemDataRole.UserRole, icon)
                self._agent_list_widget.addItem(item)

            return dock

        # ── Centre orb panel ──────────────────────────────────────────────────
        def _build_centre_panel(self) -> QFrame:
            panel = QFrame()
            panel.setObjectName("GlassPanel")
            lay = QVBoxLayout(panel)
            lay.setContentsMargins(20, 20, 20, 20)
            lay.setSpacing(12)
            lay.setAlignment(Qt.AlignmentFlag.AlignCenter)

            self._orb = OrbWidget()
            orb_wrap = QWidget()
            orb_lay = QHBoxLayout(orb_wrap)
            orb_lay.setAlignment(Qt.AlignmentFlag.AlignCenter)
            orb_lay.addWidget(self._orb)
            lay.addWidget(orb_wrap, stretch=1)

            self._status_text = QLabel("Ready")
            self._status_text.setAlignment(Qt.AlignmentFlag.AlignCenter)
            self._status_text.setObjectName("AccentLabel")
            self._status_text.setFont(QFont("Segoe UI", 11))
            lay.addWidget(self._status_text)

            self._task_label = QLabel("No active task")
            self._task_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            self._task_label.setObjectName("DimLabel")
            lay.addWidget(self._task_label)

            return panel

        # ── Right panel (activity log) ────────────────────────────────────────
        def _build_right_panel(self) -> QFrame:
            panel = QFrame()
            panel.setObjectName("GlassPanel")
            lay = QVBoxLayout(panel)
            lay.setContentsMargins(8, 12, 8, 12)
            lay.setSpacing(8)

            hdr = QLabel("ACTIVITY LOG")
            hdr.setObjectName("AccentLabel")
            hdr.setFont(QFont("Segoe UI", 10, QFont.Weight.Bold))
            hdr.setAlignment(Qt.AlignmentFlag.AlignCenter)
            lay.addWidget(hdr)

            self._log = QTextEdit()
            self._log.setReadOnly(True)
            self._log.setObjectName("LogPanel")
            lay.addWidget(self._log, stretch=1)

            clear_btn = QPushButton("Clear Log")
            clear_btn.clicked.connect(self._log.clear)
            lay.addWidget(clear_btn)

            return panel

        # ── Bottom command bar ────────────────────────────────────────────────
        def _build_bottom_bar(self) -> QFrame:
            bar = QFrame()
            bar.setObjectName("GlassPanel")
            bar.setFixedHeight(60)
            lay = QHBoxLayout(bar)
            lay.setContentsMargins(12, 8, 12, 8)
            lay.setSpacing(10)

            self._cmd_input = QLineEdit()
            self._cmd_input.setPlaceholderText("Type a command or question…")
            self._cmd_input.returnPressed.connect(self._on_submit)
            lay.addWidget(self._cmd_input, stretch=1)

            send_btn = QPushButton("Send ▶")
            send_btn.setObjectName("SendBtn")
            send_btn.clicked.connect(self._on_submit)
            lay.addWidget(send_btn)

            self._voice_btn = QPushButton("🎙")
            self._voice_btn.setObjectName("VoiceBtn")
            self._voice_btn.setToolTip("Push to talk (Voice)")
            self._voice_btn.clicked.connect(self._on_voice_btn)
            lay.addWidget(self._voice_btn)

            return bar

        # ── Theme application ─────────────────────────────────────────────────
        def _apply_theme(self):
            self.setStyleSheet(GLASS_QSS)
            # drop shadow on status bar
            shadow = QGraphicsDropShadowEffect()
            shadow.setBlurRadius(18)
            shadow.setColor(QColor(0, 255, 255, 40))
            shadow.setOffset(0, 0)
            self._orb.setGraphicsEffect(shadow)

        # ── Signal wiring ────────────────────────────────────────────────────
        def _wire_signals(self):
            self.new_log_entry.connect(self._append_log)

        # ── Status ticker ─────────────────────────────────────────────────────
        def _start_status_ticker(self):
            self._tick_timer = QTimer(self)
            self._tick_timer.timeout.connect(self._update_status_bar)
            self._tick_timer.start(5000)

        def _update_status_bar(self):
            ts = time.strftime("%H:%M:%S")
            agents = len(self._agent_list_widget)
            self.statusBar().showMessage(
                f"RGS AI Desktop  |  {agents} agents loaded  |  {ts}"
            )
            if self._core:
                try:
                    st = self._core.status()
                    tier = st["license"]["tier"]
                    self._tier_label.setText(f"Tier: {tier}")
                except Exception:
                    pass

        # ── Log helpers ───────────────────────────────────────────────────────
        def _append_log(self, text: str, kind: str = "system"):
            colour = {
                "user":   C_LOG_USER,
                "agent":  C_LOG_AGENT,
                "system": C_LOG_SYSTEM,
                "error":  C_ERR,
            }.get(kind, C_TEXT)
            ts = time.strftime("%H:%M:%S")
            html = (
                f'<span style="color:{C_TEXT_DIM}">[{ts}]</span> '
                f'<span style="color:{colour}">{text}</span>'
            )
            self._log.append(html)
            sb = self._log.verticalScrollBar()
            sb.setValue(sb.maximum())

        def log(self, text: str, kind: str = "system") -> None:
            """Thread-safe log append."""
            self.new_log_entry.emit(text, kind)

        # ── Command handling ──────────────────────────────────────────────────
        def _on_submit(self):
            text = self._cmd_input.text().strip()
            if not text:
                return
            self._cmd_input.clear()
            self.log(f"You: {text}", "user")
            self._orb.set_active(True)
            self._status_text.setText("Processing…")
            self._task_label.setText(text[:60] + ("…" if len(text) > 60 else ""))

            # Run dispatch in worker thread
            def _run():
                try:
                    if self._core:
                        result = self._core.dispatch(text)
                        ok = result.get("ok", False)
                        parts = []
                        for r in result.get("results", []):
                            if r.get("ok"):
                                val = r.get("result", "")
                                if isinstance(val, dict):
                                    val = json.dumps(val, indent=2)
                                parts.append(str(val)[:500])
                            else:
                                parts.append(f"[Error] {r.get('error')}")
                        reply = "\n".join(parts) if parts else "(no result)"
                    else:
                        reply = f"[Echo] {text}  (no orchestration core wired)"
                        ok = True
                    self.log(f"Agent: {reply}", "agent" if ok else "error")
                except Exception as exc:
                    self.log(f"Error: {exc}", "error")
                finally:
                    # UI update must be on main thread — use timer
                    QTimer.singleShot(0, self._on_task_done)

            threading.Thread(target=_run, daemon=True).start()

        def _on_task_done(self):
            self._orb.set_active(False)
            self._status_text.setText("Ready")
            self._task_label.setText("No active task")

        def _on_voice_btn(self):
            self.log("Voice: push-to-talk activated…", "system")
            self._orb.set_active(True)
            self._status_text.setText("Listening…")

            def _listen():
                try:
                    from rgs_ai_desktop.agents.voice_agent import AGENT as va
                    result = va.push_to_talk(timeout=6.0)
                    if result["ok"]:
                        text = result["result"]["text"]
                        self.log(f"Voice heard: {text}", "user")
                        # feed into command pipeline
                        self._cmd_input.setText(text)
                        QTimer.singleShot(0, self._on_submit)
                    else:
                        self.log(f"Voice: {result.get('error', 'nothing heard')}", "system")
                except Exception as exc:
                    self.log(f"Voice error: {exc}", "error")
                finally:
                    QTimer.singleShot(0, self._on_task_done)

            threading.Thread(target=_listen, daemon=True).start()

        # ── Public API for external integration ───────────────────────────────
        def update_model_label(self, model_name: str) -> None:
            self._model_label.setText(f"Model: {model_name}")

        def update_tier_label(self, tier: str) -> None:
            self._tier_label.setText(f"Tier: {tier}")

        def add_agent_to_dock(self, display_name: str, agent_key: str) -> None:
            item = QListWidgetItem(display_name)
            item.setData(Qt.ItemDataRole.UserRole, agent_key)
            self._agent_list_widget.addItem(item)

        def set_orb_active(self, active: bool) -> None:
            QTimer.singleShot(0, lambda: self._orb.set_active(active))


# ── Headless stub (when PyQt6 is absent) ─────────────────────────────────────
else:
    class IRISShell:
        """Stub when PyQt6 is not installed."""
        def __init__(self, orchestration_core=None):
            self._core = orchestration_core
            print("[IRISShell] PyQt6 not installed — running in headless stub mode")

        def log(self, text: str, kind: str = "system") -> None:
            print(f"[{kind}] {text}")

        def set_orb_active(self, active: bool) -> None:
            print(f"[orb] active={active}")


# ── Entry point ───────────────────────────────────────────────────────────────
def launch(orchestration_core=None) -> None:
    """
    Launch the IRIS shell.  Call this from main.py.
    """
    if not _HAS_PYQT6:
        print("PyQt6 not installed.  Install with:  pip install PyQt6")
        print("Running headless stub …")
        shell = IRISShell(orchestration_core)
        shell.log("RGS AI Desktop started (headless)", "system")
        return

    app = QApplication.instance() or QApplication(sys.argv)
    app.setApplicationName("RGS AI Desktop")
    app.setOrganizationName("RGS")

    shell = IRISShell(orchestration_core)
    shell.show()
    shell.log("RGS AI Desktop — IRIS Shell initialised", "system")

    if orchestration_core:
        st = orchestration_core.status()
        tier = st["license"]["tier"]
        shell.update_tier_label(tier)
        for ag in st.get("agents", {}):
            shell.log(f"Agent registered: {ag}", "system")

    sys.exit(app.exec())


if __name__ == "__main__":
    launch()
