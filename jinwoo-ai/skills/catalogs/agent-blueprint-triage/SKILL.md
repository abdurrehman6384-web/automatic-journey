---
id: agent-blueprint-triage
name: Agent blueprint triage
description: Turn agent collection examples into a small native proposal set.
category: catalogs
activation_mode: planning-only
requires_approval: false
tags: agents, blueprints, use-cases, triage, design
routing_terms: agent blueprint, use case, agent collection, code review, starter agent
source_refs: five-hundred-ai-agent-projects, awesome-llm-apps, github-awesome-copilot
jinwoo_native: true
---
# Agent blueprint triage

## Purpose
Use this skill when an agent collection offers many examples but the project needs one specific native capability.

## Procedure
1. Describe the user outcome without naming an upstream implementation as the solution.
2. Identify the minimum inputs, outputs, owner, policy classification, and acceptance evidence.
3. Compare up to three patterns at a feature level: no copied prompts, code, credentials, or tool settings.
4. Prefer a small native workflow over importing a general-purpose autonomous agent.
5. Record why adjacent examples were not selected.

## Output
Return a blueprint card with outcome, native roles, inputs, outputs, required approval, known gaps, and original implementation boundary.

## Safety boundary
This skill does not retrieve linked projects, use their dependencies, invoke their providers, or create a hidden agent loop.
