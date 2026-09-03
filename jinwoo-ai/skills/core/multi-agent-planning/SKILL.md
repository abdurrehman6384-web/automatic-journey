---
id: multi-agent-planning
name: Multi-agent planning
description: Compose a bounded Planner Executor Verifier plan from native skills.
category: core
activation_mode: planning-only
requires_approval: false
tags: orchestration, planner, executor, verifier, dependencies
routing_terms: multi-agent, orchestration, swarm, team, workflow, parallel, delegate
source_refs: mouad-skills, agent-skills-hub, ai-agents-public, awesome-llm-apps
jinwoo_native: true
---
# Multi-agent planning

## Purpose
Use this skill to coordinate a complex task without turning the catalog into an uncontrolled swarm. It selects a small set of native skills and makes dependencies visible.

## Procedure
1. State one outcome, bounded inputs, and a maximum of five relevant skills.
2. Give Planner responsibility for decomposition, Executor responsibility for a safe draft, and Verifier responsibility for evidence and policy checks.
3. Make each handoff explicit: required input, expected output, and stop condition.
4. Run independent reasoning in parallel only when outputs do not share mutable state.
5. Route every consequential proposal to the approval boundary before delivery.

## Output
Return a short directed plan with selected skills, role assignments, dependencies, evidence requirements, and a no-execution declaration.

## Safety boundary
This is a topology planner only. It creates no process, model session, queue, schedule, network call, file action, or third-party agent runtime.
