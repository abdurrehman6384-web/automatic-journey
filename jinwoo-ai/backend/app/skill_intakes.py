"""Declarative Batch 11/12 controlled source-review intake contracts.

This module deliberately contains catalogue metadata only. It does not discover,
parse, load, download, execute, or treat any upstream ``SKILL.md`` as a native
Jinwoo capability. Each cited source remains behind Jinwoo's policy, approval,
workspace and audit boundaries.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal


SkillCategory = Literal[
    "orchestration",
    "workflow",
    "coding",
    "research",
    "web-collection",
    "memory",
    "automation",
    "security",
    "governance",
    "computer-use",
    "reference",
    "media",
]
SkillIntakeStatus = Literal["source-review-required", "reference-only"]


@dataclass(frozen=True)
class SkillIntakeSpec:
    """A reviewed source location, never an installed skill payload."""

    id: str
    label: str
    owner_commander: str
    category: SkillCategory
    license: str
    source_url: str | None
    review_commit: str | None
    purpose: str
    capabilities: tuple[str, ...]
    implementation_status: SkillIntakeStatus = "source-review-required"
    guardrails: tuple[str, ...] = ()


_SOURCE_REVIEW_GUARDRAILS = (
    "This is a metadata-only source intake: do not clone, copy, download, parse, install, execute, auto-discover or treat any upstream SKILL.md, prompt, agent profile, plugin, model, asset or configuration as native Jinwoo code.",
    "Do not grant network, provider, shell, browser, repository, workspace-write, desktop, device, camera, microphone, screen, model, upload, send or delete permission from a catalogue record.",
    "A future original adapter needs an exact compatible licence/subtree review, provenance review, narrow typed contract, offline tests, explicit approval, selected-workspace confinement, redacted audit evidence and a disable path.",
)


BATCH_ELEVEN_SKILL_INTAKES: tuple[SkillIntakeSpec, ...] = (
    SkillIntakeSpec(
        id="awesome-llm-apps",
        label="awesome-llm-apps — Source Review Intake",
        owner_commander="Ashborn",
        category="reference",
        license="GitHub metadata reports Apache-2.0; every example, prompt, asset and dependency still needs individual source review",
        source_url="https://github.com/Shubhamsaboo/awesome-llm-apps",
        review_commit="24c85b099d160fbfc6ca4496464727bce78f9d6b",
        purpose="Reference catalogue for independently designed starter, advanced, multi-agent, RAG and always-on safety patterns.",
        capabilities=("Catalogue comparison", "Pattern triage", "Individual-intake planning"),
        implementation_status="reference-only",
    ),
    SkillIntakeSpec(
        id="agency-agents",
        label="agency-agents — Source Review Intake",
        owner_commander="Bellion",
        category="orchestration",
        license="GitHub metadata reports MIT; agent profiles, instructions and any downstream tools need individual source and behavioural review",
        source_url="https://github.com/msitarzewski/agency-agents",
        review_commit="3c9588880b7cafaec325a104899fd8bbe27e7d72",
        purpose="Reference for original division, hand-off and role-description design without importing personalities or autonomous agent loops.",
        capabilities=("Division-design review", "Role-boundary planning", "Handoff-pattern comparison"),
    ),
    SkillIntakeSpec(
        id="github-awesome-copilot",
        label="GitHub awesome-copilot — Source Review Intake",
        owner_commander="Igris",
        category="coding",
        license="GitHub metadata reports MIT; each instruction, agent profile and linked extension needs individual source and tool review",
        source_url="https://github.com/github/awesome-copilot",
        review_commit="6a8fa297b0fe652bd3d7c8946554dc146846b20e",
        purpose="Reference for original coding-role, accessibility and architecture review checklists, never an instruction-file import path.",
        capabilities=("Code-review checklist design", "Accessibility-review planning", "Architecture-pattern comparison"),
    ),
    SkillIntakeSpec(
        id="glm-skills",
        label="GLM Skills — Source Review Intake",
        owner_commander="Blades",
        category="media",
        license="GitHub metadata reports Apache-2.0; provider, multimodal, OCR, image, document and generated-output paths require separate review",
        source_url="https://github.com/zai-org/GLM-skills",
        review_commit="2ecd31c37e75671a4767342ba3a68a84c8f1b848",
        purpose="Reference for original multimodal capability boundaries and output-review design, with no provider, model, OCR or media runtime.",
        capabilities=("Multimodal boundary review", "Document-output planning", "Provider-risk triage"),
        guardrails=(
            "Do not run an installer or package command, authenticate to a GLM provider, load a model, process an image/PDF, generate media, or write generated files from this lane.",
        ),
    ),
    SkillIntakeSpec(
        id="grok-custom-skills",
        label="Grok Custom Skills — Source Review Intake",
        owner_commander="Kaisel",
        category="workflow",
        license="GitHub metadata reports MIT; every skill and provider-specific instruction remains independently review-gated",
        source_url="https://github.com/Stijnman/grok-custom-skills",
        review_commit="5f970c83bf96f9846d4fa6d6c9c11e786cf64fa9",
        purpose="Reference for original workflow, research, integration and quality-assurance pattern comparison.",
        capabilities=("Workflow-pattern review", "Quality-gate planning", "Provider-neutral redesign"),
    ),
    SkillIntakeSpec(
        id="grok-build-skills-source-intake",
        label="Grok Build Local Skills — Source Intake Pending",
        owner_commander="Nox",
        category="computer-use",
        license="Unverified — a local skills path is not a source licence, version pin or permission grant",
        source_url=None,
        review_commit=None,
        purpose="Records the requested local Grok Build skills-path idea without reading a home-directory path or selecting an upstream payload.",
        capabilities=("Local-path boundary review", "Source-provenance planning", "Permission-model design"),
        guardrails=(
            "Do not read ~/.grok/skills or .grok/skills, auto-discover a local skill, modify a local agent configuration, invoke a provider or treat a local file as approved source material from this lane.",
        ),
    ),
    SkillIntakeSpec(
        id="grok-xai-skills-archive",
        label="Grok/xAI Skills Archive — Source Review Intake",
        owner_commander="Kaisel",
        category="reference",
        license="No GitHub licence metadata detected (NOASSERTION); source reuse and runtime activation are prohibited pending an exact grant",
        source_url="https://github.com/SeanVasey/vasey-grok-xai-agent-skills-archive",
        review_commit="53a6cdba9e9fac72e3f9acdc622adfa33b329af0",
        purpose="Reference-only archive locator; it does not establish rights to archived prompts, tools, frameworks or skill folders.",
        capabilities=("Archive-risk triage", "Source-location record", "Individual-grant checklist"),
        implementation_status="reference-only",
    ),
    SkillIntakeSpec(
        id="ai-agents-public",
        label="AI Agents Public — Source Review Intake",
        owner_commander="Jima",
        category="workflow",
        license="GitHub metadata reports MIT; each skill, prompt, agent and downstream integration needs individual source review",
        source_url="https://github.com/vasilyu1983/AI-Agents-public",
        review_commit="3d5bc7c5b82636958d59126173b16a8929eec952",
        purpose="Reference for original task templates and documented human-review workflows without importing prompts or provider behaviour.",
        capabilities=("Task-template review", "Prompt-risk review", "Human-review workflow design"),
    ),
    SkillIntakeSpec(
        id="openai-curated-skills-source-intake",
        label="OpenAI Curated Skills — Source Intake Pending",
        owner_commander="Igris",
        category="coding",
        license="Unverified — no exact OpenAI skill repository/version was supplied or selected",
        source_url=None,
        review_commit=None,
        purpose="Records the requested OpenAI/API/Codex skill area without inferring a repository, package, provider route or prompt payload.",
        capabilities=("Provider-source request", "API-boundary planning", "Prompt-provenance review"),
        guardrails=(
            "Do not infer an official source from a provider name, install a package, authenticate an OpenAI account, send a prompt/data, call an API or enable Codex/tool execution from this lane.",
        ),
    ),
    SkillIntakeSpec(
        id="seedance-inference-skills",
        label="Inference Seedance Skills — Source Review Intake",
        owner_commander="Tusk",
        category="media",
        license="No GitHub licence metadata detected (NOASSERTION); source reuse is prohibited pending an exact grant",
        source_url="https://github.com/inference-sh/skills",
        review_commit="becc25649700d5457772a00e5143e28ccf9e5afa",
        purpose="Same source record, limited to the requested Seedance/video capability review lane; no media or model operation is enabled.",
        capabilities=("Video-workflow boundary review", "Media-provenance planning", "Output-consent design"),
        implementation_status="reference-only",
        guardrails=(
            "Do not submit text/image/video, authenticate to a video provider, download assets, generate clips, store media or export content from this lane.",
        ),
    ),
    SkillIntakeSpec(
        id="leo-seedance-skills",
        label="Seedance Skills (LeoYeAI) — Source Review Intake",
        owner_commander="Tusk",
        category="media",
        license="GitHub metadata reports MIT; prompt, asset, provider, media and IP-use boundaries need individual review",
        source_url="https://github.com/LeoYeAI/seedance-skills",
        review_commit="797e16efaa3c5ac01c0e391d0b8466a87cc5aadc",
        purpose="Reference for original video direction, clip planning and lawful media-output review patterns.",
        capabilities=("Clip-plan review", "Media-rights checklist", "Output-boundary design"),
        guardrails=(
            "Do not load a video model, generate/download/upload media, process a user's image/video, or claim rights to third-party prompts/assets from this lane.",
        ),
    ),
    SkillIntakeSpec(
        id="luo-kai-agent-skills",
        label="ai-agent-skills-by-luo-kai — Source Review Intake",
        owner_commander="Ashborn",
        category="reference",
        license="No GitHub licence metadata detected (NOASSERTION); an aggregated catalogue does not grant reuse rights for its entries",
        source_url="https://github.com/luokai0/ai-agent-skills-by-luo-kai",
        review_commit="4d2fb89cdfb75f3f6fd3c6c5ec9ad90ea129eb3c",
        purpose="Reference-only index for source discovery; its reported scale is not an active Jinwoo agent or skill count.",
        capabilities=("Catalogue discovery record", "Source-provenance checklist", "Individual-review queue"),
        implementation_status="reference-only",
    ),
    SkillIntakeSpec(
        id="agent-skill-os",
        label="AgentSkillOS — Source Review Intake",
        owner_commander="Bellion",
        category="orchestration",
        license="No GitHub licence metadata detected (NOASSERTION); retrieval/orchestration source and any corpus require an exact grant and privacy review",
        source_url="https://github.com/ynulihao/AgentSkillOS",
        review_commit="c3cfae10ea34a13973c461273ad9c5cc4aa907fe",
        purpose="Reference for bounded skill-retrieval architecture analysis only; no index, tree, corpus, orchestration process or remote fetch is loaded.",
        capabilities=("Retrieval-boundary review", "Catalog-scaling analysis", "Privacy-model planning"),
        implementation_status="reference-only",
        guardrails=(
            "Do not download any skill tree/corpus, build an embedding index, start a retrieval/orchestration service, auto-select a skill, or send prompts/data to a remote system from this lane.",
        ),
    ),
    SkillIntakeSpec(
        id="antigravity-awesome-skills",
        label="antigravity-awesome-skills — Source Review Intake",
        owner_commander="Kaisel",
        category="automation",
        license="GitHub metadata reports MIT; its CLI, bundles, install behaviour and each included skill need separate review",
        source_url="https://github.com/sickn33/antigravity-awesome-skills",
        review_commit="7eb694978762421c30855d80de73d1a909a8c335",
        purpose="Reference for original local catalogue selection and stack-validation UX, without any CLI, bundle or auto-install path.",
        capabilities=("Catalogue-UX review", "Stack-validation planning", "Selection-policy design"),
        guardrails=(
            "Do not invoke a CLI, install a bundle, execute a skill, change local configuration, discover files or grant a tool permission from this lane.",
        ),
    ),
    SkillIntakeSpec(
        id="mouad-agent-skills",
        label="mouadja02/skills — Source Review Intake",
        owner_commander="Jima",
        category="reference",
        license="No GitHub licence metadata detected (NOASSERTION); source reuse is prohibited pending an exact grant",
        source_url="https://github.com/mouadja02/skills",
        review_commit="8fa67fad2bb3a9d6d925cdfadb1ad6107486c0a0",
        purpose="Reference-only record for a category-oriented skill catalogue; it creates no native capability.",
        capabilities=("Category-map review", "Source-location record", "Grant-review checklist"),
        implementation_status="reference-only",
    ),
    SkillIntakeSpec(
        id="theneo-awesome-skills",
        label="theneoai/awesome-skills — Source Review Intake",
        owner_commander="Ashborn",
        category="reference",
        license="No GitHub licence metadata detected (NOASSERTION); source reuse is prohibited pending an exact grant",
        source_url="https://github.com/theneoai/awesome-skills",
        review_commit="61fe4f2bb47d6b61505b1b78c2b8ae5fd1ca38dd",
        purpose="Reference-only record for role/domain discovery; every source and claimed persona remains separately review-gated.",
        capabilities=("Role-domain discovery", "Source-provenance planning", "Individual-review queue"),
        implementation_status="reference-only",
    ),
    SkillIntakeSpec(
        id="claude-skills-collection",
        label="claude-skills — Source Review Intake",
        owner_commander="Igris",
        category="coding",
        license="GitHub metadata reports MIT; scripts, plugins, agents, commands and provider behaviours require individual review",
        source_url="https://github.com/alirezarezvani/claude-skills",
        review_commit="19392f7a08264ed00486a251f5b2098321771f94",
        purpose="Reference for original cross-platform engineering and agent-review patterns without copying instructions or starting provider tooling.",
        capabilities=("Engineering-pattern review", "Cross-platform boundary review", "Plugin-risk triage"),
    ),
    SkillIntakeSpec(
        id="agent-skills-hub",
        label="Agent Skills Hub — Source Review Intake",
        owner_commander="Fang",
        category="automation",
        license="GitHub metadata reports MIT; registry, installer, package and each downstream skill require separate source review",
        source_url="https://github.com/agent-skills-hub/agent-skills-hub",
        review_commit="81857196f21e0b6b6b327e32dc21570d3b21b5b2",
        purpose="Reference for universal-registry and compatibility-boundary design, with no package installer or skill activation path.",
        capabilities=("Registry-boundary review", "Compatibility planning", "Installer-risk triage"),
        guardrails=(
            "Do not invoke npx, clawhub, an installer, a package manager, a registry API, a plugin, a provider or a downstream skill from this lane.",
        ),
    ),
    SkillIntakeSpec(
        id="desktop-agent-skills",
        label="desktop-agent — Source Review Intake",
        owner_commander="Nox",
        category="computer-use",
        license="GitHub metadata reports MIT; the requested skill-folder copy, desktop behaviour, dependencies and permissions still need individual review",
        source_url="https://github.com/patrickporto/desktop-agent",
        review_commit="c68e947448b17eddb0f9fd53513093523541862d",
        purpose="Reference for original desktop-agent safety boundary design; no repository clone, skill-folder copy or desktop capability is enabled.",
        capabilities=("Desktop-boundary review", "Skill-folder provenance plan", "Permission-model design"),
        guardrails=(
            "Do not clone this repository, copy its skill folder, load a skill file, start a desktop agent, or enable shell, file, browser, window, pointer, keyboard, screen, device or OS control from this lane.",
        ),
    ),
    SkillIntakeSpec(
        id="whimsical-strategies",
        label="Whimsical Strategies — Defensive Review Intake",
        owner_commander="Greed",
        category="security",
        license="GitHub metadata reports MIT; adversarial prompt material is restricted to defensive safety review and never auto-loaded",
        source_url="https://github.com/BayramAnnakov/whimsical-strategies-skill",
        review_commit="7df829a021595c58dad29ab3a9e7067b70d1221e",
        purpose="Reference-only defensive red-team methodology review for improving resistance, evaluation and escalation controls.",
        capabilities=("Defensive threat-model review", "Evaluation-plan design", "Escalation-boundary planning"),
        implementation_status="reference-only",
        guardrails=(
            "Do not generate or operationalise jailbreak/adversarial payloads, target third-party systems, weaken policy, override approvals or use this record for offensive security activity.",
        ),
    ),
    SkillIntakeSpec(
        id="evo-tournament-search-skills",
        label="Evo-Search / Tournament-Search — Source Review Intake",
        owner_commander="Ashborn",
        category="workflow",
        license="GitHub metadata reports MIT; algorithm, evaluation-data and any automated execution path need individual review",
        source_url="https://github.com/smkalami/skills",
        review_commit="1f180f3d0f2f8a726fcd01eac447b5deafe9449d",
        purpose="Reference for original bounded comparison and evaluation design without autonomous population search or tool execution.",
        capabilities=("Evaluation-pattern review", "Decision-comparison planning", "Bounded-experiment design"),
        guardrails=(
            "Do not spawn populations, mutate/crossover prompts or plans, run a tournament, use unreviewed data, write outputs, or autonomously choose/deploy a result from this lane.",
        ),
    ),
    SkillIntakeSpec(
        id="thesis-red-team-skills",
        label="Thesis Red-Team — Source Review Intake",
        owner_commander="Iron",
        category="research",
        license="No GitHub licence metadata detected (NOASSERTION); investment source reuse is prohibited pending an exact grant",
        source_url="https://github.com/latour-ai/skills",
        review_commit="955bf2144abbd2af64f722964a2e352d59a49ea5",
        purpose="Reference-only adversarial-assumption and decision-memo review pattern for user-provided, lawful analysis.",
        capabilities=("Assumption-review planning", "Pre-mortem design", "Decision-memo structure"),
        implementation_status="reference-only",
        guardrails=(
            "Do not treat outputs as investment advice, fetch market/account data, execute trades, contact a broker, or make financial decisions for a user from this lane.",
        ),
    ),
    SkillIntakeSpec(
        id="gh-evolve",
        label="gh-evolve — Source Review Intake",
        owner_commander="Igris",
        category="coding",
        license="No GitHub licence metadata detected (NOASSERTION); source reuse and GitHub workflow activation are prohibited pending an exact grant",
        source_url="https://github.com/kaiwong-sapiens/gh-evolve",
        review_commit="e0442ba83b556906f7ca6c54a71ac3713d19cee9",
        purpose="Reference for original issue/PR collaboration safety design, not an authorised GitHub graph, issue or pull-request actor.",
        capabilities=("Collaboration-graph review", "PR-safety planning", "State-provenance design"),
        implementation_status="reference-only",
        guardrails=(
            "Do not authenticate to GitHub, read/write issues or pull requests, create branches, mutate shared state, use repository tokens, or start evolutionary collaboration from this lane.",
        ),
    ),
    SkillIntakeSpec(
        id="skill-evolver",
        label="Skill-Evolver — Source Review Intake",
        owner_commander="Ashborn",
        category="workflow",
        license="GitHub metadata reports MIT; self-improvement, generated skills, validation routes and data retention require individual review",
        source_url="https://github.com/JinHo-von-Choi/skill-evolver",
        review_commit="5c4261faa24f681c2982350709447227eaec715f",
        purpose="Reference for human-reviewed failure-analysis and evaluation design; it cannot create, revise or activate a Jinwoo skill.",
        capabilities=("Failure-analysis review", "Validation-plan design", "Human-review checkpoints"),
        guardrails=(
            "Do not self-modify Jinwoo, generate/activate a skill, rewrite agent instructions, retain failure data, run training or deploy an evolved workflow from this lane.",
        ),
    ),
    SkillIntakeSpec(
        id="context-engineering-skills",
        label="Agent Skills for Context Engineering — Source Review Intake",
        owner_commander="Blades",
        category="workflow",
        license="GitHub metadata reports MIT; instructions, mental-state models and self-improvement loops require individual behavioural review",
        source_url="https://github.com/muratcankoylan/Agent-Skills-for-Context-Engineering",
        review_commit="6dbe1a1d868eab51a3bc9011b0f55e2891513e40",
        purpose="Reference for original context-quality, evaluation and bounded multi-agent reasoning design.",
        capabilities=("Context-quality review", "Evaluation-loop planning", "Reasoning-boundary design"),
    ),
    SkillIntakeSpec(
        id="deep-research-skill",
        label="Deep Research Skill — Source Review Intake",
        owner_commander="Tank",
        category="research",
        license="GitHub metadata reports MIT; research instructions, sources, browsing and evidence handling require individual review",
        source_url="https://github.com/ShadyUnderLight/deep-research-skill",
        review_commit="e7a8f35edc0364682939510822093250d18f0841",
        purpose="Reference for original evidence traceability, current-state verification and anti-evidence decision-memo design.",
        capabilities=("Evidence-plan review", "Traceability design", "Decision-memo structure"),
        guardrails=(
            "Do not resolve DNS, open a URL, launch a browser, fetch/search content, store source content, or present external claims as verified from this lane.",
        ),
    ),
    SkillIntakeSpec(
        id="cloud-skills-source-intake",
        label="Azure / Google Cloud Skills — Source Intake Pending",
        owner_commander="Fang",
        category="automation",
        license="Unverified — no exact Azure or Google Cloud skill repository/version was supplied or selected",
        source_url=None,
        review_commit=None,
        purpose="Records the requested cloud/devops capability area without guessing an official repository, package, provider or credential flow.",
        capabilities=("Cloud-source request", "Provider-boundary planning", "Credential-safety design"),
        guardrails=(
            "Do not infer an official source from a vendor name, install an SDK, authenticate an account, use a cloud credential, connect a workspace, provision infrastructure or call a cloud API from this lane.",
        ),
    ),
)


# Batch 12 is a bounded, metadata-only upgrade-discovery queue. The entries
# were selected to address documented local gaps (document handling, retrieval,
# provider boundaries, policy, quality, software supply-chain and observability)
# without adding an external runtime or changing the canonical controller.
BATCH_TWELVE_UPGRADE_INTAKES: tuple[SkillIntakeSpec, ...] = (
    SkillIntakeSpec(
        id="markitdown-upgrade-intake",
        label="MarkItDown — Document Intake Upgrade Review",
        owner_commander="Jima",
        category="coding",
        license="GitHub metadata reports MIT; document parsers, optional dependencies, file types and output handling require individual review",
        source_url="https://github.com/microsoft/markitdown",
        review_commit="20d06b6c8508f86bfae3252a979a661a14306287",
        purpose="Candidate for a future original, selected-workspace document-to-text planning lane with no current file read or conversion.",
        capabilities=("Document-boundary review", "Format-support planning", "Output-retention design"),
        guardrails=(
            "Do not install a converter, read/upload/download a document, run a parser, invoke OCR, retain extracted text, generate a file or access an unselected workspace from this lane.",
        ),
    ),
    SkillIntakeSpec(
        id="graphrag-upgrade-intake",
        label="GraphRAG — Knowledge Retrieval Upgrade Review",
        owner_commander="Blades",
        category="memory",
        license="GitHub metadata reports MIT; graph/index/model/provider/data-processing behaviour requires individual review",
        source_url="https://github.com/microsoft/graphrag",
        review_commit="f40e9a26ce62ba0b3fef8837d24aafdcc6e6c704",
        purpose="Candidate for a future original local knowledge-map design; no corpus, graph, embedding, index, model or retrieval process is created.",
        capabilities=("Knowledge-map planning", "Retrieval-boundary review", "Data-minimisation design"),
        guardrails=(
            "Do not ingest workspace data, build a graph/index, compute embeddings, download/use a model, call a provider, search a corpus or retain retrieval content from this lane.",
        ),
    ),
    SkillIntakeSpec(
        id="litellm-upgrade-intake",
        label="LiteLLM — Provider Gateway Upgrade Review",
        owner_commander="Fang",
        category="automation",
        license="No GitHub licence metadata detected (NOASSERTION) at review; source reuse and gateway activation are prohibited pending an exact compatible grant",
        source_url="https://github.com/BerriAI/litellm",
        review_commit="22cc97fe0a27367d19fdb03a16dbfd497f4360e8",
        purpose="Reference-only candidate for provider-routing boundary comparison; Jinwoo's explicit per-request provider consent remains canonical.",
        capabilities=("Provider-boundary review", "Routing-policy comparison", "Credential-safety design"),
        implementation_status="reference-only",
        guardrails=(
            "Do not install/start a gateway, use a provider key, send prompts/data, enable fallback/load balancing, log telemetry, proxy requests or replace Jinwoo's provider approval route.",
        ),
    ),
    SkillIntakeSpec(
        id="opa-upgrade-intake",
        label="Open Policy Agent — Policy Upgrade Review",
        owner_commander="Jinwoo",
        category="governance",
        license="GitHub metadata reports Apache-2.0; policy bundles, language/runtime, telemetry and decision semantics require individual review",
        source_url="https://github.com/open-policy-agent/opa",
        review_commit="25a1d928d6ff43000c428ccfc1970d54afb5494b",
        purpose="Candidate for future policy-rule comparison; it cannot replace Jinwoo's current policy classifier or approval ownership.",
        capabilities=("Policy-rule comparison", "Decision-audit design", "Approval-model review"),
        guardrails=(
            "Do not install/run a policy engine, load a policy bundle, fetch remote policy, alter a policy decision, bypass approval, or replace Jinwoo's canonical controller from this lane.",
        ),
    ),
    SkillIntakeSpec(
        id="lancedb-upgrade-intake",
        label="LanceDB — Local Retrieval Upgrade Review",
        owner_commander="Jinwoo",
        category="memory",
        license="GitHub metadata reports Apache-2.0; local data layout, embeddings, extensions and retention/deletion behaviour require individual review",
        source_url="https://github.com/lancedb/lancedb",
        review_commit="2779b75d0d0252a324bc39ab73c9132d3b212484",
        purpose="Candidate for a future opt-in local retrieval design; SQLite remains authoritative and no vector database is created now.",
        capabilities=("Local-retrieval planning", "Retention-model review", "Memory-boundary design"),
        guardrails=(
            "Do not install/create a database, ingest/index files or memories, compute embeddings, download a model, read an unselected workspace, or change Memory Vault retention from this lane.",
        ),
    ),
    SkillIntakeSpec(
        id="promptfoo-upgrade-intake",
        label="Promptfoo — Evaluation Upgrade Review",
        owner_commander="Greed",
        category="security",
        license="GitHub metadata reports MIT; evaluation targets, red-team behaviour, provider calls, plugins and report retention require individual review",
        source_url="https://github.com/promptfoo/promptfoo",
        review_commit="48a71cd0163b01ba8efb2954eb0165dd810a6c6e",
        purpose="Candidate for original local evaluation-plan design with defensive scope only; no target, test case, red team or report is run.",
        capabilities=("Evaluation-plan review", "Defensive test design", "Evidence-retention planning"),
        guardrails=(
            "Do not install/run an evaluator, send a prompt to a provider, target a third-party system, generate adversarial payloads, scan for vulnerabilities, use a plugin or write a report from this lane.",
        ),
    ),
    SkillIntakeSpec(
        id="ruff-upgrade-intake",
        label="Ruff — Python Quality Upgrade Review",
        owner_commander="Shadow",
        category="coding",
        license="GitHub metadata reports MIT; binary provenance, rule configuration, formatting effects and workspace-write policy require individual review",
        source_url="https://github.com/astral-sh/ruff",
        review_commit="849bc61d7aea53bf7ded094973b176eb607fe3e5",
        purpose="Candidate for a future local lint/format review plan; no binary is installed and no source file is read, rewritten or formatted.",
        capabilities=("Lint-policy planning", "Formatting-impact review", "Quality-gate design"),
        guardrails=(
            "Do not install/run a binary, read or scan workspace code, apply formatting/fixes, modify configuration, write a patch or execute an automated quality command from this lane.",
        ),
    ),
    SkillIntakeSpec(
        id="syft-upgrade-intake",
        label="Syft — SBOM Upgrade Review",
        owner_commander="Greed",
        category="security",
        license="GitHub metadata reports Apache-2.0; scanner/binary provenance, filesystem/container scope and SBOM retention require individual review",
        source_url="https://github.com/anchore/syft",
        review_commit="77031752faf6810edf6d57c8ba798408796ea283",
        purpose="Candidate for an approved selected-workspace SBOM preflight design; no filesystem/container scan or SBOM creation occurs.",
        capabilities=("SBOM-boundary review", "Supply-chain planning", "Artifact-retention design"),
        guardrails=(
            "Do not install/run a scanner, inspect a filesystem/container/image, download a package database, generate/upload an SBOM, expose dependency inventory or read an unselected workspace from this lane.",
        ),
    ),
    SkillIntakeSpec(
        id="trivy-upgrade-intake",
        label="Trivy — Vulnerability Review Upgrade Intake",
        owner_commander="Greed",
        category="security",
        license="GitHub metadata reports Apache-2.0; vulnerability databases, scan targets, cloud/container integration and finding retention require individual review",
        source_url="https://github.com/aquasecurity/trivy",
        review_commit="dcfb99218f072d1f54576af3c0b4f6fc8fe843f3",
        purpose="Candidate for a future authorised vulnerability/misconfiguration scan plan; no scanner, database, target or finding is used now.",
        capabilities=("Vulnerability-plan review", "Scope-consent design", "Finding-redaction planning"),
        guardrails=(
            "Do not install/run a scanner, download a vulnerability database, read a repository/container/cloud target, scan secrets, authenticate a cloud account, expose findings or remediate anything from this lane.",
        ),
    ),
    SkillIntakeSpec(
        id="opentelemetry-upgrade-intake",
        label="OpenTelemetry Python — Local Observability Upgrade Review",
        owner_commander="Nox",
        category="governance",
        license="GitHub metadata reports Apache-2.0; instrumentation, exporters, collectors, telemetry data and network destinations require individual review",
        source_url="https://github.com/open-telemetry/opentelemetry-python",
        review_commit="eeeaa8f925c2b4430db3c08ef9912249138d7c00",
        purpose="Candidate for a future local-only observability design; no instrumentation, trace collection, exporter, collector or network telemetry is enabled.",
        capabilities=("Local-observability planning", "Telemetry-minimisation review", "Audit-vs-trace boundary design"),
        guardrails=(
            "Do not install/instrument an SDK, collect traces/metrics/logs, start a collector, configure an exporter, transmit telemetry, retain sensitive spans or alter the redacted audit trail from this lane.",
        ),
    ),
)


def source_intake_guardrails(spec: SkillIntakeSpec) -> tuple[str, ...]:
    """Join mandatory controlled-source boundaries with source-specific restrictions."""

    return _SOURCE_REVIEW_GUARDRAILS + spec.guardrails
