import { useEffect, useMemo, useState } from 'react'
import type { FormEvent } from 'react'

export type NativeSkillAvailability = 'enabled' | 'disabled'

export interface NativeSkillSummary {
  id: string
  name: string
  description: string
  category: string
  activation_mode: 'planning-only'
  requires_approval: boolean
  tags: string[]
  source_refs: string[]
  skill_path: string
  content_sha256: string
  availability: NativeSkillAvailability
  jinwoo_native: boolean
}

export interface NativeSkillDetail extends NativeSkillSummary {
  instructions: string
}

export interface NativeAgentSummary {
  id: string
  name: string
  description: string
  role: 'canonical-orchestrator'
  skill_scope: 'all-native-skills'
  agent_path: string
  jinwoo_native: boolean
}

export interface NativeSkillSource {
  id: string
  requested_repository: string
  resolved_repository?: string | null
  source_url: string
  default_branch: string
  review_commit: string
  license_signal: string
  review_scope: string
  native_skill_ids: string[]
  decision: string
}

export interface NativeSkillLibraryData {
  skills: NativeSkillSummary[]
  agents: NativeAgentSummary[]
  sources: NativeSkillSource[]
  all_sources_covered: boolean
  external_runtime_invoked: boolean
  detail: string
}

export interface NativeSkillPlanStage {
  id: 'planner' | 'executor' | 'verifier'
  label: string
  skill_ids: string[]
  detail: string
  requires_approval: boolean
}

export interface NativeSkillPlan {
  id: string
  objective: string
  agent_id: 'jinwoo-master-orchestrator'
  state: 'planned' | 'paused' | 'terminated'
  selected_skill_ids: string[]
  policy_outcome: 'safe-plan' | 'approval-required'
  requires_approval: boolean
  instruction_overlay?: string | null
  runtime_workers_started: number
  external_runtime_invoked: boolean
  stages: NativeSkillPlanStage[]
  guardrails: string[]
  created_at: string
  updated_at: string
}

interface NativeSkillLibraryPanelProps {
  library: NativeSkillLibraryData | null
  plans: NativeSkillPlan[]
  detail: NativeSkillDetail | null
  busy: boolean
  onRefresh: () => Promise<void>
  onInspect: (skillId: string) => Promise<void>
  onSetAvailability: (skillId: string, enabled: boolean) => Promise<boolean>
  onCreatePlan: (objective: string, skillIds: string[], controllerInstruction?: string) => Promise<boolean>
  onDirective: (
    planId: string,
    action: 'pause' | 'resume' | 'terminate' | 'rewrite-instructions',
    controllerInstruction?: string,
  ) => Promise<boolean>
}

const humanize = (value: string) => value.replaceAll('-', ' ')

export function NativeSkillLibraryPanel({
  library,
  plans,
  detail,
  busy,
  onRefresh,
  onInspect,
  onSetAvailability,
  onCreatePlan,
  onDirective,
}: NativeSkillLibraryPanelProps) {
  const [objective, setObjective] = useState('Plan a privacy-aware multimodal document review with acceptance evidence.')
  const [selectedSkillIds, setSelectedSkillIds] = useState<string[]>([])
  const [controllerInstruction, setControllerInstruction] = useState('')
  const [directiveText, setDirectiveText] = useState('')
  const [formError, setFormError] = useState('')

  const enabledSkills = useMemo(() => library?.skills.filter((skill) => skill.availability === 'enabled') ?? [], [library])
  const latestPlan = plans[0]

  useEffect(() => {
    setSelectedSkillIds((current) => current.filter((id) => enabledSkills.some((skill) => skill.id === id)))
  }, [enabledSkills])

  const toggleSelectedSkill = (skill: NativeSkillSummary) => {
    if (skill.availability === 'disabled') return
    setSelectedSkillIds((current) => current.includes(skill.id)
      ? current.filter((id) => id !== skill.id)
      : current.length < 5 ? [...current, skill.id] : current)
  }

  const createPlan = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault()
    const cleanObjective = objective.trim()
    if (cleanObjective.length < 2) {
      setFormError('Describe an outcome before the Master Orchestrator prepares a plan.')
      return
    }
    if (!enabledSkills.length) {
      setFormError('Enable at least one native planning skill before creating a plan.')
      return
    }
    setFormError('')
    const created = await onCreatePlan(cleanObjective, selectedSkillIds, controllerInstruction.trim() || undefined)
    if (created) setDirectiveText('')
  }

  const applyDirective = async (action: 'pause' | 'resume' | 'terminate' | 'rewrite-instructions') => {
    if (!latestPlan) return
    if (action === 'rewrite-instructions' && directiveText.trim().length < 2) {
      setFormError('Write a small session-local overlay before revising the plan.')
      return
    }
    setFormError('')
    const applied = await onDirective(latestPlan.id, action, action === 'rewrite-instructions' ? directiveText.trim() : undefined)
    if (applied && action === 'rewrite-instructions') setDirectiveText('')
  }

  return (
    <section className="native-skills" aria-labelledby="native-skills-title">
      <header className="native-skills__hero panel">
        <div>
          <p className="eyebrow"><span className="signal-dot" /> BATCH 13 · NATIVE SKILL LIBRARY</p>
          <h1 id="native-skills-title">Skills with <em>boundaries</em>.</h1>
          <p>
            Jinwoo-owned portable <code>SKILL.md</code> instructions are selected locally by the Master Orchestrator.
            They are original planning aids, not imported agents, installers, or external runtimes.
          </p>
          <div className="native-skills__metrics">
            <span><b>{library?.skills.length ?? '—'}</b> native skills</span>
            <span><b>{enabledSkills.length || (library ? 0 : '—')}</b> selectable</span>
            <span><b>{library?.sources.length ?? '—'}</b> source records</span>
            <span><b>0</b> workers started</span>
          </div>
        </div>
        <div className="native-skills__hero-lock">
          <span>⌬</span>
          <strong>{library?.all_sources_covered ? 'SOURCE COVERAGE VERIFIED' : 'LOCAL LIBRARY OFFLINE'}</strong>
          <small>Source metadata is traceable. No upstream payload is loaded.</small>
          <button className="button button--ghost" type="button" disabled={busy} onClick={() => { void onRefresh() }}>Refresh inventory</button>
        </div>
      </header>

      {!library ? (
        <section className="panel native-skills__offline">
          <span>◌</span>
          <div>
            <p className="eyebrow">LOCAL API REQUIRED</p>
            <h2>Native inventory is waiting for Jinwoo.</h2>
            <p>Start the local backend to inspect its skill documents, source metadata, availability controls, and visible plan state. No fallback payload is embedded in the browser.</p>
          </div>
        </section>
      ) : (
        <>
          <div className="native-skills__grid">
            <section className="panel native-skills__catalogue">
              <div className="panel-heading">
                <div>
                  <p className="eyebrow">DISCOVERABLE LOCAL CATALOGUE</p>
                  <h2>Choose a small, relevant capability set.</h2>
                </div>
                <span className="subtle-badge">MAX 5 / PLAN</span>
              </div>
              <p className="panel-hint">Selection only affects a local planning proposal. Disable a card to remove it from automatic and explicit selection until you re-enable it.</p>
              <div className="native-skills__skill-grid">
                {library.skills.map((skill) => {
                  const isSelected = selectedSkillIds.includes(skill.id)
                  const isDisabled = skill.availability === 'disabled'
                  return (
                    <article className={`native-skill-card ${isSelected ? 'native-skill-card--selected' : ''} ${isDisabled ? 'native-skill-card--disabled' : ''}`} key={skill.id}>
                      <div className="native-skill-card__head">
                        <span>{skill.category}</span>
                        <em>{isDisabled ? 'selection off' : skill.requires_approval ? 'approval edge' : 'plan ready'}</em>
                      </div>
                      <h3>{skill.name}</h3>
                      <p>{skill.description}</p>
                      <div className="native-skill-card__tags">{skill.tags.map((tag) => <small key={tag}>{tag}</small>)}</div>
                      <div className="native-skill-card__actions">
                        <button className="button button--ghost" type="button" disabled={isDisabled || busy} onClick={() => toggleSelectedSkill(skill)}>
                          {isSelected ? 'Remove' : 'Add to plan'}
                        </button>
                        <button className="text-button" type="button" disabled={busy} onClick={() => { void onInspect(skill.id) }}>Read SKILL.md</button>
                        <button className="text-button" type="button" disabled={busy} onClick={() => { void onSetAvailability(skill.id, isDisabled) }}>
                          {isDisabled ? 'Enable selection' : 'Disable selection'}
                        </button>
                      </div>
                    </article>
                  )
                })}
              </div>
            </section>

            <form className="panel native-skills__planner" onSubmit={createPlan}>
              <div className="panel-heading">
                <div>
                  <p className="eyebrow">JINWOO MASTER ORCHESTRATOR</p>
                  <h2>Prepare a visible skill plan.</h2>
                </div>
                <span className="subtle-badge">NO EXECUTION</span>
              </div>
              <p className="native-skills__agent"><b>{library.agents[0]?.name ?? 'Canonical agent'}</b> · Planner → Executor → Verifier roles exist only as a reviewable plan.</p>
              <label htmlFor="native-skill-objective">Outcome</label>
              <textarea id="native-skill-objective" value={objective} maxLength={4000} onChange={(event) => setObjective(event.target.value)} />
              <label htmlFor="native-skill-overlay">Optional controller overlay <small>session-local; never writes a SKILL.md</small></label>
              <textarea id="native-skill-overlay" value={controllerInstruction} maxLength={2000} onChange={(event) => setControllerInstruction(event.target.value)} placeholder="Example: keep the draft text-only and make open questions explicit." />
              <p className="native-skills__selected"><b>{selectedSkillIds.length ? selectedSkillIds.length : 'Auto'}</b> {selectedSkillIds.length ? `selected: ${selectedSkillIds.join(', ')}` : 'enabled skills will be matched deterministically'}</p>
              {formError && <p className="form-error" role="alert">{formError}</p>}
              <button className="button" type="submit" disabled={busy}>{busy ? 'Preparing plan…' : 'Prepare safe skill plan'} <span>↗</span></button>
              <p className="panel-hint">No model, process, provider, browser, device, scanner, file action, or external agent is started from this panel.</p>
            </form>
          </div>

          {detail && (
            <section className="panel native-skills__detail" aria-live="polite">
              <div className="panel-heading">
                <div>
                  <p className="eyebrow">PORTABLE INSTRUCTION PREVIEW · {detail.skill_path}</p>
                  <h2>{detail.name}</h2>
                </div>
                <div className="native-skills__detail-badges"><span className="subtle-badge">{detail.availability}</span><span className="subtle-badge">SHA {detail.content_sha256.slice(0, 10)}</span></div>
              </div>
              <pre>{detail.instructions}</pre>
            </section>
          )}

          <section className="panel native-skills__plan" aria-live="polite">
            <div className="panel-heading">
              <div>
                <p className="eyebrow">MASTER ORCHESTRATOR · LOCAL PLAN STATE</p>
                <h2>{latestPlan ? humanize(latestPlan.state) : 'No skill plan prepared yet.'}</h2>
              </div>
              {latestPlan && <div className="native-skills__detail-badges"><span className="subtle-badge">{humanize(latestPlan.policy_outcome)}</span><span className="subtle-badge">0 workers started</span></div>}
            </div>
            {latestPlan ? (
              <>
                <p className="native-skills__plan-objective">“{latestPlan.objective}”</p>
                <div className="native-skills__plan-skills">{latestPlan.selected_skill_ids.map((id) => <span key={id}>{id}</span>)}</div>
                <ol className="native-skills__stages">
                  {latestPlan.stages.map((stage, index) => (
                    <li key={stage.id}>
                      <span>{String(index + 1).padStart(2, '0')}</span>
                      <div><strong>{stage.label}</strong><p>{stage.detail}</p><small>{stage.skill_ids.join(' · ')}</small></div>
                      {stage.requires_approval && <em>approval edge</em>}
                    </li>
                  ))}
                </ol>
                <div className="native-skills__directive">
                  <div>
                    <p className="eyebrow">SESSION-LOCAL CONTROLLER DIRECTIVE</p>
                    <textarea value={directiveText} maxLength={2000} onChange={(event) => setDirectiveText(event.target.value)} placeholder={latestPlan.instruction_overlay ?? 'Revise only this plan overlay; immutable skill files stay unchanged.'} disabled={latestPlan.state === 'terminated'} />
                  </div>
                  <div className="native-skills__directive-actions">
                    {latestPlan.state === 'planned' && <button className="button button--ghost" type="button" disabled={busy} onClick={() => { void applyDirective('pause') }}>Pause plan</button>}
                    {latestPlan.state === 'paused' && <button className="button button--ghost" type="button" disabled={busy} onClick={() => { void applyDirective('resume') }}>Resume plan</button>}
                    {latestPlan.state !== 'terminated' && <><button className="button button--ghost" type="button" disabled={busy} onClick={() => { void applyDirective('rewrite-instructions') }}>Revise overlay</button><button className="text-button text-button--danger" type="button" disabled={busy} onClick={() => { void applyDirective('terminate') }}>Terminate plan</button></>}
                  </div>
                </div>
                <div className="native-skills__guardrails">
                  <p className="eyebrow">ENFORCED BOUNDARIES</p>
                  {latestPlan.guardrails.map((guardrail) => <span key={guardrail}>✓ {guardrail}</span>)}
                </div>
              </>
            ) : <p className="panel-hint">Use the form above to create a bounded local plan. The controller has nothing to run, and its only mutable state is the plan record shown here.</p>}
          </section>

          <section className="panel native-skills__provenance">
            <div className="panel-heading">
              <div>
                <p className="eyebrow">CONTROLLED PROVENANCE · METADATA ONLY</p>
                <h2>{library.sources.length} reviewed source records → {library.skills.length} clean-room native skills</h2>
              </div>
              <span className="subtle-badge">NO WHOLESALE COPY</span>
            </div>
            <p>{library.detail}</p>
            <details>
              <summary>Inspect source coverage, licence signals, and native mappings</summary>
              <div className="native-skills__source-grid">
                {library.sources.map((source) => (
                  <article key={source.id}>
                    <span>{source.license_signal}</span>
                    <strong>{source.requested_repository}</strong>
                    <p>{source.decision}</p>
                    <small>{source.review_commit.slice(0, 12)} · {source.native_skill_ids.join(', ')}</small>
                  </article>
                ))}
              </div>
            </details>
          </section>
        </>
      )}
    </section>
  )
}
