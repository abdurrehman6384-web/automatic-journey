---
id: approval-and-permission-boundary
name: Approval and permission boundary
description: Separate safe drafting from actions that require explicit user approval.
category: core
activation_mode: planning-only
requires_approval: false
tags: approval, permissions, consent, privacy, risk
routing_terms: approve, approval, permission, consent, send, upload, install, delete
source_refs: grok-custom-skills, ai-agents-public
jinwoo_native: true
---
# Approval and permission boundary

## Purpose
Use this skill whenever a request may write data, install software, reach a network, use a provider key, operate a device, or affect an external system.

## Procedure
1. Split the request into read-only reasoning and consequential actions.
2. Classify each action as allowed planning, approval-required, or blocked.
3. Show the exact proposed action, scope, data involved, rollback, and timeout before asking for approval.
4. Treat lack of approval as a stop, not an invitation to silently continue.
5. Preserve the original immutable skill instructions; only a session-local controller note may be revised.

## Output
Return a permission ledger with action, impact, selected workspace scope, approval required, and why the action is not yet executed.

## Safety boundary
This skill never self-approves. It cannot send, upload, delete, install, scan, invoke a provider, control a desktop, or use credentials.
