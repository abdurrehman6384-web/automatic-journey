---
id: catalogue-curation
name: Catalogue curation
description: Reduce a large public skill catalogue to traceable native candidates.
category: catalogs
activation_mode: planning-only
requires_approval: false
tags: catalog, curation, provenance, deduplication, source-review
routing_terms: catalogue, catalog, skill collection, duplicate, curate, source review
source_refs: luo-kai-catalogue, antigravity-awesome-skills, voltagent-awesome-agent-skills
jinwoo_native: true
---
# Catalogue curation

## Purpose
Use this skill to make a large skills collection manageable without treating every file as automatically safe, useful, or licensable.

## Procedure
1. Group candidates by user outcome rather than their upstream folder name.
2. Merge near-duplicates into one native capability with multiple provenance records.
3. Reject any candidate that lacks a clear purpose, source identity, licence path, safety boundary, or testable output.
4. Preserve the source URL, observed revision, licence signal, reviewed material, and decision in the native provenance registry.
5. Create a new native skill only when it adds a unique, bounded outcome.

## Output
Return a curation report with retained native skills, merged sources, excluded categories, outstanding reviews, and activation state.

## Safety boundary
Curation does not clone repositories, read local agent folders, copy upstream instructions, install registries, or activate a capability.
