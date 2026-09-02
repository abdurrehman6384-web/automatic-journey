# Controlled Integration Batch 12 — Bounded Next-Ten Upgrade Review Queue

**Status:** complete as a **metadata-only source-review queue**. Every record is
non-executing. This batch adds no third-party source, package, binary, model,
provider route, scanner, database, telemetry exporter, background worker or
unattended discovery process.

## Purpose and boundary

The requested ongoing upgrade discovery is represented safely as one finite
review pass rather than an autonomous Internet loop. The queue makes ten
potential future upgrade lanes visible, revision-pinned and individually
controlled. It is not an implementation selection, a package recommendation,
a licence conclusion, or permission to retrieve or use upstream contents.

During this pass, only public GitHub repository metadata and the default-branch
Git reference were requested. No repository archive, tree, blob, source file,
`SKILL.md`, instruction file, dependency manifest, installer, package, model,
provider, scanner, telemetry route or runtime was downloaded, cloned, copied,
installed, imported or executed.

The GitHub metadata was observed on **2026-09-03**. GitHub-reported licence
metadata is a discovery signal only; it does not establish a compatible licence
or authorise reuse.

## Metadata-only candidate matrix

| Queue | Candidate | Default branch observed | Immutable ref observed | GitHub metadata licence signal | Potential future upgrade target | Controlled status |
| --- | --- | --- | --- | --- | --- | --- |
| 01 | [microsoft/markitdown](https://github.com/microsoft/markitdown) | `main` | `20d06b6c8508f86bfae3252a979a661a14306287` | MIT | Selected-workspace document-to-text boundary planning | Source review required; no document conversion or file read |
| 02 | [microsoft/graphrag](https://github.com/microsoft/graphrag) | `main` | `f40e9a26ce62ba0b3fef8837d24aafdcc6e6c704` | MIT | Local knowledge-map/retrieval boundary planning | Source review required; no corpus, graph, embedding, index or model |
| 03 | [BerriAI/litellm](https://github.com/BerriAI/litellm) | `litellm_internal_staging` | `22cc97fe0a27367d19fdb03a16dbfd497f4360e8` | `NOASSERTION` | Provider-routing and consent-boundary comparison | **Reference only**; no gateway, credential, proxy or provider request |
| 04 | [open-policy-agent/opa](https://github.com/open-policy-agent/opa) | `main` | `25a1d928d6ff43000c428ccfc1970d54afb5494b` | Apache-2.0 | Policy-rule and approval-model comparison | Source review required; Jinwoo remains canonical |
| 05 | [lancedb/lancedb](https://github.com/lancedb/lancedb) | `main` | `2779b75d0d0252a324bc39ab73c9132d3b212484` | Apache-2.0 | Opt-in local retrieval and retention design | Source review required; SQLite remains authoritative today |
| 06 | [promptfoo/promptfoo](https://github.com/promptfoo/promptfoo) | `main` | `48a71cd0163b01ba8efb2954eb0165dd810a6c6e` | MIT | Defensive local evaluation-plan design | Source review required; no target, payload, provider call or report |
| 07 | [astral-sh/ruff](https://github.com/astral-sh/ruff) | `main` | `849bc61d7aea53bf7ded094973b176eb607fe3e5` | MIT | Local lint/format review planning | Source review required; no binary, scan, rewrite or format action |
| 08 | [anchore/syft](https://github.com/anchore/syft) | `main` | `77031752faf6810edf6d57c8ba798408796ea283` | Apache-2.0 | Approved SBOM preflight planning | Source review required; no filesystem/container/image scan or SBOM |
| 09 | [aquasecurity/trivy](https://github.com/aquasecurity/trivy) | `main` | `dcfb99218f072d1f54576af3c0b4f6fc8fe843f3` | Apache-2.0 | Authorised vulnerability/misconfiguration scan-plan design | Source review required; no database, scan target, finding or remediation |
| 10 | [open-telemetry/opentelemetry-python](https://github.com/open-telemetry/opentelemetry-python) | `main` | `eeeaa8f925c2b4430db3c08ef9912249138d7c00` | Apache-2.0 | Local-only observability and audit boundary planning | Source review required; no SDK, instrumentation, collector, exporter or telemetry |

## What was implemented locally

This is a clean-room control-plane addition, not upstream code integration:

- `backend/app/skill_intakes.py` declares the ten immutable source-review
  contracts in `BATCH_TWELVE_UPGRADE_INTAKES`, including their observed refs,
  intended review targets and per-source prohibitions.
- `FrameworkRegistry` exposes each record as a `skill-catalog` review lane with
  `activation_boundary="reference-only"` and `execution_enabled=false`.
  The API now also exposes the recorded `review_commit` field for controlled
  review visibility; this does not fetch or validate the source at runtime.
- The Framework Registry dashboard has a responsive **Upgrade review queue**.
  It displays queue order, future target, review categories, observed revision,
  metadata licence signal, source link, owner and locked state.
- `batch-twelve-upgrade-queue-safety` is part of the native control review. It
  fails if a Batch 12 record is missing, becomes executable, leaves the
  reference-only activation boundary, or changes to an unapproved status.
- `scripts/check_safe_intake.py` now covers Batch 07–12 clean-room review
  surfaces. It rejects direct imports and manifest additions for the ten
  candidate runtime/package families, alongside the existing payload and
  restricted-runtime checks.

## Enforced non-activation conditions

For every queue entry, all of the following remain false in Batch 12:

- no package, binary, SDK, service, database, model, graph, index, parser,
  evaluator, scanner, collector or exporter is installed or started;
- no workspace file, memory item, document, codebase, container, image, cloud
  account, provider key, prompt, trace, metric, log, finding or other user data
  is read, sent, retained or transformed through a candidate;
- no automatic lint, format, scan, policy decision, routing change, retrieval,
  provider fallback, telemetry transmission, remediation or background task is
  performed;
- no candidate changes Jinwoo's policy ownership, user-selected workspace,
  per-request provider consent, audit redaction or explicit approval model; and
- no follow-on Internet discovery happens automatically after this finite pass.

## Required review before any later activation

A candidate can advance only through a separate, explicitly approved review
that at minimum:

1. confirms upstream identity, exact revision, maintained status and the
   specific subtree/artifacts under consideration;
2. reads and evaluates the exact applicable licence, notices, third-party and
   transitive dependency terms for the intended use;
3. maps privacy, local-data, credential, network, retention/deletion,
   telemetry and supply-chain implications;
4. defines a minimal original Jinwoo integration boundary, selected-workspace
   scope, reversible behavior, visible UI and audit events;
5. obtains explicit action-level approval before installation, fetching,
   scanning, parsing, indexing, provider use, telemetry or any write; and
6. passes isolated tests and a fresh control/static-guard update before the
   candidate can become an executable adapter.

For LiteLLM, an exact compatible licence grant is an additional prerequisite
before any source reuse or gateway work is considered. For document, retrieval,
security and observability candidates, the relevant privacy and data-flow
review is also mandatory even if licence review passes.

A later review may deliberately create another **finite** queue after user
instruction. It must not silently start a perpetual clone/install/execute loop.
