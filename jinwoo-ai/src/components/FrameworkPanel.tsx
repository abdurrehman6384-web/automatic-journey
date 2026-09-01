import { useState } from 'react'
import type { FormEvent } from 'react'
import type { FrameworkDryRun, FrameworkStatus } from '../types/army'

interface FrameworkPanelProps {
  frameworks: FrameworkStatus[]
  dryRun: FrameworkDryRun | null
  busy: boolean
  onDryRun: (frameworkId: string, prompt: string, requestedAgents: number) => Promise<boolean>
}

const runtimeIcon = (runtime: FrameworkStatus['runtime']) => {
  if (runtime === 'builtin') return '♛'
  if (runtime === 'container-sidecar') return '▣'
  if (runtime === 'go-cli') return '⌁'
  if (runtime === 'typescript-mcp' || runtime === 'typescript-service') return '⌘'
  return '◈'
}

export function FrameworkPanel({ frameworks, dryRun, busy, onDryRun }: FrameworkPanelProps) {
  const [selectedId, setSelectedId] = useState<string | null>(null)
  const [prompt, setPrompt] = useState('Prepare a safe, read-only integration plan for this project.')
  const [requestedAgents, setRequestedAgents] = useState(3)
  const [formError, setFormError] = useState('')
  const selected = frameworks.find((framework) => framework.id === selectedId)

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
          <p className="eyebrow">ORCHESTRATION ADAPTERS</p>
          <h2 id="frameworks-title">Framework boundaries</h2>
        </div>
        <span className="subtle-badge">CONTROLLED</span>
      </div>
      <div className="framework-list">
        {frameworks.map((framework) => (
          <div className="framework-row" key={framework.id}>
            <span className={`framework-mark framework-mark--${framework.runtime}`}>{runtimeIcon(framework.runtime)}</span>
            <div>
              <strong>{framework.label}</strong>
              <p>{framework.detail}</p>
              <small className="framework-meta">{framework.integrationBatch ? `Batch ${framework.integrationBatch}` : 'Core'} · {framework.ownerCommander} · {framework.implementationStatus.replaceAll('-', ' ')} · {framework.license}{framework.sourceUrl ? <> · <a href={framework.sourceUrl} target="_blank" rel="noreferrer">Source</a></> : null}</small>
              {framework.id === 'jinwoo-native-control-audit'
                ? <small className="framework-review-button">Use the local control review below.</small>
                : framework.integrationBatch > 0 && framework.implementationStatus !== 'queued' && <button className="framework-review-button" type="button" onClick={() => setSelectedId(framework.id)} disabled={busy}>Dry-run plan</button>}
            </div>
            <span className={`framework-state framework-state--${framework.state}`}>
              {framework.executionEnabled ? 'active' : framework.state.replace('-', ' ')}
            </span>
          </div>
        ))}
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
