---
id: gesture-and-vision-safety-planning
name: Gesture and vision safety planning
description: Plan a camera-off interaction design with privacy and emergency-stop controls.
category: interaction
activation_mode: planning-only
requires_approval: true
tags: gesture, vision, camera, accessibility, privacy
routing_terms: gesture, hand, camera, webcam, vision, virtual mouse, accessibility
source_refs: barehands, gesture-controlled-virtual-mouse
jinwoo_native: true
---
# Gesture and vision safety planning

## Purpose
Use this skill for a future gesture or vision interaction concept while the V1 implementation remains camera-off and device-off.

## Procedure
1. Define the accessibility goal independently of any camera or tracking library.
2. Name required consent, captured data, retention limit, processing location, and deletion behavior.
3. Model false positives, false negatives, accidental activation, and a physical or visible emergency stop.
4. Require a non-camera fallback for every essential action.
5. Propose isolated tests with synthetic data only before requesting any device permission.

## Output
Return an interaction safety brief with consent copy, data-flow diagram description, fallback, emergency stop, calibration limits, and approval gates.

## Safety boundary
No webcam, microphone, frame capture, hand landmark model, biometric data, pointer control, voice route, device access, or physical action is enabled.
