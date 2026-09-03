---
id: agent-governance
name: Agent governance
description: Define accountable boundaries for native agents and skill handoffs.
category: core
activation_mode: planning-only
requires_approval: false
tags: governance, policy, audit, handoff, accountability
routing_terms: governance, policy, guardrail, audit, agent, handoff, control
source_refs: mouad-skills, grok-custom-skills, github-awesome-copilot
jinwoo_native: true
---
# Agent governance

## Purpose
Use this skill when a task crosses agent roles, capability boundaries, or approval levels. It keeps Jinwoo as the canonical controller rather than allowing a named skill or external framework to become an independent authority.

## Procedure
1. Identify the task owner, data boundary, requested outcome, and prohibited actions.
2. Assign Planner, Executor, and Verifier responsibilities without spawning workers.
3. State the policy classification and every approval edge before an action is proposed.
4. Require a redacted audit event for a plan decision, state transition, or approved handoff.
5. Prefer a narrower native skill when the request can be decomposed.

## Output
Produce a responsibility map containing owner, allowed inputs, allowed outputs, stop condition, reviewer, and escalation condition.

## Safety boundary
A governance map grants no tool access. It cannot weaken policy, override user approval, expose credentials, change a workspace boundary, or start a background agent.
