import { useMemo, useState } from 'react'
import type { FormEvent } from 'react'
import type { CoordinationPattern, ShadowArmyOverview, ShadowArmyPlan } from '../types/army'

interface ShadowArmyCoreProps {
  overview: ShadowArmyOverview | null
  plan: ShadowArmyPlan | null
  busy: boolean
  onPlan: (prompt: string, requestedLogicalAgents: number, coordination: CoordinationPattern) => Promise<boolean>
}

const patternLabels: Record<CoordinationPattern, { title: string; detail: string; icon: string }> = {
  hierarchical: {
    title: 'Hierarchical command',
    detail: 'Jinwoo → Bellion → Commander → Division → P · E · V',
    icon: '⌘',
  },
  'commander-council': {
    title: 'Commander council',
    detail: 'A small advisory debate with one Bellion decision route.',
    icon: '◈',
  },
  'dependency-graph': {
    title: 'Dependency graph',
    detail: 'Visible stages and approval edges for complex work.',
    icon: '⌁',
  },
  'bounded-swarm': {
    title: 'Bounded swarm',
    detail: 'Logical specialists, with no hidden worker expansion.',
    icon: '✦',
  },
}

const fallbackOverview: ShadowArmyOverview = {
  commanders: 15,
  divisions: 45,
  logicalAgents: 450,
  workerSlots: 1350,
  activeRuntimeWorkers: 0,
  runtimeCapPerMission: 3,
  allExternalRuntimesDisabled: true,
  hierarchy: [
    'Jinwoo · Shadow Monarch',
    'Bellion · Grand Marshal',
    '15 Commanders',
    '45 Sub-departments',
    '450 Logical Agents',
    'Planner · Executor · Verifier',
  ],
  supportedPatterns: ['hierarchical', 'commander-council', 'dependency-graph', 'bounded-swarm'],
}

const humanize = (value: string) => value.replaceAll('-', ' ')

export function ShadowArmyCore({ overview, plan, busy, onPlan }: ShadowArmyCoreProps) {
  const [prompt, setPrompt] = useState('Design a safe multi-agent code review and verification workflow.')
  const [requestedLogicalAgents, setRequestedLogicalAgents] = useState(6)
  const [coordination, setCoordination] = useState<CoordinationPattern>('hierarchical')
  const [formError, setFormError] = useState('')

  const activeOverview = overview ?? fallbackOverview
  const patterns = useMemo(() => activeOverview.supportedPatterns.length ? activeOverview.supportedPatterns : fallbackOverview.supportedPatterns, [activeOverview.supportedPatterns])

  const submit = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault()
    const cleanPrompt = prompt.trim()
    if (cleanPrompt.length < 2) {
      setFormError('Describe the mission before Jinwoo creates a topology.')
      return
    }
    setFormError('')
    await onPlan(cleanPrompt, requestedLogicalAgents, coordination)
  }

  return (
    <section className="shadow-core" aria-labelledby="shadow-core-title">
      <header className="shadow-core__hero panel">
        <div className="shadow-core__hero-copy">
          <p className="eyebrow"><span className="signal-dot" /> NATIVE MULTI-AGENT CORE · BATCH 07</p>
          <h1 id="shadow-core-title">Shadow Army <em>Core</em></h1>
          <p>
            A local, visible command topology for Jinwoo. It models the full Army without silently spawning
            processes, model sessions, browser agents, or external framework runtimes.
          </p>
          <div className="shadow-core__hero-pills">
            <span>{activeOverview.commanders} commanders</span>
            <span>{activeOverview.divisions} divisions</span>
            <span>{activeOverview.logicalAgents} logical seats</span>
            <span>{activeOverview.runtimeCapPerMission} runtime roles max</span>
          </div>
        </div>
        <div className="shadow-core__lockup" aria-label="Shadow Army safety state">
          <span className="shadow-core__seal">♛</span>
          <strong>{activeOverview.allExternalRuntimesDisabled ? 'EXTERNAL RUNTIMES LOCKED' : 'REVIEW REQUIRED'}</strong>
          <small>Frameworks influence a plan; Jinwoo keeps final control.</small>
        </div>
      </header>

      <div className="shadow-core__metric-grid" aria-label="Shadow Army core capacity">
        <article><span>Logical army</span><b>{activeOverview.logicalAgents}</b><small>catalogue seats, not processes</small></article>
        <article><span>Worker slots</span><b>{activeOverview.workerSlots.toLocaleString()}</b><small>P · E · V per logical seat</small></article>
        <article><span>Active workers</span><b>{activeOverview.activeRuntimeWorkers}</b><small>none begin from planning</small></article>
        <article><span>External engines</span><b>0</b><small>always visible and disabled</small></article>
      </div>

      <div className="shadow-core__content-grid">
        <section className="panel shadow-core__topology">
          <div className="panel-heading">
            <div>
              <p className="eyebrow">COMMAND TOPOLOGY</p>
              <h2>One visible chain of command</h2>
            </div>
            <span className="subtle-badge">NO HIDDEN SPAWN</span>
          </div>
          <ol className="shadow-core__hierarchy">
            {activeOverview.hierarchy.map((level, index) => (
              <li key={level}>
                <span>{String(index + 1).padStart(2, '0')}</span>
                <strong>{level}</strong>
              </li>
            ))}
          </ol>
          <p className="panel-hint">
            Every selected logical agent remains behind a Planner → Executor → Verifier hand-off. A framework
            record does not authorise a tool, a model, a file write, or a background worker.
          </p>
        </section>

        <form className="panel shadow-core__form" onSubmit={submit}>
          <div className="panel-heading">
            <div>
              <p className="eyebrow">BELLION · TOPOLOGY BUILDER</p>
              <h2>Prepare a mission map</h2>
            </div>
            <span className="subtle-badge">PLAN ONLY</span>
          </div>
          <label htmlFor="shadow-core-prompt">Mission</label>
          <textarea
            id="shadow-core-prompt"
            value={prompt}
            maxLength={8000}
            onChange={(event) => setPrompt(event.target.value)}
            placeholder="Describe a safe outcome, such as a code-review, research, or media plan."
          />
          <div className="shadow-core__form-grid">
            <label htmlFor="shadow-core-pattern">
              Coordination pattern
              <select id="shadow-core-pattern" value={coordination} onChange={(event) => setCoordination(event.target.value as CoordinationPattern)}>
                {patterns.map((pattern) => <option key={pattern} value={pattern}>{patternLabels[pattern].title}</option>)}
              </select>
            </label>
            <label htmlFor="shadow-core-count">
              Logical scope
              <input
                id="shadow-core-count"
                type="number"
                min="1"
                max="450"
                value={requestedLogicalAgents}
                onChange={(event) => setRequestedLogicalAgents(Math.max(1, Math.min(450, Number(event.target.value) || 1)))}
              />
            </label>
          </div>
          <p className="shadow-core__pattern-detail"><span>{patternLabels[coordination].icon}</span>{patternLabels[coordination].detail}</p>
          {formError && <p className="form-error" role="alert">{formError}</p>}
          <button className="button" type="submit" disabled={busy}>{busy ? 'Mapping Army…' : 'Prepare safe topology'} <span>↗</span></button>
          <p className="panel-hint">The request is policy-screened. This step creates no task runner and makes no model, network, or tool call.</p>
        </form>
      </div>

      {plan ? (
        <section className="shadow-core__plan panel" aria-live="polite">
          <div className="shadow-core__plan-head">
            <div>
              <p className="eyebrow">LATEST TOPOLOGY · {plan.id.slice(-6).toUpperCase()}</p>
              <h2>{plan.commander} / {plan.division}</h2>
              <p>“{plan.prompt}”</p>
            </div>
            <div className="shadow-core__plan-badges">
              <span className={`risk-badge risk-badge--${plan.risk}`}>{plan.risk} risk</span>
              <span className="subtle-badge">{humanize(plan.coordination)}</span>
            </div>
          </div>

          <div className="shadow-core__plan-stats">
            <span><b>{plan.logicalAgentsReserved}</b> logical seats reserved</span>
            <span><b>{plan.displayedLogicalAgents}</b> representative seats shown</span>
            <span><b>{plan.runtimeWorkerCap}</b> workers maximum</span>
            <span><b>{plan.runtimeWorkersStarted}</b> workers started</span>
          </div>

          <div className="shadow-core__plan-columns">
            <div>
              <p className="eyebrow">MISSION GRAPH</p>
              <ol className="shadow-core__stages">
                {plan.stages.map((stage, index) => (
                  <li key={stage.id}>
                    <span>{index + 1}</span>
                    <div><strong>{stage.label}</strong><p>{stage.detail}</p></div>
                    {stage.requiresApproval && <em>approval edge</em>}
                  </li>
                ))}
              </ol>
            </div>
            <div>
              <p className="eyebrow">LOGICAL SPECIALISTS</p>
              <div className="shadow-core__agents">
                {plan.agents.map((agent) => (
                  <article key={agent.id}>
                    <span>logical · offline</span>
                    <strong>{agent.name}</strong>
                    <p>{agent.specialty}</p>
                  </article>
                ))}
              </div>
            </div>
          </div>

          <div className="shadow-core__frameworks">
            <div>
              <p className="eyebrow">FRAMEWORK PATTERN REFERENCES</p>
              <h3>{plan.patternSummary}</h3>
            </div>
            <div>
              {plan.frameworks.map((framework) => (
                <article key={framework.id}>
                  <span className={framework.executionEnabled ? 'framework-state framework-state--canonical' : 'framework-state framework-state--not-installed'}>{framework.executionEnabled ? 'native' : 'disabled'}</span>
                  <strong>{framework.label}</strong>
                  <p>{framework.patternRole}</p>
                  <small>{humanize(framework.implementationStatus)} · no external execution</small>
                </article>
              ))}
            </div>
          </div>

          <div className="shadow-core__guardrails">
            <p className="eyebrow">GUARDRAILS</p>
            <ul>{plan.guardrails.map((guardrail) => <li key={guardrail}>{guardrail}</li>)}</ul>
          </div>
        </section>
      ) : (
        <section className="panel shadow-core__empty-plan">
          <span>✦</span>
          <div><p className="eyebrow">READY FOR A MISSION</p><h2>Create a topology before any agent work exists.</h2><p>Bellion will return a commander, division, logical scope, framework references, visible stages and safety boundaries.</p></div>
        </section>
      )}

      <section className="shadow-core__archive-note panel">
        <div><p className="eyebrow">PROJECT.ZIP INTAKE</p><h2>Safe concepts are integrated; unreviewed controls stay quarantined.</h2></div>
        <p>
          The uploaded archive informed the registry, status, queue and orchestrator design. Its bundled secrets,
          external wrappers, auto-execution, computer-control, network, security-offense and hardware paths are not
          loaded into Jinwoo.
        </p>
      </section>
    </section>
  )
}
