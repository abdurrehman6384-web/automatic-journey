---
id: agent-evaluation
name: Agent evaluation
description: Define behavioral and safety checks for a native skill or agent plan.
category: engineering
activation_mode: planning-only
requires_approval: false
tags: evaluation, reliability, benchmark, regression, safety
routing_terms: evaluate, evaluation, benchmark, reliability, regression, test agent
source_refs: agent-skills-hub, ai-agents-public
jinwoo_native: true
---
# Agent evaluation

## Purpose
Use this skill to decide how a native agent or skill plan should be evaluated before any future runtime is enabled.

## Procedure
1. Define the behavior contract and prohibited outcomes.
2. Build examples for normal use, ambiguous requests, safety-boundary requests, and failure paths.
3. Measure evidence quality, policy adherence, determinism, latency budget, and user-visible explanation quality.
4. Separate test fixtures from real credentials, private workspaces, and third-party targets.
5. Treat a failed or missing measurement as an unresolved risk, not a passing score.

## Output
Return an evaluation matrix with scenario, expected boundary, evidence, pass criteria, failure action, and follow-up owner.

## Safety boundary
This skill does not invoke a model, provider, scanner, benchmark service, or adversarial target. It creates a local evaluation design only.
