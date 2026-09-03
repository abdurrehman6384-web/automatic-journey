---
id: robotics-software-review
name: Robotics software review
description: Review robotics software architecture and tests without controlling hardware.
category: robotics
activation_mode: planning-only
requires_approval: true
tags: robotics, ros, testing, simulation, safety
routing_terms: robotics, robot, ros, actuator, simulation, hardware, controller
source_refs: robotics-agent-skills
jinwoo_native: true
---
# Robotics software review

## Purpose
Use this skill to reason about software quality and safety architecture for robotics work. It never treats a software plan as authority to operate a physical system.

## Procedure
1. Separate pure logic, simulation, integration, and hardware-in-the-loop concerns.
2. Require a test strategy that begins with deterministic unit tests and synthetic inputs.
3. Identify safety interlocks, operator control, fail-safe state, and evidence needed before any physical trial.
4. Keep credentials, device protocols, maps, and production telemetry outside the planning artifact.
5. Escalate all hardware, actuator, motion, or safety-critical changes to a trained operator and independent sign-off.

## Output
Return a review matrix covering software component, failure mode, safe test layer, evidence, operator boundary, and stop condition.

## Safety boundary
No ROS runtime, simulator, device, network, certificate, actuator, controller, or hardware command is installed, run, generated, or transmitted.
