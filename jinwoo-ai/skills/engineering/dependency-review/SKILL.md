---
id: dependency-review
name: Dependency review
description: Plan a no-scan dependency and licence review before introducing a package.
category: engineering
activation_mode: planning-only
requires_approval: false
tags: dependency, license, supply-chain, upgrade, security
routing_terms: dependency, package, library, upgrade, cve, license, sbom
source_refs: claude-skills-collection
jinwoo_native: true
---
# Dependency review

## Purpose
Use this skill before adding, updating, or enabling a dependency. It is deliberately useful even when no scanner or package manager is authorised.

## Procedure
1. Identify the exact package, version or commit, language ecosystem, and intended feature.
2. Separate first-party code from transitive dependencies, generated assets, and hosted services.
3. Check licence compatibility, maintenance evidence, provenance, default network behavior, data access, and rollback path.
4. Propose the smallest isolated test plan and an explicit manifest change for user review.
5. Record unresolved questions instead of treating package popularity as safety evidence.

## Output
Return a dependency decision sheet: requested capability, minimum version, licence status, data/network implications, test boundary, approval needed, and rejection criteria.

## Safety boundary
This skill does not install, fetch, scan, execute, or modify a manifest. It never presents a vulnerability result as verified without an authorised scan.
