---
id: multimodal-provider-boundary
name: Multimodal provider boundary
description: Design a provider-neutral multimodal workflow without sending media or credentials.
category: models
activation_mode: planning-only
requires_approval: true
tags: model, provider, multimodal, ocr, document, media
routing_terms: glm, model, provider, ocr, image, pdf, multimodal, api key
source_refs: glm-skills
jinwoo_native: true
---
# Multimodal provider boundary

## Purpose
Use this skill to plan a provider-neutral document, image, or media workflow before selecting a model or submitting data to any service.

## Procedure
1. Specify the input type, sensitivity level, intended output, and local retention policy.
2. Decide whether a local-only route is possible before considering a cloud provider.
3. Identify model, API key, network, copyright, and output-verification risks separately.
4. Require per-request cloud consent and show the exact data class that would leave the device.
5. Keep the workflow interoperable so a provider can be removed without breaking policy ownership.

## Output
Return a model boundary card with input classification, permitted processing location, provider consent state, output checks, retention rule, and fallback.

## Safety boundary
This skill does not install a SDK, download a model, access a key, perform OCR, upload media, call a provider, or produce files from user data.
