---
id: architecture-decision-record
name: Architecture decision record
description: Capture a reversible technical choice with alternatives and evidence.
category: engineering
activation_mode: planning-only
requires_approval: false
tags: architecture, adr, design, tradeoff, decision
routing_terms: adr, architecture, decision, tradeoff, choose, design, alternative
source_refs: grok-custom-skills, github-awesome-copilot
jinwoo_native: true
---
# Architecture decision record

## Purpose
Use this native skill when the project must make a durable technical choice. It makes assumptions and tradeoffs reviewable without pretending an external design is already approved.

## Procedure
1. Define the context and the decision that is actually in scope.
2. List at least two realistic options, including retaining the current design where useful.
3. Evaluate privacy, licence, operations, maintenance, performance, and rollback implications.
4. Name the evidence that supports the recommendation and what remains unverified.
5. Mark the decision as proposed until its required approval is recorded.

## Output
Use the headings: Context, Decision, Alternatives, Consequences, Evidence, Open Questions, Approval, and Rollback.

## Safety boundary
An ADR is documentation, not a command. It cannot change dependencies, architecture, policy, repositories, or external services.
