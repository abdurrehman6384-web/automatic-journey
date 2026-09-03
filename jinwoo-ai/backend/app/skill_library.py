"""Strict local loader for Jinwoo-authored portable skills and agents.

The loader reads only the checked-in ``skills/`` and ``agents/`` directories.
It never opens an upstream repository, a user home skill path, a workspace, or
an external runtime. ``SOURCES.json`` is provenance metadata, not a source
payload or a licence grant.
"""

from __future__ import annotations

from dataclasses import dataclass
from hashlib import sha256
import json
import re
from pathlib import Path

from .schemas import (
    NativeAgentSummary,
    NativeSkillDetail,
    NativeSkillSummary,
    SkillLibrary,
    SkillResolution,
    SkillSourceProvenance,
)


_PROJECT_ROOT = Path(__file__).resolve().parents[2]
_SKILLS_ROOT = _PROJECT_ROOT / "skills"
_AGENTS_ROOT = _PROJECT_ROOT / "agents"
_SOURCES_PATH = _SKILLS_ROOT / "SOURCES.json"
_MAX_SKILL_BYTES = 16_000
_MAX_AGENT_BYTES = 12_000
_MAX_SOURCES_BYTES = 128_000
_SAFE_ID = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
_SAFE_ROUTING_TERM = re.compile(r"^[a-z0-9]+(?:[ -][a-z0-9]+)*$")
_SAFE_SHA = re.compile(r"^[0-9a-f]{40}$")
_REQUIRED_SKILL_KEYS = {
    "id", "name", "description", "category", "activation_mode", "requires_approval",
    "tags", "routing_terms", "source_refs", "jinwoo_native",
}
_REQUIRED_AGENT_KEYS = {"id", "name", "description", "role", "skill_scope", "jinwoo_native"}
_SOURCE_REQUIRED_KEYS = {
    "id", "requested_repository", "source_url", "default_branch", "review_commit", "license_signal",
    "review_scope", "native_skill_ids", "decision",
}
_SOURCE_ALLOWED_KEYS = _SOURCE_REQUIRED_KEYS | {"resolved_repository"}
_SAFE_REPOSITORY = re.compile(r"^[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+$")
_SAFE_BRANCH = re.compile(r"^[A-Za-z0-9._/-]{1,120}$")
# A deliberate fixed inventory stops an arbitrary source record from becoming a
# native capability merely because it is placed in SOURCES.json.
_EXPECTED_SOURCE_REPOSITORIES = {
    "luo-kai-catalogue": "luokai0/ai-agent-skills-by-luo-kai",
    "antigravity-awesome-skills": "sickn33/antigravity-awesome-skills",
    "mouad-skills": "mouadja02/skills",
    "theneo-awesome-skills": "theneoai/awesome-skills",
    "claude-skills-collection": "alirezarezvani/claude-skills",
    "agent-skills-hub": "agent-skills-hub/agent-skills-hub",
    "voltagent-awesome-agent-skills": "VoltAgent/awesome-agent-skills",
    "desktop-agent": "patrickporto/desktop-agent",
    "one-m-one-ai-computer-use": "1m1ai/computer-use",
    "acu-computer-use-index": "trycua/acu",
    "barehands": "jaredrhod/barehands",
    "gesture-controlled-virtual-mouse": "Viral-Doshi/Gesture-Controlled-Virtual-Mouse",
    "robotics-agent-skills": "arpitg1304/robotics-agent-skills",
    "glm-skills": "zai-org/GLM-skills",
    "grok-custom-skills": "Stijnman/grok-custom-skills",
    "ai-agents-public": "vasilyu1983/AI-Agents-public",
    "seedance-skills": "LeoYeAI/seedance-skills",
    "five-hundred-ai-agent-projects": "ashishpatel26/500-AI-Agents-Projects",
    "awesome-llm-apps": "Shubhamsaboo/awesome-llm-apps",
    "github-awesome-copilot": "github/awesome-copilot",
}
_REQUIRED_SKILL_HEADINGS = ("## Purpose", "## Procedure", "## Output", "## Safety boundary")


class SkillLibraryError(ValueError):
    """Raised when a local native skill/agent/provenance record is invalid."""


@dataclass(frozen=True)
class _LoadedSkill:
    summary: NativeSkillSummary
    instructions: str
    routing_terms: tuple[str, ...]


@dataclass(frozen=True)
class _LoadedAgent:
    summary: NativeAgentSummary


def _read_local_text(path: Path, maximum_bytes: int) -> str:
    """Read one regular local library file with conservative size/path checks."""

    try:
        resolved = path.resolve(strict=True)
    except OSError as error:
        raise SkillLibraryError(f"Missing native library file: {path.name}") from error
    if resolved != path.absolute() or path.is_symlink() or not path.is_file():
        raise SkillLibraryError(f"Native library file must be a regular in-tree file: {path.name}")
    if path.stat().st_size > maximum_bytes:
        raise SkillLibraryError(f"Native library file exceeds its size limit: {path.name}")
    try:
        return path.read_text(encoding="utf-8")
    except (OSError, UnicodeError) as error:
        raise SkillLibraryError(f"Cannot read native library file: {path.name}") from error


def _frontmatter(raw: str, required_keys: set[str], label: str) -> tuple[dict[str, str], str]:
    """Parse the small, intentionally non-general YAML frontmatter subset we own."""

    if not raw.startswith("---\n"):
        raise SkillLibraryError(f"{label} must begin with native frontmatter")
    marker = raw.find("\n---\n", 4)
    if marker < 0:
        raise SkillLibraryError(f"{label} has no closing frontmatter marker")
    values: dict[str, str] = {}
    for line in raw[4:marker].splitlines():
        if not line or line.startswith("#"):
            continue
        if line[:1].isspace() or ":" not in line:
            raise SkillLibraryError(f"{label} has unsupported frontmatter")
        key, value = line.split(":", 1)
        key = key.strip()
        value = value.strip()
        if key not in required_keys or key in values or not value:
            raise SkillLibraryError(f"{label} has invalid frontmatter key/value")
        values[key] = value
    if set(values) != required_keys:
        missing = sorted(required_keys - set(values))
        raise SkillLibraryError(f"{label} is missing required fields: {', '.join(missing)}")
    body = raw[marker + len("\n---\n"):]
    return values, body


def _native_boolean(value: str, field: str, label: str) -> bool:
    if value == "true":
        return True
    if value == "false":
        return False
    raise SkillLibraryError(f"{label} has invalid {field}")


def _csv(value: str, field: str, label: str) -> tuple[str, ...]:
    values = tuple(part.strip() for part in value.split(",") if part.strip())
    if not values or len(values) != len(set(values)):
        raise SkillLibraryError(f"{label} has invalid {field}")
    return values


def _relative_skill_path(path: Path, skill_id: str) -> str:
    try:
        relative = path.relative_to(_SKILLS_ROOT)
    except ValueError as error:
        raise SkillLibraryError("Native skill is outside the skills directory") from error
    if len(relative.parts) != 3 or relative.parts[-1] != "SKILL.md" or relative.parts[-2] != skill_id:
        raise SkillLibraryError(f"Native skill path is not canonical: {relative}")
    return relative.as_posix()


def _load_skill(path: Path) -> _LoadedSkill:
    raw = _read_local_text(path, _MAX_SKILL_BYTES)
    frontmatter, body = _frontmatter(raw, _REQUIRED_SKILL_KEYS, path.name)
    skill_id = frontmatter["id"]
    if not _SAFE_ID.fullmatch(skill_id) or not _native_boolean(frontmatter["jinwoo_native"], "jinwoo_native", path.name):
        raise SkillLibraryError(f"{path.name} is not a Jinwoo-owned skill")
    if frontmatter["activation_mode"] != "planning-only":
        raise SkillLibraryError(f"{path.name} attempts to expose a non-planning activation mode")
    if not all(heading in body for heading in _REQUIRED_SKILL_HEADINGS):
        raise SkillLibraryError(f"{path.name} is missing the required native safety sections")
    tags = _csv(frontmatter["tags"], "tags", path.name)
    routing_terms = _csv(frontmatter["routing_terms"], "routing_terms", path.name)
    source_refs = _csv(frontmatter["source_refs"], "source_refs", path.name)
    if not all(_SAFE_ID.fullmatch(item) for item in (*tags, *source_refs)) or not all(
        _SAFE_ROUTING_TERM.fullmatch(item) for item in routing_terms
    ):
        raise SkillLibraryError(f"{path.name} has unsafe identifiers")
    return _LoadedSkill(
        summary=NativeSkillSummary(
            id=skill_id,
            name=frontmatter["name"],
            description=frontmatter["description"],
            category=frontmatter["category"],
            activation_mode="planning-only",
            requires_approval=_native_boolean(frontmatter["requires_approval"], "requires_approval", path.name),
            tags=list(tags),
            source_refs=list(source_refs),
            skill_path=_relative_skill_path(path, skill_id),
            content_sha256=sha256(raw.encode("utf-8")).hexdigest(),
            jinwoo_native=True,
        ),
        instructions=raw,
        routing_terms=routing_terms,
    )


def _load_agent(path: Path) -> _LoadedAgent:
    raw = _read_local_text(path, _MAX_AGENT_BYTES)
    frontmatter, _body = _frontmatter(raw, _REQUIRED_AGENT_KEYS, path.name)
    agent_id = frontmatter["id"]
    try:
        relative = path.relative_to(_AGENTS_ROOT)
    except ValueError as error:
        raise SkillLibraryError("Native agent is outside the agents directory") from error
    if (
        not _SAFE_ID.fullmatch(agent_id)
        or len(relative.parts) != 2
        or relative.parts[-1] != "AGENT.md"
        or relative.parts[-2] != agent_id
        or not _native_boolean(frontmatter["jinwoo_native"], "jinwoo_native", path.name)
        or frontmatter["role"] != "canonical-orchestrator"
        or frontmatter["skill_scope"] != "all-native-skills"
    ):
        raise SkillLibraryError(f"{path.name} is not a canonical native agent manifest")
    return _LoadedAgent(
        summary=NativeAgentSummary(
            id=agent_id,
            name=frontmatter["name"],
            description=frontmatter["description"],
            role="canonical-orchestrator",
            skill_scope="all-native-skills",
            agent_path=relative.as_posix(),
            jinwoo_native=True,
        )
    )


def _load_sources() -> tuple[SkillSourceProvenance, ...]:
    raw = _read_local_text(_SOURCES_PATH, _MAX_SOURCES_BYTES)
    try:
        payload = json.loads(raw)
    except json.JSONDecodeError as error:
        raise SkillLibraryError("SOURCES.json is not valid JSON") from error
    if (
        not isinstance(payload, dict)
        or set(payload) != {"schema_version", "sources"}
        or payload.get("schema_version") != 1
        or not isinstance(payload.get("sources"), list)
    ):
        raise SkillLibraryError("SOURCES.json does not match the native provenance schema")
    sources: list[SkillSourceProvenance] = []
    for item in payload["sources"]:
        if (
            not isinstance(item, dict)
            or not _SOURCE_REQUIRED_KEYS <= set(item)
            or not set(item) <= _SOURCE_ALLOWED_KEYS
        ):
            raise SkillLibraryError("SOURCES.json contains unsupported source fields")
        try:
            source = SkillSourceProvenance.model_validate(item)
        except (TypeError, ValueError) as error:
            raise SkillLibraryError("SOURCES.json contains an invalid source record") from error
        if (
            not _SAFE_ID.fullmatch(source.id)
            or not _SAFE_REPOSITORY.fullmatch(source.requested_repository)
            or source.resolved_repository is not None and not _SAFE_REPOSITORY.fullmatch(source.resolved_repository)
            or not _SAFE_BRANCH.fullmatch(source.default_branch)
            or not _SAFE_SHA.fullmatch(source.review_commit)
            or source.source_url != f"https://github.com/{source.requested_repository}"
            or not all(_SAFE_ID.fullmatch(skill_id) for skill_id in source.native_skill_ids)
            or not all(value.strip() for value in (source.license_signal, source.review_scope, source.decision))
            or any(len(value) > 1_200 for value in (source.license_signal, source.review_scope, source.decision))
        ):
            raise SkillLibraryError(f"Invalid native provenance record: {source.id}")
        sources.append(source)
    source_ids = [source.id for source in sources]
    if len(sources) != 20 or len(source_ids) != len(set(source_ids)):
        raise SkillLibraryError("The requested source provenance inventory is incomplete or duplicated")
    if {source.id: source.requested_repository for source in sources} != _EXPECTED_SOURCE_REPOSITORIES:
        raise SkillLibraryError("The source provenance inventory does not match the approved requested repositories")
    return tuple(sorted(sources, key=lambda source: source.id))


def _summary_with_availability(skill: _LoadedSkill, disabled_skill_ids: frozenset[str]) -> NativeSkillSummary:
    return skill.summary.model_copy(
        update={"availability": "disabled" if skill.summary.id in disabled_skill_ids else "enabled"}
    )


class NativeSkillLibrary:
    """Discover only Jinwoo-owned skills and the canonical orchestration agent."""

    def _load_all(self) -> tuple[dict[str, _LoadedSkill], dict[str, _LoadedAgent], tuple[SkillSourceProvenance, ...]]:
        if not _SKILLS_ROOT.is_dir() or not _AGENTS_ROOT.is_dir():
            raise SkillLibraryError("Native skills or agents directory is missing")
        canonical_skill_paths = sorted(_SKILLS_ROOT.glob("*/*/SKILL.md"))
        canonical_agent_paths = sorted(_AGENTS_ROOT.glob("*/AGENT.md"))
        if set(canonical_skill_paths) != set(_SKILLS_ROOT.rglob("SKILL.md")):
            raise SkillLibraryError("Native skills directory contains a non-canonical SKILL.md payload")
        if set(canonical_agent_paths) != set(_AGENTS_ROOT.rglob("AGENT.md")):
            raise SkillLibraryError("Native agents directory contains a non-canonical AGENT.md payload")
        skills = [_load_skill(path) for path in canonical_skill_paths]
        agents = [_load_agent(path) for path in canonical_agent_paths]
        skill_by_id = {skill.summary.id: skill for skill in skills}
        agent_by_id = {agent.summary.id: agent for agent in agents}
        if len(skills) != len(skill_by_id) or len(skills) != 15:
            raise SkillLibraryError("Native skill inventory must contain 15 unique skills")
        if set(agent_by_id) != {"jinwoo-master-orchestrator"}:
            raise SkillLibraryError("Native agent inventory must contain the canonical master orchestrator")
        sources = _load_sources()
        source_by_id = {source.id: source for source in sources}
        observed_source_refs = {source_ref for skill in skills for source_ref in skill.summary.source_refs}
        if observed_source_refs != set(source_by_id):
            raise SkillLibraryError("Every requested source must map to at least one native skill")
        for source in sources:
            declared = set(source.native_skill_ids)
            observed = {
                skill_id for skill_id, skill in skill_by_id.items()
                if source.id in skill.summary.source_refs
            }
            if not declared or not declared <= set(skill_by_id) or declared != observed:
                raise SkillLibraryError(f"Source/skill provenance mapping disagrees: {source.id}")
        return skill_by_id, agent_by_id, sources

    def library(self, disabled_skill_ids: frozenset[str] = frozenset()) -> SkillLibrary:
        skills, agents, sources = self._load_all()
        return SkillLibrary(
            skills=[_summary_with_availability(item, disabled_skill_ids) for item in sorted(skills.values(), key=lambda item: item.summary.id)],
            agents=[item.summary for item in sorted(agents.values(), key=lambda item: item.summary.id)],
            sources=list(sources),
            all_sources_covered=True,
            external_runtime_invoked=False,
            detail=(
                "Jinwoo-owned portable skill instructions and the canonical master orchestrator are discoverable locally. "
                "No upstream payload, external runtime, provider, browser, device, process or worker is opened."
            ),
        )

    def skill(self, skill_id: str, disabled_skill_ids: frozenset[str] = frozenset()) -> NativeSkillDetail:
        skills, _agents, _sources = self._load_all()
        skill = skills.get(skill_id)
        if skill is None:
            raise SkillLibraryError("Unknown native skill")
        return NativeSkillDetail(**_summary_with_availability(skill, disabled_skill_ids).model_dump(), instructions=skill.instructions)

    def agent(self, agent_id: str) -> NativeAgentSummary:
        _skills, agents, _sources = self._load_all()
        agent = agents.get(agent_id)
        if agent is None:
            raise SkillLibraryError("Unknown native agent")
        return agent.summary

    def resolve(
        self,
        objective: str,
        skill_ids: list[str],
        max_results: int,
        disabled_skill_ids: frozenset[str] = frozenset(),
    ) -> SkillResolution:
        skills, _agents, _sources = self._load_all()
        available_skills = {skill_id: skill for skill_id, skill in skills.items() if skill_id not in disabled_skill_ids}
        if not available_skills:
            raise SkillLibraryError("All native skills are disabled; enable at least one planning skill before resolving a plan")
        if skill_ids:
            if len(skill_ids) != len(set(skill_ids)):
                raise SkillLibraryError("Select each native skill at most once")
            selected = []
            for skill_id in skill_ids:
                if skill_id in disabled_skill_ids:
                    raise SkillLibraryError("A disabled native skill cannot be selected; enable it first")
                skill = available_skills.get(skill_id)
                if skill is None:
                    raise SkillLibraryError("Unknown native skill")
                selected.append(skill)
            basis = "Explicit native skill selection."
        else:
            terms = set(re.findall(r"[a-z0-9]+", objective.casefold()))
            scored: list[tuple[int, _LoadedSkill]] = []
            for skill in available_skills.values():
                searchable = (*skill.routing_terms, *skill.summary.tags, skill.summary.id, skill.summary.category)
                score = sum(
                    3
                    for phrase in searchable
                    if (phrase_terms := set(re.findall(r"[a-z0-9]+", phrase.casefold()))) and phrase_terms <= terms
                )
                score += sum(1 for token in re.findall(r"[a-z0-9]+", skill.summary.name.casefold()) if token in terms)
                scored.append((score, skill))
            ranked = sorted(scored, key=lambda item: (-item[0], item[1].summary.id))
            selected = [skill for score, skill in ranked if score > 0][:max_results]
            if not selected:
                fallback_ids = ("agent-governance", "approval-and-permission-boundary", "evidence-before-completion")
                selected = [available_skills[skill_id] for skill_id in fallback_ids if skill_id in available_skills][:max_results]
                if not selected:
                    selected = [available_skills[skill_id] for skill_id in sorted(available_skills)[:max_results]]
                    basis = "No direct keyword match; selected the remaining enabled native planning baseline."
                else:
                    basis = "No direct keyword match; selected the enabled native governance, approval and evidence baseline."
            else:
                basis = "Matched the objective against locally authored routing terms and tags."
        return SkillResolution(
            objective=objective,
            selected_skill_ids=[skill.summary.id for skill in selected],
            skills=[skill.summary for skill in selected],
            selection_basis=basis,
            external_runtime_invoked=False,
            guardrails=[
                "Selection reads only Jinwoo-owned skills inside this repository.",
                "A selected skill is planning-only and does not start a model, tool, process, provider or external agent.",
                "Impactful actions still need separate policy classification and explicit user approval.",
            ],
        )


skill_library = NativeSkillLibrary()
