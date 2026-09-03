---
id: consented-computer-use-planning
name: Consented computer use planning
description: Design a visible and reversible desktop action proposal without executing it.
category: computer-use
activation_mode: planning-only
requires_approval: true
tags: desktop, computer-use, screen, input, consent
routing_terms: desktop, computer use, screenshot, mouse, keyboard, window, screen
source_refs: desktop-agent, one-m-one-ai-computer-use, acu-computer-use-index
jinwoo_native: true
---
# Consented computer use planning

## Purpose
Use this skill to design a future desktop interaction safely. It is intentionally a proposal layer rather than a desktop controller.

## Procedure
1. State the exact user-visible goal and the selected device/workspace boundary.
2. Break the proposed interaction into previewable steps with an emergency stop and rollback description.
3. Identify every permission: screen capture, accessibility/input, clipboard, window control, and network.
4. Require explicit approval immediately before each consequential step.
5. Design verification that does not expose captured content or perform an unintended action.

## Output
Return a computer-use proposal containing step preview, permission ledger, confirmation point, timeout, stop condition, and redacted audit event.

## Safety boundary
No screenshot, OCR, mouse, keyboard, clipboard, window, browser, shell, or desktop action is available through this skill. It cannot operate a host system.
