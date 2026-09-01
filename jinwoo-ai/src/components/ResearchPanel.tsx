import { useState } from 'react'
import type { FormEvent } from 'react'
import type { ResearchPlan } from '../types/army'

interface ResearchPanelProps {
  plan: ResearchPlan | null
  busy: boolean
  onPlan: (frameworkId: ResearchPlan['frameworkId'], topic: string, targets: string[], confirmPublicSources: boolean) => Promise<boolean>
}

const researchAdapters: Array<{ id: ResearchPlan['frameworkId']; label: string; note: string }> = [
  { id: 'crawl4ai', label: 'Crawl4AI', note: 'Apache-2.0 · public-web collection contract' },
  { id: 'firecrawl-web-agent', label: 'Firecrawl Web-Agent', note: 'MIT · structured public-web research contract' },
  { id: 'firecrawl', label: 'Firecrawl', note: 'AGPL-3.0 · no runtime use before a separate licence decision' },
]

export function ResearchPanel({ plan, busy, onPlan }: ResearchPanelProps) {
  const [frameworkId, setFrameworkId] = useState<ResearchPlan['frameworkId']>('crawl4ai')
  const [topic, setTopic] = useState('')
  const [targets, setTargets] = useState('')
  const [confirmPublicSources, setConfirmPublicSources] = useState(false)
  const [formError, setFormError] = useState('')

  const submit = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault()
    const cleanTopic = topic.trim()
    if (cleanTopic.length < 2) {
      setFormError('Describe the research question or topic first.')
      return
    }
    const targetList = targets.split('\n').map((item) => item.trim()).filter(Boolean)
    if (targetList.length > 10) {
      setFormError('Use at most 10 explicit source URLs in one research plan.')
      return
    }
    if (targetList.length && !confirmPublicSources) {
      setFormError('Confirm that you are authorised to research the listed public sources.')
      return
    }
    setFormError('')
    await onPlan(frameworkId, cleanTopic, targetList, confirmPublicSources)
  }

  const selectedAdapter = researchAdapters.find((adapter) => adapter.id === frameworkId)

  return (
    <div className="research-layout">
      <section className="panel research-planner" aria-labelledby="research-planner-title">
        <div className="panel-heading">
          <div>
            <p className="eyebrow">TANK // NO-FETCH RESEARCH GATE</p>
            <h2 id="research-planner-title">Plan public-web research</h2>
          </div>
          <span className="subtle-badge">NO NETWORK</span>
        </div>
        <p className="research-copy">Validate a bounded research brief before a future retrieval mission. This tool never opens a URL, starts a browser, calls a crawler, resolves DNS or sends your workspace data.</p>
        <form className="research-form" onSubmit={submit}>
          <label htmlFor="research-adapter">Controlled adapter</label>
          <select id="research-adapter" value={frameworkId} onChange={(event) => setFrameworkId(event.target.value as ResearchPlan['frameworkId'])} disabled={busy}>
            {researchAdapters.map((adapter) => <option key={adapter.id} value={adapter.id}>{adapter.label}</option>)}
          </select>
          <small className="research-adapter-note">{selectedAdapter?.note}</small>
          <label htmlFor="research-topic">Research topic</label>
          <textarea id="research-topic" value={topic} onChange={(event) => setTopic(event.target.value)} maxLength={2000} placeholder="Example: Compare local embedding models for a privacy-first desktop app" disabled={busy} />
          <label htmlFor="research-targets">Explicit public HTTPS sources <small>Optional · one URL per line · 10 max</small></label>
          <textarea id="research-targets" value={targets} onChange={(event) => setTargets(event.target.value)} maxLength={20_000} placeholder={'https://example.org/research\nhttps://docs.example.org/guide'} disabled={busy} />
          <label className="research-confirm"><input type="checkbox" checked={confirmPublicSources} onChange={(event) => setConfirmPublicSources(event.target.checked)} disabled={busy} /><span>I am authorised to research these public sources. I understand this only creates a no-fetch plan.</span></label>
          {formError && <p className="form-error" role="alert">{formError}</p>}
          <button className="button" type="submit" disabled={busy}>{busy ? 'Validating…' : 'Create no-fetch plan'}</button>
        </form>
      </section>

      <aside className="side-stack">
        <section className="panel research-boundary">
          <p className="eyebrow">BOUNDARIES IN FORCE</p>
          <h2>Tank remains contained.</h2>
          <ul>
            <li>HTTPS public targets only; no local, private, authenticated or credential-bearing URLs.</li>
            <li>No cookies, browser sessions, logins, uploads, shell commands or crawler runtime.</li>
            <li>Any later retrieval needs a separate visible approval, reviewed licence and strict limits.</li>
          </ul>
        </section>
        {plan && (
          <section className="panel research-result" aria-live="polite">
            <p className="eyebrow">LATEST NO-FETCH PLAN</p>
            <h2>{plan.frameworkId.replaceAll('-', ' ')}</h2>
            <p>{plan.targets.length ? `${plan.targets.length} explicit public target${plan.targets.length === 1 ? '' : 's'} validated.` : 'No targets listed yet; no retrieval can be proposed.'}</p>
            <div className="research-result__flags"><span>{plan.externalFetchStarted ? 'Fetch started' : 'No fetch started'}</span><span>{plan.requiresApprovalForFetch ? 'Future approval required' : 'No future approval'}</span></div>
            {plan.targets.length > 0 && <ul className="research-target-list">{plan.targets.map((target) => <li key={target.url}><b>{target.hostname}</b><small>{target.url}</small></li>)}</ul>}
            <h3>Safeguards</h3>
            <ul>{plan.safeguards.map((safeguard) => <li key={safeguard}>{safeguard}</li>)}</ul>
          </section>
        )}
      </aside>
    </div>
  )
}
