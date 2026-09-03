---
id: evidence-before-completion
name: Evidence before completion
description: Build reproducible evidence before a completion or readiness claim.
category: core
activation_mode: planning-only
requires_approval: false
tags: verification, acceptance, testing, evidence, release
routing_terms: verify, verification, validate, test, completion, done, release
source_refs: luo-kai-catalogue, antigravity-awesome-skills, grok-custom-skills
jinwoo_native: true
---
# Evidence before completion

## Purpose
Use this native skill before claiming that a change, plan, or integration is complete. It turns a vague success claim into a small set of observable checks.

## Procedure
1. Restate the requested outcome and list the facts that must be true.
2. Name the smallest deterministic checks that can establish each fact.
3. Run only checks already authorised by the active workspace and policy boundary.
4. Record pass, fail, skipped, and unknown results separately.
5. If evidence is missing, report the work as incomplete and name the next safe check.

## Output
Return an acceptance table with: criterion, evidence source, outcome, remaining risk, and recommended next step. Never infer a passing result from an unrun command, an unavailable service, or a partial log.

## Safety boundary
This skill plans and evaluates evidence. It does not run tests, install dependencies, mutate files, contact a service, or alter an audit record. Any impactful verification action remains separately approval-gated.
