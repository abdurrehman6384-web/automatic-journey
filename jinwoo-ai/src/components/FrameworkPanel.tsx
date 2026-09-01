import { useMemo, useState } from 'react'
import type { FormEvent } from 'react'
import type { FrameworkDryRun, FrameworkStatus } from '../types/army'

interface FrameworkPanelProps {
  frameworks: FrameworkStatus[]
  dryRun: FrameworkDryRun | null
  busy: boolean
  onDryRun: (frameworkId: string, prompt: string, requestedAgents: number) => Promise<boolean>
}

type StatusFilter = 'all' | 'ready' | 'review' | 'reference' | 'queued'

const runtimeIcon = (runtime: FrameworkStatus['runtime']) => {
  if (runtime === 'builtin') return '♛'
  if (runtime === 'container-sidecar') return '▣'
  if (runtime === 'desktop-client') return '▤'
  if (runtime === 'mobile-client') return '▯'
  if (runtime === 'skill-catalog') return '✦'
  if (runtime === 'go-cli' || runtime === 'go-service' || runtime === 'rust-cli') return '⌁'
  if (runtime === 'typescript-mcp' || runtime === 'typescript-service') return '⌘'
  return '◈'
}

const statusMatches = (framework: FrameworkStatus, filter: StatusFilter) => {
  if (filter === 'all') return true
  if (filter === 'ready') return framework.implementationStatus === 'active' || framework.implementationStatus === 'contract-ready'
  if (filter === 'review') return framework.implementationStatus === 'license-review-required' || framework.implementationStatus === 'source-review-required' || framework.implementationStatus === 'archived-upstream'
  if (filter === 'reference') return framework.implementationStatus === 'reference-only'
  return framework.implementationStatus === 'queued'
}

const stateLabelFor = (framework: FrameworkStatus) => {
  if (framework.executionEnabled) return 'active native'
  if (framework.implementationStatus === 'license-review-required') return 'licence review'
  if (framework.implementationStatus === 'source-review-required') return 'source intake'
  if (framework.implementationStatus === 'reference-only') return 'reference only'
  if (framework.implementationStatus === 'archived-upstream') return 'archived upstream'
  if (framework.implementationStatus === 'queued') return 'queued'
  return framework.state.replaceAll('-', ' ')
}

export function FrameworkPanel({ frameworks, dryRun, busy, onDryRun }: FrameworkPanelProps) {
  const [selectedId, setSelectedId] = useState<string | null>(null)
  const [prompt, setPrompt] = useState('Prepare a safe, read-only integration plan for this project.')
  const [requestedAgents, setRequestedAgents] = useState(3)
  const [formError, setFormError] = useState('')
  const [query, setQuery] = useState('')
  const [category, setCategory] = useState<'all' | FrameworkStatus['category']>('all')
  const [statusFilter, setStatusFilter] = useState<StatusFilter>('all')
  const selected = frameworks.find((framework) => framework.id === selectedId)
  const categories = useMemo(() => [...new Set(frameworks.map((framework) => framework.category))].sort(), [frameworks])
  const filteredFrameworks = useMemo(() => {
    const needle = query.trim().toLocaleLowerCase()
    return frameworks.filter((framework) => {
      const searchable = [framework.label, framework.ownerCommander, framework.category, framework.runtime, framework.license, framework.implementationStatus, ...(framework.capabilities ?? [])].join(' ').toLocaleLowerCase()
      return (!needle || searchable.includes(needle)) && (category === 'all' || framework.category === category) && statusMatches(framework, statusFilter)
    })
  }, [category, frameworks, query, statusFilter])

  const submitDryRun = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault()
    if (!selected) return
    if (!prompt.trim()) {
      setFormError('Describe the safe plan you want this adapter to review.')
      return
    }
    setFormError('')
    if (await onDryRun(selected.id, prompt.trim(), requestedAgents)) setSelectedId(null)
  }

  return (
    <section className="panel framework-panel" aria-labelledby="frameworks-title">
      <div className="panel-heading">
        <div>
          <p className="eyebrow">ADAPTERS &amp; ADVANCED SKILLS</p>
          <h2 id="frameworks-title">Framework boundaries</h2>
        </div>
        <span className="subtle-badge">{filteredFrameworks.length}/{frameworks.length} VISIBLE</span>
      </div>
      <p className="framework-intro">Search capability contracts by lane, owner or status. A visible record is never an installation or a tool permission.</p>
      <div className="framework-filters" aria-label="Filter framework registry">
        <label className="framework-search">
          <span>Search registry</span>
          <input value={query} onChange={(event) => setQuery(event.target.value)} placeholder="Media, MCP, gesture, security…" type="search" />
        </label>
        <label>
          <span>Category</span>
          <select value={category} onChange={(event) => setCategory(event.target.value as 'all' | FrameworkStatus['category'])}>
            <option value="all">All categories</option>
            {categories.map((item) => <option key={item} value={item}>{item.replaceAll('-', ' ')}</option>)}
          </select>
        </label>
        <label>
          <span>Status</span>
          <select value={statusFilter} onChange={(event) => setStatusFilter(event.target.value as StatusFilter)}>
            <option value="all">All states</option>
            <option value="ready">Active / contract ready</option>
            <option value="review">Review required</option>
            <option value="reference">Reference only</option>
            <option value="queued">Queued</option>
          </select>
        </label>
      </div>
      <div className="framework-list">
        {filteredFrameworks.map((framework) => {
          const referenceOnly = framework.implementationStatus === 'reference-only'
          const reviewLabel = referenceOnly ? 'Review boundary' : 'Dry-run plan'
          const stateLabel = stateLabelFor(framework)
          return (
            <div className="framework-row" key={framework.id}>
              <span className={`framework-mark framework-mark--${framework.runtime}`}>{runtimeIcon(framework.runtime)}</span>
              <div>
                <strong>{framework.label}</strong>
                <p>{framework.detail}</p>
                {framework.capabilities?.length ? <div className="framework-capabilities" aria-label={`${framework.label} capabilities`}>{framework.capabilities.map((capability) => <span key={capability}>{capability}</span>)}</div> : null}
                <small className="framework-meta">{framework.integrationBatch ? `Batch ${framework.integrationBatch}` : 'Core'} · {framework.ownerCommander} · {framework.implementationStatus.replaceAll('-', ' ')}{framework.capabilities?.length && framework.activationBoundary ? <> · {framework.activationBoundary.replaceAll('-', ' ')}</> : null} · {framework.license}{framework.sourceUrl ? <> · <a href={framework.sourceUrl} target="_blank" rel="noreferrer">Source</a></> : null}</small>
                {framework.id === 'jinwoo-native-control-audit'
                  ? <small className="framework-review-button">Use the local control review from the Control &amp; Audit view.</small>
                  : framework.integrationBatch > 0 && !['queued', 'source-review-required'].includes(framework.implementationStatus) && <button className="framework-review-button" type="button" onClick={() => setSelectedId(framework.id)} disabled={busy}>{reviewLabel}</button>}
              </div>
              <span className={`framework-state framework-state--${framework.state} framework-state--${framework.implementationStatus}`}>
                {stateLabel}
              </span>
            </div>
          )
        })}
        {!filteredFrameworks.length && <p className="framework-empty">No controlled lane matches these filters. Clear a filter to see the full registry.</p>}
      </div>
      {selected && (
        <form className="framework-dry-run" onSubmit={submitDryRun}>
          <div className="framework-dry-run__heading"><b>{selected.label} safe dry run</b><button type="button" onClick={() => setSelectedId(null)} disabled={busy}>Cancel</button></div>
          <label htmlFor="framework-plan">Requested plan</label>
          <textarea id="framework-plan" value={prompt} maxLength={8000} onChange={(event) => setPrompt(event.target.value)} />
          <label htmlFor="framework-agent-count">Logical agents requested <small>Runtime stays capped at 3 workers</small></label>
          <input id="framework-agent-count" type="number" min="1" max="450" value={requestedAgents} onChange={(event) => setRequestedAgents(Math.max(1, Math.min(450, Number(event.target.value) || 1)))} />
          {formError && <p className="form-error" role="alert">{formError}</p>}
          <button className="button" type="submit" disabled={busy}>{busy ? 'Reviewing…' : 'Prepare bounded plan'}</button>
        </form>
      )}
      {dryRun && (
        <div className={`framework-result framework-result--${dryRun.policyOutcome}`}>
          <p className="eyebrow">LATEST SAFE DRY RUN · {dryRun.frameworkLabel}</p>
          <strong>{dryRun.summary}</strong>
          <div><span>{dryRun.requestedAgents} logical requested</span><span>{dryRun.boundedRuntimeWorkers} runtime workers max</span><span>{dryRun.externalRuntimeInvoked ? 'External runtime invoked' : 'No upstream runtime invoked'}</span></div>
          <ol>{dryRun.nextSteps.map((step) => <li key={step}>{step}</li>)}</ol>
        </div>
      )}
      <p className="panel-hint">A dry run is a policy-screened plan only. Optional frameworks cannot run missions or bypass Jinwoo’s approval, privacy, workspace and audit controls.</p>
    </section>
  )
}
